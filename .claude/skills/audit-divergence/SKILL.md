# Audit BOB vs USD Divergence

All python commands MUST use `.venv/bin/python` (not `python` or `python3`).

**This skill never writes to YNAB.** It only issues GET requests. If it finds a broken
transaction, report it and stop — let the user decide what to do.

Use this when `/reconcile` or `/sync-bob` reports a difference between BOB Budget and
the ⚙️ BOB Budget account in USD Budget and you need to know whether it is a real
failure or just exchange rate drift.

## Why the reconcile number alone proves nothing

The reconcile report computes `bob_total / spot_rate - usd_balance`. That is not an
identity. The USD account is a **historical-cost ledger**: each synced transaction was
converted at the rate in force on its own date and is never revalued. The left side
reprices the entire standing balance at today's rate. So whenever the BOB balance is
non-zero and the rate moves, the two drift apart with nothing wrong.

Between June and August 2026 the rate went 9.7 → 11.42 and produced tens of dollars of
drift in both directions. Never conclude anything from the headline number.

## Phase 1 — Export both ledgers

```bash
.venv/bin/python .claude/skills/audit-divergence/export_ledgers.py
```

Writes `.audit/ledgers.json`. Set `AUDIT_DIR` to put it elsewhere.

The script prints, per account, the ledger sum next to YNAB's reported balance. **If any
line is flagged `INCOMPLETE DUMP`, stop.** Everything downstream is derived from these
transactions, so a mismatch means the analysis would be built on partial data.

(The YNAB `/transactions` endpoint silently trims to roughly the last year unless an
explicit `since_date` is passed. The script passes `1990-01-01`. Do not remove it.)

## Phase 2 — Attribute the divergence day by day

```bash
.venv/bin/python .claude/skills/audit-divergence/attribute.py --from YYYY-MM-DD
```

Defaults to 90 days back. Options: `--to`, `--threshold` (flow gap worth flagging, USD),
`--drill YYYY-MM-DD ...` to print a day's BOB and USD entries side by side.

It walks `bob_balance(D) / rate_in_force_on_D - usd_balance(D)` and splits each day's
move into two terms:

| Term | Meaning |
|------|---------|
| `reprice` | the standing balance repriced by a rate change. **Arithmetic, never a bug.** |
| `flow gap` | that day's BOB flow converted at that day's rate, minus the USD flow. **Zero on a healthy day.** |

Read the `flow gap` column only. Every day it moves is a day something failed to cross.

## Phase 3 — Report

Give the user:

1. The **attribution totals**: opening divergence, repricing, real flow gaps, closing
   divergence. State plainly whether the rate explains the difference or not.
2. The **flagged days** with what happened on each.
3. The **BOB transactions with no USD counterpart**. This list is rate-independent, so
   it is the actual verdict. For each, the script prints the amount at its own day's
   rate and whether it came from a bank pipeline (`import_id` present) or was typed by
   hand (`manual entry`).

Flow gaps that are **not** missing transactions, and what they usually mean:

- **Conversion basis.** A Binance trade carries its own `[TC:]` that differs slightly
  from the day's prevailing rate. On a 20,000 Bs trade a 0.06 spread is several USD.
  Harmless.
- **`Reconciliation Balance Adjustment`.** YNAB plugs the USD side during a
  reconciliation and there is no BOB twin. Real, but it is the user's own adjustment.

## The failure mode this keeps catching

`/sync-bob` derives `--since-date` from the last **reconciled** transaction on the USD
side. That assumes BOB is append-only in time. It is not:

- Baneco stamps the **operation** date, not the posting date, so `TRASP.CTAS.TERCEROS`
  transfers arrive days late carrying an older date.
- Manual wallet entries are back-dated by definition.

Anything that lands at or below the reconciled floor after the window has moved past it
is invisible to every future sync, forever, with no error. When the missing-counterpart
list shows a transaction dated at or before the last reconciled date, this is why.
