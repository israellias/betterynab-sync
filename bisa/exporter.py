import os
import shutil
import sys
from datetime import date

from playwright.sync_api import sync_playwright

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT_DIR = os.path.dirname(MODULE_DIR)
BROWSER_DATA_DIR = os.path.join(SCRIPT_DIR, ".bisa_browser_data")
EXPORT_PATH = os.path.join(MODULE_DIR, "export.csv")

LOGIN_URL = "https://ebisaplus.bisa.com/BISA.UI/#/administrationGeneral/login"
HOME_PATH = "/administrationGeneral/home"
MY_PRODUCTS_PATH = "/administrationGeneral/myProducts"


class BisaExporter:
    def __init__(self, account_number: str, username: str, password: str):
        self._account_number = account_number
        self._username = username
        self._password = password

    def export(self, since_date: str = None) -> str:
        """Open BISA web banking, navigate to account, download CSV.

        Returns path to saved CSV file.
        """
        end_date = date.today().strftime("%d/%m/%Y")
        if since_date:
            # Convert yyyy-mm-dd to dd/mm/yyyy
            parts = since_date.split("-")
            start_date = f"{parts[2]}/{parts[1]}/{parts[0]}"
        else:
            start_date = end_date

        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                BROWSER_DATA_DIR,
                headless=False,
                accept_downloads=True,
            )
            page = context.pages[0] if context.pages else context.new_page()

            # Step 1: Ensure logged in
            if not self._ensure_logged_in(page):
                context.close()
                sys.exit(1)

            print("Logged in to BISA.", flush=True)

            # Step 2: Navigate to My Products
            self._navigate_to_products(page)

            # Step 3: Click on the account
            self._select_account(page)

            # Step 4: Set date filter
            self._set_date_filter(page, start_date, end_date)

            # Step 5: Download CSV
            self._download_csv(page)

            context.close()

        print(f"Saved: {EXPORT_PATH}", flush=True)
        return EXPORT_PATH

    def reset(self):
        """Clear persistent browser state to force fresh login."""
        if os.path.exists(BROWSER_DATA_DIR):
            shutil.rmtree(BROWSER_DATA_DIR)
            print("Browser state cleared.", flush=True)

    def _ensure_logged_in(self, page) -> bool:
        """Try to reach home via session. Only login if session expired."""
        HOME_URL = "https://ebisaplus.bisa.com/BISA.UI/#" + HOME_PATH
        page.goto(HOME_URL)
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(3000)

        # Session alive — already at home
        if HOME_PATH in page.url:
            return True

        # Redirected to login — need to authenticate
        print("Session expired, logging in...", flush=True)

        # Fill username and advance
        username_input = page.locator("#step01")
        username_input.wait_for(state="visible", timeout=10000)
        username_input.fill(self._username)
        page.wait_for_timeout(500)

        page.locator("text=Siguiente").first.click()

        # Fill password and submit
        password_input = page.locator("#step02")
        password_input.wait_for(state="visible", timeout=10000)
        password_input.fill(self._password)
        page.wait_for_timeout(1000)

        submit_buttons = page.locator("icb-button a").filter(has_text="Siguiente")
        for i in range(submit_buttons.count()):
            if submit_buttons.nth(i).is_visible():
                submit_buttons.nth(i).click(timeout=10000)
                break

        # Wait for 2FA / redirect (up to 2 minutes)
        print("Credentials submitted, waiting for 2FA...", flush=True)
        for attempt in range(120):
            try:
                if HOME_PATH in page.url:
                    return True
                page.wait_for_timeout(1000)
            except Exception:
                print("Browser was closed during login.", flush=True)
                return False

        print("Login timed out.", flush=True)
        return False

    def _navigate_to_products(self, page):
        """Navigate to My Products page."""
        products_url = page.url.split("#")[0] + "#" + MY_PRODUCTS_PATH
        page.goto(products_url)
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(3000)

    def _select_account(self, page):
        """Click on the row containing the configured account number."""
        account_locator = page.locator(f"text={self._account_number}").first
        account_locator.wait_for(timeout=10000)
        account_locator.click()
        page.wait_for_timeout(3000)

        # Wait for the account detail view to load
        page.locator("icb-range-date-filter").first.wait_for(state="attached", timeout=15000)
        if not page.locator("icb-range-date-filter").first.is_visible():
            page.wait_for_timeout(3000)

    def _set_date_filter(self, page, start_date: str, end_date: str):
        """Open date filter and set start/end dates."""
        print(f"Setting date range: {start_date} - {end_date}", flush=True)

        # Expand the date filter panel
        header = page.locator("icb-range-date-filter-header:visible").first
        header.wait_for(timeout=10000)
        header.click()
        page.wait_for_timeout(1000)

        # Switch to date range mode
        fecha_link = page.locator("a:has-text('Fecha desde - hasta'):visible").first
        fecha_link.wait_for(timeout=10000)
        fecha_link.click()
        page.wait_for_timeout(1000)

        # Set from-date via calendar picker
        date_components = page.locator("icb-range-date-filter-header icb-date")
        self._pick_date_via_calendar(page, date_components.nth(0), start_date)

        # Set to-date only if different from what's shown
        to_text = date_components.nth(1).text_content().strip()
        if to_text != end_date:
            self._pick_date_via_calendar(page, date_components.nth(1), end_date)

        page.wait_for_timeout(3000)

    def _download_csv(self, page):
        """Click the export button and download CSV."""
        # Click first visible element in the file exporter component
        exporter = page.locator("icb-listfileexporter")
        export_links = exporter.locator("a, button, span")
        for i in range(export_links.count()):
            if export_links.nth(i).is_visible():
                export_links.nth(i).click()
                break
        page.wait_for_timeout(2000)

        # Select CSV format and download
        csv_option = page.locator("text=CSV").first
        if csv_option.is_visible():
            with page.expect_download(timeout=30000) as download_info:
                csv_option.click()
        else:
            with page.expect_download(timeout=30000) as download_info:
                pass

        download = download_info.value
        download.save_as(EXPORT_PATH)
        file_size = os.path.getsize(EXPORT_PATH)
        print(f"Downloaded CSV ({file_size} bytes)", flush=True)

    def _pick_date_via_calendar(self, page, date_element, target_date: str):
        """Click a date element to open calendar, navigate to month, click day.

        target_date is in dd/mm/yyyy format.
        """
        target_day = int(target_date.split("/")[0])
        target_month = int(target_date.split("/")[1])
        target_year = int(target_date.split("/")[2])

        date_element.click()
        page.wait_for_timeout(1000)

        # Calendar is now open — navigate to the correct month
        # The calendar header shows current month/year
        calendar = page.locator("icb-calendar:visible").first
        max_nav = 12
        for _ in range(max_nav):
            # Read current month/year from calendar header
            header_text = calendar.evaluate("""el => {
                // Month and year may be in separate elements
                let month = '', year = '';
                const allEls = el.querySelectorAll('*');
                for (const e of allEls) {
                    if (e.children.length === 0) {
                        const text = e.textContent.trim();
                        if (text.match(/^[a-zA-ZáéíóúÁÉÍÓÚ]+$/) && text.length > 3) month = text;
                        if (text.match(/^\\d{4}$/)) year = text;
                    }
                }
                if (month && year) return month + ' ' + year;
                // Fallback: single element with both
                for (const e of allEls) {
                    if (e.children.length === 0) {
                        const text = e.textContent.trim();
                        if (text.match(/[a-zA-ZáéíóúÁÉÍÓÚ]+\\s+\\d{4}/)) return text;
                    }
                }
                return '';
            }""")
            # Parse the displayed month
            month_names = {
                'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
                'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
                'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
            }
            current_month = None
            current_year = None
            for name, num in month_names.items():
                if name in header_text.lower():
                    current_month = num
                    break
            # Extract year
            for word in header_text.split():
                if word.isdigit() and len(word) == 4:
                    current_year = int(word)

            if current_month is None or current_year is None:
                break

            if current_month == target_month and current_year == target_year:
                break

            # Navigate backwards or forwards
            if (current_year, current_month) > (target_year, target_month):
                calendar.locator("a").filter(has_text="<").first.click()
            else:
                calendar.locator("a").filter(has_text=">").first.click()
            page.wait_for_timeout(500)

        # Click the target day
        day_cell = calendar.locator(f"a:text-is('{target_day}'), span:text-is('{target_day}')").first
        day_cell.click()
        page.wait_for_timeout(1000)
