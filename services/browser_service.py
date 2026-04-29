"""
Browser Service
Singleton wrapper around LinkedInBrowser with connection pooling,
retry logic, and session persistence across pipeline runs.
"""
import asyncio
import random
from typing import Optional
from linkedin_browser import LinkedInBrowser

# Shared singleton — one browser session across the whole process
_browser: Optional[LinkedInBrowser] = None
_lock = asyncio.Lock()


async def get_browser(headless: bool = False) -> LinkedInBrowser:
    """Return the shared browser instance, starting it if needed."""
    global _browser
    async with _lock:
        if _browser is None:
            _browser = LinkedInBrowser()
        if not _browser._started:
            await _browser.start(headless=headless)
    return _browser


async def ensure_logged_in(email: str = None, password: str = None, headless: bool = False) -> bool:
    """
    Ensure the browser is running and logged into LinkedIn.
    Returns True if logged in, False otherwise.
    """
    browser = await get_browser(headless=headless)
    if browser.is_logged_in:
        return True
    if email and password:
        return await browser.login(email, password)
    # Wait up to 3 minutes for manual login
    for i in range(36):
        await asyncio.sleep(5)
        if await browser._check_login():
            return True
        if i % 6 == 0:
            print(f"[BrowserService] Waiting for manual login... ({i * 5}s)")
    return False


async def send_dm(name: str, message: str, linkedin_url: str = None) -> dict:
    """
    Send a DM to an existing LinkedIn connection.
    Retries once on transient errors.
    """
    browser = await get_browser()
    for attempt in range(2):
        result = await browser.send_message(name, message, linkedin_url)
        if result["status"] in ("sent", "limit_reached"):
            return result
        if attempt == 0:
            await asyncio.sleep(random.uniform(3, 7))
    return result


async def send_connection_request(name: str, note: str, linkedin_url: str = None) -> dict:
    """
    Send a connection request with an optional note (<300 chars).
    Retries once on transient errors.
    """
    browser = await get_browser()
    note_trimmed = (note or "")[:300]
    for attempt in range(2):
        result = await browser.send_connection_request(name, note_trimmed, linkedin_url)
        if result["status"] in ("sent", "limit_reached"):
            return result
        if attempt == 0:
            await asyncio.sleep(random.uniform(3, 7))
    return result


async def close_browser():
    """Gracefully close the browser and clear the singleton."""
    global _browser
    async with _lock:
        if _browser and _browser._started:
            await _browser.close()
        _browser = None


def get_session_stats() -> dict:
    """Return current session stats without starting the browser."""
    if _browser is None:
        return {
            "is_logged_in": False,
            "messages_sent": 0,
            "messages_limit": 25,
            "requests_sent": 0,
            "requests_limit": 25,
            "browser_running": False,
        }
    return _browser.get_session_stats()
