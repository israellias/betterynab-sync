"""Find the day the BOB and USD ledgers stopped agreeing, and say why. Read-only.

Comparing `bob_total / spot_rate` against the USD account balance is not an identity.
The USD account is a historical-cost ledger: every synced transaction was converted at
the rate in force on its own date, while the left side reprices the whole standing
balance at today's rate. A non-zero difference is therefore expected and means nothing
on its own.

So this walks `bob_balance(D) / rate_in_force_on_D - usd_balance(D)` and splits each
day's move into two terms:

    reprice  = balance(D-1) * (1/rate(D) - 1/rate(D-1))   the standing balance repriced
    flow gap = bob_flow(D) / rate(D) - usd_flow(D)        what actually failed that day

`reprice` is arithmetic and is never a bug. `flow gap` sits at zero on a healthy day,
so any day it moves is a transaction that did not make it across.

Usage: attribute.py [--from YYYY-MM-DD] [--to YYYY-MM-DD] [--drill YYYY-MM-DD ...]
"""
import argparse
import json
import os
import re
from datetime import date, timedelta

BISA_CC = "2096c0e6-e608-4373-8346-4414ee53664c"
DATA = os.environ.get("AUDIT_DIR", ".audit")

parser = argparse.ArgumentParser()
parser.add_argument("--from", dest="start", default=None, help="defaults to 90 days back")
parser.add_argument("--to", dest="end", default=None, help="defaults to the last dated activity")
parser.add_argument("--drill", nargs="*", default=[], help="print these days side by side")
parser.add_argument("--threshold", type=float, default=1.0, help="flow gap worth reporting, USD")
args = parser.parse_args()

with open(f"{DATA}/ledgers.json") as f:
    data = json.load(f)

accounts = {a["id"]: a["name"] for a in data["bob_accounts"]}
open_accounts = {
    a["id"]: a["name"] for a in data["bob_accounts"] if not a["closed"] and not a["deleted"]
}
parents = [
    t for t in data["bob_transactions"] if not t["deleted"] and t["account_id"] in open_accounts
]
usd = [t for t in data["usd_bob_account_transactions"] if not t["deleted"]]

end = args.end or max(max(t["date"] for t in parents), max(t["date"] for t in usd))
start = args.start or (date.fromisoformat(end) - timedelta(days=90)).isoformat()


def identifier(txn_id, day):
    return "{}|{}".format(txn_id[:8], "".join(day.split("-")[1:]))


# --- flatten BOB to the leaves the sync actually walks ------------------------
leaves = []
for txn in parents:
    for child in txn["subtransactions"] or [txn]:
        if child.get("deleted"):
            continue
        category = child.get("category_name") or ""
        payee = child.get("payee_name") or txn.get("payee_name") or ""
        leaves.append(
            {
                "date": txn["date"],
                "amount": child["amount"] / 1000.0,
                "account": open_accounts[txn["account_id"]],
                "category": category,
                "payee": payee,
                "memo": (child.get("memo") or "") or (txn.get("memo") or ""),
                "import_id": txn.get("import_id"),
                # the sync skips these on purpose, they are mirrored as USD transfers
                "excluded": "⚙️" in category
                or "🔗" in category
                or payee.startswith("Transfer :"),
                "identifier": identifier(child["id"], txn["date"]),
            }
        )

synced_identifiers = {
    m.group(0)
    for t in usd
    if (m := re.search(r"[0-9a-f]{8}\|\d{4}$", (t.get("memo") or "").strip()))
}
missing = [
    l for l in leaves if not l["excluded"] and l["identifier"] not in synced_identifiers
]

# --- rate series --------------------------------------------------------------
rates = sorted(
    {
        (t["date"], float(m.group(1)))
        for t in usd
        if (m := re.search(r"\[TC:(\d+(?:\.\d+)?)\]", t.get("memo") or ""))
    }
)


def rate_at(day):
    seen = [r for d, r in rates if d <= day]
    return seen[-1] if seen else None


def balances(day):
    bob = sum(t["amount"] / 1000.0 for t in parents if t["date"] <= day)
    usd_balance = sum(t["amount"] / 1000.0 for t in usd if t["date"] <= day)
    return bob, usd_balance


# --- baselines ----------------------------------------------------------------
usd_reconciled = [t["date"] for t in usd if t["cleared"] == "reconciled"]
cc_reconciled = [
    t["date"]
    for t in parents
    if t["account_id"] == BISA_CC and t["cleared"] == "reconciled"
]
print("=" * 88)
print("BASELINES")
print(f"  regular     (USD/BOB account last reconciled) : {max(usd_reconciled, default='-')}")
print(f"  credit card (BOB Budget BISA CC reconciled)   : {max(cc_reconciled, default='-')}")
bob_now, usd_now = balances(end)
spot = rate_at(end)
print(f"  rate in force on {end}                : {spot}")
print(f"  BOB {bob_now:,.2f} Bs -> {bob_now / spot:,.2f} USD | USD account {usd_now:,.2f}")
print(f"  DIVERGENCE {bob_now / spot - usd_now:,.2f} USD")
print("=" * 88)

