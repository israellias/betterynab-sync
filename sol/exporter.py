import os
import shutil
import sys
from datetime import date

from playwright.sync_api import sync_playwright

from sol.config import SolConfig

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT_DIR = os.path.dirname(MODULE_DIR)
BROWSER_DATA_DIR = os.path.join(SCRIPT_DIR, ".sol_browser_data")
EXPORT_PATH = os.path.join(MODULE_DIR, "export.pdf")

BASE_URL = "https://solnetdigital.bancosol.com.bo/"
LOGIN_URL = BASE_URL + "login"
DASHBOARD_URL = BASE_URL + "dashboard/extract"


class SolExporter:
    def __init__(self, config: SolConfig):
        self._config = config

    def export(self, since_date: str = None) -> str:
        """Login to Banco Sol and download account PDF. Returns path to saved file.

        Args:
            since_date: Start date in YYYY-MM-DD format. If provided, uses custom
                        date range. Otherwise downloads the default statement.
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

            print("Logged in to Banco Sol.", flush=True)

            # Navigate to Historial de movimientos
            self._navigate_to_history(page)

            # Set date range if since_date provided
            if since_date:
                self._select_date_range(page, since_date)

            # Download PDF
            save_path = self._download_pdf(page)
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
        """Navigate to Banco Sol and log in via Banca Personas."""
        page.goto(BASE_URL)
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(3000)

        # Check if already logged in (redirected to dashboard)
        if "/dashboard" in page.url:
            return True

        # Step 1: Click "Banca personas - Iniciar sesion"
        banca_personas = page.locator('text=Banca personas').first
        if banca_personas.count() == 0:
            banca_personas = page.locator('a:has-text("Banca personas"), button:has-text("Banca personas")').first
        banca_personas.wait_for(state="visible", timeout=15000)
        banca_personas.click()
        page.wait_for_timeout(3000)

        # Check if already at dashboard after clicking
        if "/dashboard" in page.url:
            return True

        # Step 2: Fill username and password on the login form
        page.wait_for_selector('input', timeout=15000)

        # Find the Usuario input field
        usuario_input = page.locator('input[type="text"], input[placeholder*="Usuario"], input[name*="user"]').first
        usuario_input.wait_for(state="visible", timeout=10000)
        usuario_input.fill(self._config.username)
        page.wait_for_timeout(500)

        # Find the Contrasena input field
        password_input = page.locator('input[type="password"]').first
        password_input.wait_for(state="visible", timeout=10000)
        password_input.fill(self._config.password)
        page.wait_for_timeout(500)

        # Click the "Ingresar" button
        ingresar_btn = page.locator('button:has-text("Ingresar")').first
        ingresar_btn.click()

        # Wait for login to complete (may have 2FA)
        for _ in range(120):
            page.wait_for_timeout(1000)
            if "/dashboard" in page.url:
                return True
            body = page.inner_text("body")[:500]
            if "bloqueado" in body.lower() or "error" in body.lower():
                print("Login error detected.", flush=True)
                return False

        print("Login timed out.", flush=True)
        return False

    def _navigate_to_history(self, page):
        """Click 'Historial de movimientos' in the sidebar."""
        historial = page.locator('text=Historial de movimientos').first
        historial.wait_for(state="visible", timeout=15000)
        historial.click()
        page.wait_for_timeout(3000)
        page.wait_for_load_state("networkidle")

    def _select_date_range(self, page, since_date: str):
        """Set a custom date range using the Rango de busqueda dropdown.

        Based on the Banco Sol UI flow:
        1. Open "Rango de búsqueda" dropdown
        2. Select "Personalizado"
        3. Click "Fecha" input to open calendar
        4. Navigate calendar to pick start date, then end date
        5. Click "Ok" to confirm

        Args:
            since_date: Start date in YYYY-MM-DD format.
        """
        start_year, start_month, start_day = [int(x) for x in since_date.split("-")]
        today = date.today()

        # Step 1: Click the "Rango de búsqueda" custom dropdown to open it
        rango_dropdown = page.locator('text=Rango de búsqueda').first
        if rango_dropdown.count() > 0:
            rango_dropdown.click()
            page.wait_for_timeout(1000)

        # Step 2: Select "Personalizado" from the opened dropdown options
        personalizado = page.locator('text=Personalizado').first
        if personalizado.count() > 0 and personalizado.is_visible():
            personalizado.click()
            print("Selected: Personalizado", flush=True)
        else:
            print("Could not find 'Personalizado' option.", flush=True)
        page.wait_for_timeout(2000)

        # Step 3: Click the calendar icon button next to the "Fecha" input
        # Use Playwright locator to find and click the button with calendar icon
        # The structure is: container > input[placeholder="Fecha"] + button(with svg icon)
        fecha_input = page.locator('input[placeholder="Fecha"]').first
        if fecha_input.count() > 0:
            # Get the bounding box of the Fecha input to find the icon to its right
            box = fecha_input.bounding_box()
            if box:
                # Click to the right of the input where the calendar icon is
                page.mouse.click(box["x"] + box["width"] + 20, box["y"] + box["height"] / 2)
                print("Clicked calendar icon area", flush=True)
        page.wait_for_timeout(2000)

        # Step 3: Pick the start date in the calendar
        self._pick_date_in_calendar(page, start_year, start_month, start_day)
        page.wait_for_timeout(1000)

        # After picking start date, the calendar might still be open for end date
        # Or we might need to click again to pick end date
        # Take a screenshot to see state
        page.screenshot(path=os.path.join(MODULE_DIR, "debug_after_start.png"))

        # Step 4: Pick the end date (today)
        self._pick_date_in_calendar(page, today.year, today.month, today.day)
        page.wait_for_timeout(1000)

        page.screenshot(path=os.path.join(MODULE_DIR, "debug_after_end.png"))

        # Step 5: Click "Ok" to confirm the date range
        ok_btn = page.locator('button:has-text("Ok")').first
        if ok_btn.count() > 0 and ok_btn.is_visible():
            ok_btn.click()
            print("Clicked Ok to confirm date range", flush=True)
            page.wait_for_timeout(5000)
            page.wait_for_load_state("networkidle")
        else:
            print("No Ok button found/visible", flush=True)

        page.screenshot(path=os.path.join(MODULE_DIR, "debug_after_ok.png"))
        print(f"Filtered: {since_date} → {today.isoformat()}", flush=True)

    def _pick_date_in_calendar(self, page, target_year: int, target_month: int, target_day: int):
        """Navigate the Banco Sol calendar picker to a specific date.

        The calendar has < and > nav buttons with a "Month Year" header between them.
        Day cells are buttons in a grid.
        """
        import re

        MONTH_LOOKUP = {
            "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
            "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
            "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
        }

        def _read_calendar_header():
            """Read the month/year from the calendar header using multiple strategies."""
            return page.evaluate("""() => {
                // Strategy 1: Find any element whose text matches "Month Year" pattern
                // Look in the calendar popup area (near the day grid)
                const allElements = document.querySelectorAll('*');
                const monthPattern = /^(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\\s+\\d{4}$/i;
                for (const el of allElements) {
                    // Only check leaf-ish elements (avoid containers that include all calendar text)
                    if (el.children.length <= 2) {
                        const text = el.textContent.trim();
                        if (monthPattern.test(text)) {
                            return text;
                        }
                    }
                }

                // Strategy 2: Find elements containing a Spanish month name + 4-digit year
                // with short text length (to avoid matching whole calendar body)
                const monthNames = ['enero','febrero','marzo','abril','mayo','junio',
                                    'julio','agosto','septiembre','octubre','noviembre','diciembre'];
                for (const el of allElements) {
                    const text = el.textContent.trim();
                    if (text.length > 5 && text.length < 25) {
                        const lower = text.toLowerCase();
                        const hasMonth = monthNames.some(m => lower.includes(m));
                        const hasYear = /\\d{4}/.test(text);
                        if (hasMonth && hasYear) {
                            return text;
                        }
                    }
                }

                return '';
            }""")

        for attempt in range(24):
            page.wait_for_timeout(500)

            header_text = _read_calendar_header()
            print(f"Calendar header: '{header_text}' (attempt {attempt})", flush=True)

            if not header_text:
                # If still empty, try a DOM debug dump on first attempt
                if attempt == 0:
                    debug_info = page.evaluate("""() => {
                        // Find all buttons and their attributes
                        const buttons = document.querySelectorAll('button');
                        const info = [];
                        for (const btn of buttons) {
                            const text = btn.textContent.trim().substring(0, 50);
                            const name = btn.getAttribute('name') || '';
                            const cls = btn.className.substring(0, 80);
                            if (text || name) {
                                info.push(`name="${name}" class="${cls}" text="${text}"`);
                            }
                        }
                        return info.join('\\n');
                    }""")
                    print(f"DOM buttons debug:\\n{debug_info}", flush=True)
                break

            current_month = None
            current_year = None
            for name, num in MONTH_LOOKUP.items():
                if name in header_text.lower():
                    current_month = num
                    break
            year_match = re.search(r'\d{4}', header_text)
            if year_match:
                current_year = int(year_match.group())

            if current_month is None or current_year is None:
                print(f"Could not parse: '{header_text}'", flush=True)
                break

            if current_month == target_month and current_year == target_year:
                print(f"Calendar at correct month: {header_text}", flush=True)
                break

            # Navigate: try rdp name selectors first, then fall back to text < >
            if (current_year, current_month) > (target_year, target_month):
                prev_btn = page.locator('button[name="previous-month"]')
                if prev_btn.count() > 0:
                    prev_btn.click()
                else:
                    page.locator('button:has-text("<")').first.click()
                print(f"Calendar: navigated back from {header_text}", flush=True)
            else:
                next_btn = page.locator('button[name="next-month"]')
                if next_btn.count() > 0:
                    next_btn.click()
                else:
                    page.locator('button:has-text(">")').first.click()
                print(f"Calendar: navigated forward from {header_text}", flush=True)
            page.wait_for_timeout(500)

        # Click the target day — try rdp name="day" first, then generic buttons in grid
        day_clicked = False
        day_buttons = page.locator('button[name="day"]')
        if day_buttons.count() > 0:
            for i in range(day_buttons.count()):
                btn = day_buttons.nth(i)
                if btn.is_visible() and btn.text_content().strip() == str(target_day):
                    btn.click()
                    day_clicked = True
                    print(f"Calendar: clicked day {target_day} (rdp)", flush=True)
                    break

        if not day_clicked:
            # Fallback: find buttons with just the day number as text
            all_buttons = page.locator('button')
            for i in range(all_buttons.count()):
                btn = all_buttons.nth(i)
                if btn.is_visible() and btn.text_content().strip() == str(target_day):
                    # Avoid clicking nav buttons or other action buttons
                    name = btn.get_attribute("name") or ""
                    if name in ("previous-month", "next-month"):
                        continue
                    btn.click()
                    day_clicked = True
                    print(f"Calendar: clicked day {target_day} (fallback)", flush=True)
                    break

        if not day_clicked:
            print(f"Calendar: could NOT find day {target_day}", flush=True)

        page.wait_for_timeout(500)

    def _download_pdf(self, page) -> str | None:
        """Click 'Descargar historial' and select 'Formato pdf'."""
        # Scroll to bottom to reveal any hidden buttons
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1000)

        # Find a visible AND enabled "Descargar historial" button
        descargar_buttons = page.locator('button:has-text("Descargar"), a:has-text("Descargar")')
        descargar = None
        for i in range(descargar_buttons.count()):
            btn = descargar_buttons.nth(i)
            if btn.is_visible() and btn.is_enabled():
                text = btn.text_content() or ""
                if "historial" in text.lower() or "Descargar" in text:
                    descargar = btn
                    break

        if descargar is None:
            print("No visible+enabled 'Descargar historial' button found.", flush=True)
            return None

        descargar.click()
        page.wait_for_timeout(3000)

        # The menu shows: "Formato PDF" header with a "Descargar" link below it
        # We need to find the "Descargar" link associated with "Formato PDF"

        # Strategy: Find the section containing "Formato PDF" text, then click its "Descargar" link
        pdf_section = page.locator('text=Formato PDF').first
        if pdf_section.count() == 0:
            print("No 'Formato PDF' section found.", flush=True)
            return None

        # Look for "Descargar" link near the "Formato PDF" text
        # Try parent container approach
        pdf_container = pdf_section.locator('..').first  # Parent element
        pdf_download_link = pdf_container.locator('text=Descargar').first

        if pdf_download_link.count() == 0:
            # Try sibling approach
            pdf_download_link = page.locator('text=Formato PDF').locator('..').locator('text=Descargar').first

        if pdf_download_link.count() == 0:
            print("No 'Descargar' link found for PDF format.", flush=True)
            return None

        with page.expect_download(timeout=30000) as download_info:
            pdf_download_link.click()

        download = download_info.value
        download.save_as(EXPORT_PATH)
        file_size = os.path.getsize(EXPORT_PATH)
        print(f"Downloaded PDF ({file_size} bytes)", flush=True)
        return EXPORT_PATH
