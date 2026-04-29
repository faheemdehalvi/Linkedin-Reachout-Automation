"""
LinkedIn Browser Automation
Sends messages and connection requests directly on LinkedIn.
Uses Playwright with persistent browser profile for session management.

Safety features:
- Random delays between actions (30-90s)
- Human-like typing with variable speed
- Session limits (25 messages, 25 requests per run)
- Persistent login via browser profile (no re-login needed)
"""
import asyncio
import random
import json
import os
from pathlib import Path
from datetime import datetime

# Safety constants
MIN_DELAY_BETWEEN_ACTIONS = 30   # seconds
MAX_DELAY_BETWEEN_ACTIONS = 90   # seconds
TYPING_MIN_DELAY = 30            # ms per keystroke
TYPING_MAX_DELAY = 120           # ms per keystroke
MAX_MESSAGES_PER_SESSION = 25
MAX_REQUESTS_PER_SESSION = 25

BROWSER_PROFILE_DIR = str(Path(__file__).parent / "data" / "browser_profile")
LINKEDIN_BASE = "https://www.linkedin.com"


class LinkedInBrowser:
    """Playwright-based LinkedIn automation with anti-detection."""

    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None
        self.is_logged_in = False
        self.messages_sent = 0
        self.requests_sent = 0
        self._started = False

    # ─────────────────────────────────────────────
    # Lifecycle
    # ─────────────────────────────────────────────

    async def start(self, headless=False):
        """Launch browser with persistent profile (keeps cookies/session)."""
        if self._started:
            return self.is_logged_in

        from playwright.async_api import async_playwright

        os.makedirs(BROWSER_PROFILE_DIR, exist_ok=True)

        self.playwright = await async_playwright().start()

        self.context = await self.playwright.chromium.launch_persistent_context(
            BROWSER_PROFILE_DIR,
            headless=headless,
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            timezone_id="America/New_York",
            args=[
                "--disable-blink-features=AutomationControlled",
            ],
        )

        # Remove webdriver flag to avoid detection
        self.page = self.context.pages[0] if self.context.pages else await self.context.new_page()
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        """)

        self._started = True
        self.is_logged_in = await self._check_login()
        return self.is_logged_in

    async def _check_login(self):
        """Check if already logged into LinkedIn via saved cookies."""
        try:
            await self.page.goto(
                f"{LINKEDIN_BASE}/feed/",
                wait_until="domcontentloaded",
                timeout=20000,
            )
            await self.page.wait_for_timeout(3000)

            url = self.page.url
            if "/feed" in url or "/mynetwork" in url:
                print("✅ Already logged into LinkedIn")
                return True

            print("❌ Not logged in — login required")
            return False
        except Exception as e:
            print(f"Login check error: {e}")
            return False

    async def login(self, email, password):
        """Login to LinkedIn with email/password."""
        try:
            await self.page.goto(
                f"{LINKEDIN_BASE}/login",
                wait_until="domcontentloaded",
                timeout=20000,
            )
            await self.page.wait_for_timeout(2000)

            # Type email
            email_field = self.page.locator("#username")
            await email_field.fill("")
            await self._human_type(email_field, email)
            await self.page.wait_for_timeout(random.randint(500, 1500))

            # Type password
            pass_field = self.page.locator("#password")
            await pass_field.fill("")
            await self._human_type(pass_field, password)
            await self.page.wait_for_timeout(random.randint(500, 1500))

            # Click sign in
            await self.page.locator('button[type="submit"]').click()
            await self.page.wait_for_timeout(5000)

            # Handle verification/captcha (waits up to 2 mins for manual completion)
            url = self.page.url
            if "checkpoint" in url or "challenge" in url:
                print("⚠️  LinkedIn verification required — complete it in the browser window")
                for _ in range(24):
                    await self.page.wait_for_timeout(5000)
                    if "/feed" in self.page.url:
                        break

            self.is_logged_in = "/feed" in self.page.url or "/mynetwork" in self.page.url

            if self.is_logged_in:
                print("✅ Logged in successfully")
            else:
                print(f"❌ Login may have failed — current URL: {self.page.url}")

            return self.is_logged_in

        except Exception as e:
            print(f"Login error: {e}")
            return False

    async def close(self):
        """Close browser gracefully (session is saved for next time)."""
        if self.context:
            await self.context.close()
        if self.playwright:
            await self.playwright.stop()
        self._started = False
        self.is_logged_in = False
        print("Browser closed")

    # ─────────────────────────────────────────────
    # Send DM to existing connection
    # ─────────────────────────────────────────────

    async def send_message(self, person_name, message, linkedin_url=None):
        """Send a DM to a LinkedIn connection via the messaging compose flow."""
        if not self.is_logged_in:
            return {"status": "error", "message": "Not logged in"}

        if self.messages_sent >= MAX_MESSAGES_PER_SESSION:
            return {"status": "limit_reached", "message": f"Session limit reached ({MAX_MESSAGES_PER_SESSION})"}

        try:
            # Navigate to messaging
            await self.page.goto(
                f"{LINKEDIN_BASE}/messaging/",
                wait_until="domcontentloaded",
                timeout=20000,
            )
            await self._random_wait(2000, 4000)

            # Click compose / new message
            compose_btn = await self._find_first([
                'a[href="/messaging/thread/new/"]',
                'button[class*="msg-overlay-bubble-header"]',
                'header button[class*="compose"]',
            ])
            if not compose_btn:
                # Try clicking the pencil icon
                compose_btn = self.page.locator(
                    'svg[data-test-icon="compose-small"], '
                    'button[aria-label*="Compose"], '
                    'button[aria-label*="new message"], '
                    'a[data-control-name="overlay.compose_message"]'
                ).first
            await compose_btn.click()
            await self._random_wait(1500, 3000)

            # Type person name in the "To" field
            to_field = await self._find_first([
                'input[name="searchTerm"]',
                'input[placeholder*="name"]',
                'input[role="combobox"]',
                'input[class*="msg-connections-typeahead"]',
            ])
            if not to_field:
                return {"status": "error", "message": "Could not find the To field"}

            await self._human_type(to_field, person_name)
            await self._random_wait(2000, 4000)

            # Select person from dropdown suggestions
            suggestion = await self._find_first([
                '[role="option"]',
                '.msg-connections-typeahead__search-result',
                'li.basic-typeahead__selectable',
                '.msg-search-pill',
            ])
            if not suggestion:
                return {"status": "error", "message": f"Could not find '{person_name}' in connections"}

            await suggestion.click()
            await self._random_wait(1000, 2000)

            # Type the message
            msg_box = await self._find_first([
                'div.msg-form__contenteditable[role="textbox"]',
                'div.msg-form__contenteditable',
                '[contenteditable="true"][role="textbox"]',
                'div[aria-label*="Write a message"]',
            ])
            if not msg_box:
                return {"status": "error", "message": "Could not find message input box"}

            await msg_box.click()
            await self.page.wait_for_timeout(500)
            await self._human_type(msg_box, message)
            await self._random_wait(1000, 2000)

            # Click send
            send_btn = await self._find_first([
                'button.msg-form__send-button',
                'button[type="submit"]',
                'button[aria-label*="Send"]',
            ])
            if not send_btn:
                return {"status": "error", "message": "Could not find Send button"}

            await send_btn.click()
            await self._random_wait(2000, 4000)

            self.messages_sent += 1
            print(f"✅ Message sent to {person_name} ({self.messages_sent}/{MAX_MESSAGES_PER_SESSION})")

            # Anti-detection delay
            delay = random.randint(MIN_DELAY_BETWEEN_ACTIONS, MAX_DELAY_BETWEEN_ACTIONS)
            print(f"⏳ Waiting {delay}s before next action...")
            await self.page.wait_for_timeout(delay * 1000)

            return {
                "status": "sent",
                "person": person_name,
                "messages_sent_total": self.messages_sent,
                "sent_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            print(f"❌ Error messaging {person_name}: {e}")
            return {"status": "error", "message": f"Error messaging {person_name}: {str(e)}"}

    # ─────────────────────────────────────────────
    # Send connection request to prospect
    # ─────────────────────────────────────────────

    async def send_connection_request(self, person_name, note="", linkedin_url=None):
        """Send a connection request with an optional note."""
        if not self.is_logged_in:
            return {"status": "error", "message": "Not logged in"}

        if self.requests_sent >= MAX_REQUESTS_PER_SESSION:
            return {"status": "limit_reached", "message": f"Session limit reached ({MAX_REQUESTS_PER_SESSION})"}

        try:
            if linkedin_url:
                await self.page.goto(linkedin_url, wait_until="domcontentloaded", timeout=20000)
            else:
                # Search for the person
                encoded = person_name.replace(" ", "%20")
                await self.page.goto(
                    f"{LINKEDIN_BASE}/search/results/people/?keywords={encoded}",
                    wait_until="domcontentloaded",
                    timeout=20000,
                )
                await self._random_wait(3000, 5000)

                # Click the first matching profile
                profile_link = self.page.locator(
                    'a.app-aware-link[href*="/in/"] span[aria-hidden="true"], '
                    'a[href*="/in/"] span.entity-result__title-text'
                ).first
                if await profile_link.count() > 0:
                    await profile_link.click()
                    await self._random_wait(2000, 4000)
                else:
                    return {"status": "error", "message": f"Could not find profile for '{person_name}'"}

            await self._random_wait(2000, 4000)

            # Try to find Connect button (may be in "More" dropdown)
            connect_btn = await self._find_connect_button()
            if not connect_btn:
                return {
                    "status": "error",
                    "message": f"No Connect button for {person_name} — may already be connected",
                }

            await connect_btn.click()
            await self._random_wait(1500, 3000)

            # Add a note if provided
            if note:
                add_note_btn = self.page.locator('button:has-text("Add a note")').first
                if await add_note_btn.count() > 0:
                    await add_note_btn.click()
                    await self._random_wait(1000, 2000)

                    note_field = await self._find_first([
                        'textarea[name="message"]',
                        'textarea#custom-message',
                        'textarea',
                    ])
                    if note_field:
                        await self._human_type(note_field, note[:300])  # LinkedIn 300 char limit
                        await self._random_wait(1000, 2000)

            # Click Send
            send_btn = self.page.locator(
                'button[aria-label*="Send"], button:has-text("Send")'
            ).last
            await send_btn.click()
            await self._random_wait(2000, 4000)

            self.requests_sent += 1
            print(f"✅ Connection request sent to {person_name} ({self.requests_sent}/{MAX_REQUESTS_PER_SESSION})")

            # Anti-detection delay
            delay = random.randint(MIN_DELAY_BETWEEN_ACTIONS, MAX_DELAY_BETWEEN_ACTIONS)
            print(f"⏳ Waiting {delay}s before next action...")
            await self.page.wait_for_timeout(delay * 1000)

            return {
                "status": "sent",
                "person": person_name,
                "requests_sent_total": self.requests_sent,
                "sent_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            print(f"❌ Error connecting with {person_name}: {e}")
            return {"status": "error", "message": f"Error: {str(e)}"}

    # ─────────────────────────────────────────────
    # Batch operations
    # ─────────────────────────────────────────────

    async def send_batch_messages(self, messages_list):
        """Send multiple DMs with human-like delays. Returns summary."""
        results = []
        total = len(messages_list)

        for i, item in enumerate(messages_list):
            name = item.get("name", "")
            message = item.get("message", "")
            url = item.get("linkedin_url")

            print(f"\n📤 [{i+1}/{total}] Sending DM to {name}...")
            result = await self.send_message(name, message, url)
            result["index"] = i
            results.append(result)

            if result["status"] == "limit_reached":
                print("⚠️  Session limit — stopping batch")
                break

        sent = sum(1 for r in results if r["status"] == "sent")
        failed = sum(1 for r in results if r["status"] == "error")
        print(f"\n📊 Batch DMs: {sent} sent, {failed} failed out of {total}")
        return {"sent": sent, "failed": failed, "total": total, "results": results}

    async def send_batch_requests(self, requests_list):
        """Send multiple connection requests with human-like delays."""
        results = []
        total = len(requests_list)

        for i, item in enumerate(requests_list):
            name = item.get("name", "")
            note = item.get("note", "")
            url = item.get("linkedin_url")

            print(f"\n📤 [{i+1}/{total}] Connecting with {name}...")
            result = await self.send_connection_request(name, note, url)
            result["index"] = i
            results.append(result)

            if result["status"] == "limit_reached":
                print("⚠️  Session limit — stopping batch")
                break

        sent = sum(1 for r in results if r["status"] == "sent")
        failed = sum(1 for r in results if r["status"] == "error")
        print(f"\n📊 Batch requests: {sent} sent, {failed} failed out of {total}")
        return {"sent": sent, "failed": failed, "total": total, "results": results}

    # ─────────────────────────────────────────────
    # Scraping: Existing connections
    # ─────────────────────────────────────────────

    async def scrape_my_connections(self, max_pages=5):
        """
        Scrape the logged-in user's existing LinkedIn connections.
        Navigates to 'My Network > Connections' and extracts name, title, 
        company, and profile URL for each connection.

        Args:
            max_pages: How many pages of connections to scroll/scrape (each ~10-40 people).

        Returns:
            List of dicts with keys: name, title, company, linkedin_url, connection_status
        """
        if not self.is_logged_in:
            print("Not logged in -- cannot scrape connections.")
            return []

        leads = []
        seen_urls = set()

        try:
            await self.page.goto(
                f"{LINKEDIN_BASE}/mynetwork/invite-connect/connections/",
                wait_until="domcontentloaded",
                timeout=20000,
            )
            await self._random_wait(3000, 5000)

            for page_num in range(max_pages):
                print(f"[Scrape] Scrolling connections page {page_num + 1}/{max_pages}...")

                # Scroll down to load more cards
                for _ in range(3):
                    await self.page.evaluate("window.scrollBy(0, window.innerHeight)")
                    await self._random_wait(1500, 3000)

                # Extract connection cards
                cards = self.page.locator('li.mn-connection-card')
                count = await cards.count()

                for i in range(count):
                    try:
                        card = cards.nth(i)

                        # Name
                        name_el = card.locator('span.mn-connection-card__name').first
                        name = (await name_el.text_content()).strip() if await name_el.count() > 0 else ""

                        # Title / occupation
                        title_el = card.locator('span.mn-connection-card__occupation').first
                        occupation = (await title_el.text_content()).strip() if await title_el.count() > 0 else ""

                        # Profile URL
                        link_el = card.locator('a[href*="/in/"]').first
                        href = await link_el.get_attribute('href') if await link_el.count() > 0 else ""
                        if href and not href.startswith("http"):
                            href = LINKEDIN_BASE + href

                        if not name or href in seen_urls:
                            continue
                        seen_urls.add(href)

                        # Split occupation into title + company if possible
                        title = occupation
                        company = ""
                        if " at " in occupation:
                            parts = occupation.split(" at ", 1)
                            title = parts[0].strip()
                            company = parts[1].strip()

                        leads.append({
                            "name": name,
                            "title": title,
                            "company": company,
                            "linkedin_url": href,
                            "connection_status": "connection",  # they are already connected
                        })
                    except Exception:
                        continue

                # Check if there is a "Show more" button
                show_more = self.page.locator('button:has-text("Show more results")').first
                if await show_more.count() > 0 and await show_more.is_visible():
                    await show_more.click()
                    await self._random_wait(2000, 4000)
                else:
                    break  # no more pages

            print(f"[Scrape] Found {len(leads)} existing connections.")

        except Exception as e:
            print(f"[Scrape] Error scraping connections: {e}")

        return leads

    # ─────────────────────────────────────────────
    # Scraping: Discover new prospects via search
    # ─────────────────────────────────────────────

    async def scrape_prospects(self, keywords, max_pages=3):
        """
        Search LinkedIn People with keywords and extract profile cards.
        Only returns people you are NOT already connected with.

        Args:
            keywords: Search query, e.g. "SaaS founder", "Data Engineer", "Product Manager fintech"
            max_pages: How many search result pages to scrape (each has ~10 results).

        Returns:
            List of dicts with keys: name, title, company, linkedin_url, connection_status
        """
        if not self.is_logged_in:
            print("Not logged in -- cannot search prospects.")
            return []

        leads = []
        seen_urls = set()

        try:
            for page_num in range(1, max_pages + 1):
                encoded = keywords.replace(" ", "%20")
                url = f"{LINKEDIN_BASE}/search/results/people/?keywords={encoded}&page={page_num}"

                print(f"[Scrape] Searching '{keywords}' - page {page_num}/{max_pages}...")
                await self.page.goto(url, wait_until="domcontentloaded", timeout=20000)
                await self._random_wait(3000, 5000)

                # Scroll to load all results
                for _ in range(3):
                    await self.page.evaluate("window.scrollBy(0, window.innerHeight)")
                    await self._random_wait(1000, 2000)

                # Extract result cards
                cards = self.page.locator('li.reusable-search__result-container')
                count = await cards.count()

                if count == 0:
                    print(f"[Scrape] No more results on page {page_num}. Stopping.")
                    break

                for i in range(count):
                    try:
                        card = cards.nth(i)

                        # Skip people who are already connected (look for "Message" button instead of "Connect")
                        message_btn = card.locator('button:has-text("Message")').first
                        if await message_btn.count() > 0:
                            continue  # already connected, skip

                        # Name
                        name_el = card.locator('span[aria-hidden="true"]').first
                        name = (await name_el.text_content()).strip() if await name_el.count() > 0 else ""

                        # Skip "LinkedIn Member" (private profiles)
                        if not name or "LinkedIn Member" in name:
                            continue

                        # Profile URL
                        link_el = card.locator('a[href*="/in/"]').first
                        href = await link_el.get_attribute('href') if await link_el.count() > 0 else ""
                        if href and not href.startswith("http"):
                            href = LINKEDIN_BASE + href
                        # Clean tracking params
                        if "?" in href:
                            href = href.split("?")[0]

                        if href in seen_urls:
                            continue
                        seen_urls.add(href)

                        # Title
                        title_el = card.locator('div.entity-result__primary-subtitle').first
                        title = (await title_el.text_content()).strip() if await title_el.count() > 0 else ""

                        # Company (secondary subtitle)
                        company_el = card.locator('div.entity-result__secondary-subtitle').first
                        company = (await company_el.text_content()).strip() if await company_el.count() > 0 else ""

                        leads.append({
                            "name": name,
                            "title": title,
                            "company": company,
                            "linkedin_url": href,
                            "connection_status": "prospect",
                        })
                    except Exception:
                        continue

                # Human-like delay between pages
                delay = random.randint(MIN_DELAY_BETWEEN_ACTIONS, MAX_DELAY_BETWEEN_ACTIONS)
                print(f"[Scrape] Anti-detection pause ({delay}s) before next page...")
                await self.page.wait_for_timeout(delay * 1000)

            print(f"[Scrape] Found {len(leads)} new prospects for '{keywords}'.")

        except Exception as e:
            print(f"[Scrape] Error scraping prospects: {e}")

        return leads

    # ─────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────

    async def _find_first(self, selectors):
        """Try multiple CSS selectors and return the first match."""
        for sel in selectors:
            loc = self.page.locator(sel).first
            if await loc.count() > 0:
                return loc
        return None

    async def _find_connect_button(self):
        """Find the Connect button, checking both top-level and More menu."""
        # Direct Connect button
        btn = self.page.locator(
            'button.pvs-profile-actions__action:has-text("Connect"), '
            'button[aria-label*="connect" i]:not([aria-label*="disconnect"])'
        ).first
        if await btn.count() > 0:
            return btn

        # Check inside "More" dropdown
        more_btn = self.page.locator(
            'button[aria-label="More actions"], '
            'button.pvs-profile-actions__action--overflow'
        ).first
        if await more_btn.count() > 0:
            await more_btn.click()
            await self.page.wait_for_timeout(1000)
            connect_item = self.page.locator(
                '[role="menuitem"]:has-text("Connect"), '
                'div.artdeco-dropdown__item:has-text("Connect")'
            ).first
            if await connect_item.count() > 0:
                return connect_item

        return None

    async def _human_type(self, element, text):
        """Type text with human-like variable speed."""
        for char in text:
            await element.type(char, delay=random.randint(TYPING_MIN_DELAY, TYPING_MAX_DELAY))
            # Occasional longer pause (thinking)
            if random.random() < 0.05:
                await self.page.wait_for_timeout(random.randint(300, 800))

    async def _random_wait(self, min_ms, max_ms):
        """Wait a random duration."""
        await self.page.wait_for_timeout(random.randint(min_ms, max_ms))

    def get_session_stats(self):
        """Return current session stats."""
        return {
            "is_logged_in": self.is_logged_in,
            "messages_sent": self.messages_sent,
            "messages_limit": MAX_MESSAGES_PER_SESSION,
            "requests_sent": self.requests_sent,
            "requests_limit": MAX_REQUESTS_PER_SESSION,
            "browser_running": self._started,
        }