# --- daily walk ---------------------------------------------------------------
print(f"\n--- daily attribution, {start} to {end} ---")
print(f"{'date':<12}{'rate':>7}{'divergence':>12}{'step':>9}{'reprice':>10}{'flow gap':>10}")
previous_day = (date.fromisoformat(start) - timedelta(days=1)).isoformat()
prev_bob, prev_usd = balances(previous_day)
prev_rate = rate_at(previous_day)
opening = prev_bob / prev_rate - prev_usd
previous = opening
reprice_total = flow_total = 0.0
breaks = []

day = date.fromisoformat(start)
while day <= date.fromisoformat(end):
    today = day.isoformat()
    bob, usd_balance = balances(today)
    rate = rate_at(today)
    divergence = bob / rate - usd_balance
    reprice = prev_bob * (1 / rate - 1 / prev_rate)
    flow_gap = (bob - prev_bob) / rate - (usd_balance - prev_usd)
    reprice_total += reprice
    flow_total += flow_gap
    if abs(flow_gap) > args.threshold:
        breaks.append((today, flow_gap, bob - prev_bob, usd_balance - prev_usd, rate))
    mark = "  <<<" if abs(flow_gap) > args.threshold else ""
    print(
        f"{today:<12}{rate:>7.2f}{divergence:>12,.2f}"
        f"{divergence - previous:>9,.2f}{reprice:>10,.2f}{flow_gap:>10,.2f}{mark}"
    )
    prev_bob, prev_usd, prev_rate, previous = bob, usd_balance, rate, divergence
    day += timedelta(days=1)

print(f"\n--- attribution ---")
print(f"  divergence at {start}          : {opening:>9,.2f} USD")
print(f"  + repricing of the standing balance : {reprice_total:>9,.2f} USD  (arithmetic, not a bug)")
print(f"  + real flow gaps                    : {flow_total:>9,.2f} USD")
print(f"  = divergence at {end}          : {previous:>9,.2f} USD")

if breaks:
    print(f"\n  days where the flow gap exceeds {args.threshold} USD:")
    for today, gap, bob_flow, usd_flow, rate in sorted(breaks, key=lambda b: b[1]):
        print(f"    {today} | gap {gap:>8,.2f} USD | BOB {bob_flow:>11,.2f} Bs -> USD {usd_flow:>9,.2f} @ {rate}")

# --- the rate-independent verdict ---------------------------------------------
print(f"\n--- BOB transactions with no USD counterpart, {start} onward ---")
window = sorted((l for l in missing if l["date"] >= start), key=lambda l: l["date"])
if not window:
    print("  none, every BOB transaction reached USD Budget")
for leaf in window:
    rate = rate_at(leaf["date"])
    origin = "manual entry" if not leaf["import_id"] else leaf["import_id"]
    print(
        f"  {leaf['date']} | {leaf['amount']:>10,.2f} Bs | {leaf['amount']/rate:>8,.2f} USD @ {rate} | "
        f"{leaf['account']:<11} | {leaf['category'][:22]:<22} | {leaf['payee'][:18]:<18} | {origin}"
    )
    print(f"    memo: {leaf['memo'][:88]}")
if window:
    total_bs = sum(l["amount"] for l in window)
    at_own_rate = sum(l["amount"] / rate_at(l["date"]) for l in window)
    print(f"\n  {len(window)} transactions | {total_bs:,.2f} Bs | {at_own_rate:,.2f} USD at their own rates")
    print(f"  divergence if these were synced: {bob_now / spot - (usd_now + at_own_rate):,.2f} USD")

# --- optional day-by-day drill ------------------------------------------------
for target in args.drill:
    print("\n" + "=" * 88)
    print(f"DAY {target}")
    print("  BOB side:")
    for txn in parents:
        if txn["date"] != target:
            continue
        print(
            f"    {txn['amount']/1000.0:>11,.2f} Bs | {accounts.get(txn['account_id'], '?')[:11]:<11} | "
            f"{(txn.get('category_name') or '-')[:22]:<22} | {(txn.get('payee_name') or '-')[:24]:<24} | "
            f"{(txn.get('memo') or '')[:40]}"
        )
        for child in txn["subtransactions"]:
            print(
                f"      {child['amount']/1000.0:>9,.2f} Bs |   split    | "
                f"{(child.get('category_name') or '-')[:22]:<22} | {(child.get('payee_name') or '-')[:24]:<24} | "
                f"{(child.get('memo') or '')[:40]}"
            )
    print("  USD side:")
    for txn in usd:
        if txn["date"] != target:
            continue
        tc = re.search(r"\[TC:(\d+(?:\.\d+)?)\]", txn.get("memo") or "")
        print(
            f"    {txn['amount']/1000.0:>10,.2f} USD | TC {tc.group(1) if tc else '-':<6} | "
            f"{(txn.get('category_name') or '-')[:22]:<22} | {(txn.get('payee_name') or '-')[:24]:<24} | "
            f"{(txn.get('memo') or '')[:40]}"
        )
