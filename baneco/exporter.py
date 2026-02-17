import os
import shutil
import sys
import time

from playwright.sync_api import sync_playwright

from baneco.config import BanecoConfig


SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BROWSER_DATA_DIR = os.path.join(SCRIPT_DIR, ".baneco_browser_data")
DOWNLOAD_DIR = os.path.join(SCRIPT_DIR, "file_import")
CODE_FILE = "/tmp/baneco_2fa_code"


class BanecoExporter:
    def __init__(self, config: BanecoConfig):
        self._config = config

    def export(self, since_date: str = None) -> str:
        """Login to Baneco and download account CSV. Returns path to saved file.

        Args:
            since_date: If provided, selects a custom date range starting from
                        this date. Otherwise downloads the default statement.
        """
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                BROWSER_DATA_DIR,
                headless=False,
                accept_downloads=True,
            )
            page = context.pages[0] if context.pages else context.new_page()

            if not self._login(page):
                print("Login failed.", flush=True)
                context.close()
                sys.exit(1)

            account = self._config.baneco_account
            print(f"Logged in. Exporting account {account}...", flush=True)
            save_path = self._download_csv(page, account, since_date)
            context.close()

            if not save_path:
                print("Export failed.", flush=True)
                sys.exit(1)

            print(f"Saved: {save_path}", flush=True)
            return save_path

    def reset(self):
        """Clear persistent browser state to force fresh login."""
        if os.path.exists(BROWSER_DATA_DIR):
            shutil.rmtree(BROWSER_DATA_DIR)
            print("Browser state cleared.", flush=True)

    def _login(self, page) -> bool:
        page.goto("https://benet.baneco.com.bo/login")
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(5000)

        if "/home" in page.url:
            return True

        page.wait_for_selector('input[type="text"]', timeout=15000)
        inputs = page.locator('input[type="text"]')
        inputs.nth(0).fill(self._config.baneco_username)
        inputs.nth(1).fill(self._config.baneco_password)

        checkbox = page.locator("mat-checkbox")
        if checkbox.count() > 0 and checkbox.is_visible():
            checkbox.click()
        page.wait_for_timeout(500)

        page.click('button[type="submit"]')

        for _ in range(30):
            page.wait_for_timeout(1000)
            if "/home" in page.url:
                return True
            body = page.inner_text("body")[:500]
            if "Código de Autorización" in body:
                return self._handle_2fa(page)
            if "bloqueado" in body.lower():
                print("Account blocked.", flush=True)
                return False

        print("Login timed out.", flush=True)
        return False

    def _handle_2fa(self, page) -> bool:
        if os.path.exists(CODE_FILE):
            os.remove(CODE_FILE)

        print(f"2FA required. Write code to {CODE_FILE}", flush=True)
        print(f'  echo "123456" > {CODE_FILE}', flush=True)

        while not os.path.exists(CODE_FILE):
            time.sleep(1)

        with open(CODE_FILE, "r") as f:
            code = f.read().strip()
        os.remove(CODE_FILE)

        print("Submitting 2FA code...", flush=True)
        page.locator('input[maxlength="6"]').fill(code)
        page.wait_for_timeout(500)
        page.click('button:has-text("Continuar")')
        page.wait_for_timeout(8000)
        page.wait_for_load_state("networkidle")
        return "/home" in page.url

    # Spanish month abbreviations for Baneco date format (DD/Mon/YYYY)
    _MONTHS_ES = {
        "01": "Ene", "02": "Feb", "03": "Mar", "04": "Abr",
        "05": "May", "06": "Jun", "07": "Jul", "08": "Ago",
        "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dic",
    }

    @staticmethod
    def _to_baneco_date(iso_date: str) -> str:
        """Convert '2026-02-01' to '01/Feb/2026' (Baneco's input format)."""
        year, month, day = iso_date.split("-")
        return f"{day}/{BanecoExporter._MONTHS_ES[month]}/{year}"

    def _select_date_range(self, page, since_date: str):
        """Set a custom date range on the account detail page before downloading.

        Opens the filter panel, selects "Rango de fechas" from the Período
        dropdown, fills start/end dates, and clicks Buscar.
        """
        filter_toggle = page.locator('button:has-text("Buscar o filtrar")')
        if filter_toggle.count() == 0:
            print("No filter button found, using default range.", flush=True)
            return

        filter_toggle.first.click()
        page.wait_for_timeout(2000)

        # Select "Rango de fechas" from the Período dropdown
        periodo_select = page.locator("mat-select")
        if periodo_select.count() == 0:
            print("No Período dropdown found, using default range.", flush=True)
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
            return

        periodo_select.first.click()
        page.wait_for_timeout(1000)

        rango_option = page.locator('mat-option:has-text("Rango de fechas")')
        if rango_option.count() == 0:
            print("No 'Rango de fechas' option found, using default range.", flush=True)
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
            return

        rango_option.first.click()
        page.wait_for_timeout(1000)

        # Fill start and end date inputs (format: DD/Mon/YYYY)
        from datetime import date

        start_str = self._to_baneco_date(since_date)
        end_str = self._to_baneco_date(date.today().isoformat())

        date_inputs = page.locator('input[placeholder*="Ej."]')
        if date_inputs.count() >= 2:
            date_inputs.nth(0).fill(start_str)
            date_inputs.nth(1).fill(end_str)
            page.wait_for_timeout(500)
        else:
            print("Date inputs not found after selecting Rango de fechas.", flush=True)
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
            return

        # Click "Buscar" inside the overlay to apply the filter
        buscar_btn = page.locator('.cdk-overlay-pane button:has-text("Buscar")')
        if buscar_btn.count() > 0:
            buscar_btn.first.click()
            page.wait_for_timeout(3000)
            page.wait_for_load_state("networkidle")
            print(f"Filtered: {start_str} → {end_str}", flush=True)
        else:
            print("No Buscar button found.", flush=True)
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)

    def _download_csv(self, page, account: str, since_date: str = None) -> str | None:
        page.wait_for_selector("text=Cajas de ahorros", timeout=20000)

        ver = page.locator(f'tr:has-text("{account}") >> text=Ver')
        if ver.count() == 0:
            ver = page.locator(
                f'tr:has-text("{account}") a, tr:has-text("{account}") button'
            )
        if ver.count() == 0:
            print(f"Account {account} not found.", flush=True)
            return None

        ver.first.click()
        page.wait_for_timeout(5000)
        page.wait_for_load_state("networkidle")

        if since_date:
            self._select_date_range(page, since_date)

        descargar = page.locator('button:has-text("Descargar")')
        if descargar.count() == 0:
            print("No download button found.", flush=True)
            return None

        descargar.first.click()
        page.wait_for_timeout(2000)

        csv_opt = page.locator(
            '.cdk-overlay-pane button:has-text("CSV"), .cdk-overlay-pane a:has-text("CSV")'
        )
        if csv_opt.count() == 0:
            print("No CSV option found.", flush=True)
            return None

        with page.expect_download(timeout=15000) as download_info:
            csv_opt.first.click()

        download = download_info.value
        filename = download.suggested_filename or f"baneco_{account}.csv"
        save_path = os.path.join(DOWNLOAD_DIR, filename)
        download.save_as(save_path)
        return save_path
