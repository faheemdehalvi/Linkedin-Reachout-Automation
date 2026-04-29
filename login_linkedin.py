import asyncio
from services.browser_service import get_browser

async def main():
    print("Starting LinkedIn browser in visible mode...")
    print("Please log in to your account when the browser opens.")
    print("If there's a captcha or verification, please complete it.")
    
    # Force headless=False to make the browser visible
    browser = await get_browser(headless=False)
    
    if browser.is_logged_in:
        print("\n[OK] You are already logged in to LinkedIn!")
    else:
        print("\n[*] Browser is open. Please log in to LinkedIn now.")
        print("Waiting for login... (Will wait up to 3 minutes)")
        
        # Wait up to 3 minutes for manual login
        for i in range(36):
            await asyncio.sleep(5)
            if await browser._check_login():
                print("\n[OK] Successfully logged in! Session saved.")
                break
            if i % 6 == 0:
                print(f"Still waiting for login... ({i * 5}s elapsed)")
        else:
            print("\n[FAIL] Login timeout. You can run this script again.")

    print("\nClosing browser in 5 seconds. Your session is saved securely.")
    await asyncio.sleep(5)
    await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
