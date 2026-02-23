import json
import os
import shutil
import sys

from playwright.sync_api import sync_playwright

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT_DIR = os.path.dirname(MODULE_DIR)
BROWSER_DATA_DIR = os.path.join(SCRIPT_DIR, ".binance_browser_data")
EXPORT_PATH = os.path.join(MODULE_DIR, "export.json")
BALANCE_PATH = os.path.join(MODULE_DIR, "balance.json")

LOGIN_URL = "https://www.binance.com/en/my/dashboard"
P2P_ORDER_URL = "https://www.binance.com/en/my/orders/p2p"
P2P_API_PATTERN = "/bapi/c2c/v2/private/c2c/order-match/order-list"


class BinanceExporter:
    def export(self, since_date: str = None) -> str:
        """Open Binance P2P history, intercept API response, save JSON.

        Returns path to saved JSON file.
        """
        all_orders = []

        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                BROWSER_DATA_DIR,
                headless=False,
            )
            page = context.pages[0] if context.pages else context.new_page()

            # Step 1: Ensure logged in via dashboard (no P2P nav yet)
            if not self._ensure_logged_in(page):
                context.close()
                sys.exit(1)

            # Step 1b: Capture USDT balance from dashboard
            self._capture_usdt_balance(page)

            print("Logged in. Capturing P2P order history...", flush=True)

            # Step 2: Set up API interception BEFORE navigating to P2P
            captured_response = []

            def handle_response(response):
                if P2P_API_PATTERN in response.url:
                    try:
                        body = response.json()
                        if body.get("data"):
                            captured_response.append(body["data"])
                    except Exception:
                        pass

            page.on("response", handle_response)

            # Step 3: Now navigate to P2P page — listener catches the API call
            all_orders = self._capture_orders(page, since_date, captured_response)

            page.remove_listener("response", handle_response)
            context.close()

        print(f"Captured {len(all_orders)} orders.", flush=True)

        with open(EXPORT_PATH, "w") as f:
            json.dump({"data": all_orders}, f, indent=2)

        print(f"Saved: {EXPORT_PATH}", flush=True)
        return EXPORT_PATH

    def reset(self):
        """Clear persistent browser state to force fresh login."""
        if os.path.exists(BROWSER_DATA_DIR):
            shutil.rmtree(BROWSER_DATA_DIR)
            print("Browser state cleared.", flush=True)

    def _ensure_logged_in(self, page) -> bool:
        """Navigate to dashboard to check session. Wait for manual login if needed."""
        page.goto(LOGIN_URL)
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(5000)

        for attempt in range(120):  # Wait up to 2 minutes
            if "/my/dashboard" in page.url:
                return True
            if attempt == 0:
                print("Not logged in. Please log in manually in the browser...", flush=True)
            page.wait_for_timeout(1000)

        print("Login timed out.", flush=True)
        return False

    def _capture_orders(self, page, since_date: str, captured_response: list) -> list:
        """Navigate to P2P page (listener already attached) and collect all orders."""
        all_orders = []

        page.goto(P2P_ORDER_URL)
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(5000)

        # Collect first page
        for data in captured_response:
            all_orders.extend(data)
        captured_response.clear()

        # Paginate: click "Next" until no more pages or we've gone past since_date
        while True:
            next_btn = page.locator('button[aria-label="Next"]')
            if next_btn.count() == 0 or not next_btn.is_enabled():
                break

            # Check if oldest order on current page is before since_date
            if since_date and all_orders:
                oldest = self._oldest_date(all_orders)
                if oldest and oldest < since_date:
                    break

            next_btn.click()
            page.wait_for_timeout(3000)

            for data in captured_response:
                all_orders.extend(data)
            captured_response.clear()

        # Filter by since_date if provided
        if since_date:
            all_orders = [
                o for o in all_orders
                if self._order_date(o) >= since_date
            ]

        # Deduplicate by orderNumber
        seen = set()
        unique = []
        for order in all_orders:
            order_num = order.get("orderNumber")
            if order_num not in seen:
                seen.add(order_num)
                unique.append(order)

        return unique

    @staticmethod
    def _order_date(order: dict) -> str:
        """Extract ISO date from order's createTime timestamp."""
        from datetime import datetime
        ts = order.get("createTime", 0)
        return datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d")

    def _capture_usdt_balance(self, page):
        """Capture USDT funding balance from the wallet overview page.

        Tries API interception first (broad pattern), then falls back to DOM scraping.
        """
        captured_balance = []

        def handle_asset_response(response):
            if "/asset-service/wallet/asset" not in response.url:
                return
            try:
                body = response.json()
                data = body.get("data")
                if not isinstance(data, list):
                    return
                for item in data:
                    if isinstance(item, dict) and item.get("asset") == "USDT":
                        val = item.get("amount")
                        if val:
                            captured_balance.append(float(val))
                            return
            except Exception:
                pass

        page.on("response", handle_asset_response)

        # Navigate to wallet overview to trigger asset API call
        page.goto("https://www.binance.com/en/my/wallet/account/overview")
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(8000)

        page.remove_listener("response", handle_asset_response)

        if captured_balance:
            balance = captured_balance[0]
            with open(BALANCE_PATH, "w") as f:
                json.dump({"usdt_balance": balance}, f)
            print(f"USDT balance: {balance}", flush=True)
        else:
            print("Could not capture USDT balance.", flush=True)

    @staticmethod
    def _oldest_date(orders: list) -> str | None:
        """Find the oldest date among orders."""
        if not orders:
            return None
        from datetime import datetime
        timestamps = [o.get("createTime", 0) for o in orders]
        oldest_ts = min(timestamps)
        return datetime.fromtimestamp(oldest_ts / 1000).strftime("%Y-%m-%d")
