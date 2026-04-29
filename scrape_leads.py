"""
LinkedIn Lead Scraper
Automatically pulls your existing connections AND discovers new prospects
from LinkedIn search, then saves them all into your Supabase database.

Usage:
    python scrape_leads.py --mode connections              # Scrape your existing connections
    python scrape_leads.py --mode prospects --query "SaaS founder"   # Find new prospects
    python scrape_leads.py --mode both --query "Product Manager"     # Do both at once
"""
import asyncio
import argparse
from linkedin_browser import LinkedInBrowser
from supabase_database import SupabaseLinkedInDatabase


async def scrape_and_save(mode="both", query="", max_pages=3):
    browser = LinkedInBrowser()
    db = SupabaseLinkedInDatabase()

    try:
        print("Starting browser...")
        logged_in = await browser.start(headless=False)

        if not logged_in:
            print("Not logged in. Please log in manually in the browser window.")
            print("Waiting up to 3 minutes...")
            for i in range(36):
                await asyncio.sleep(5)
                if await browser._check_login():
                    logged_in = True
                    break
                if i % 6 == 0:
                    print(f"  Still waiting... ({i * 5}s)")
            if not logged_in:
                print("Could not log in. Run login_linkedin.py first.")
                return

        total_saved = 0

        # ── Scrape existing connections ──
        if mode in ("connections", "both"):
            print("\n--- Scraping your existing LinkedIn connections ---")
            connections = await browser.scrape_my_connections(max_pages=max_pages)
            print(f"Found {len(connections)} connections. Saving to database...")

            for person in connections:
                try:
                    profile_id = person["linkedin_url"].split("/in/")[-1].strip("/") if "/in/" in person["linkedin_url"] else person["name"].replace(" ", "-").lower()
                    db.add_person(
                        linkedin_profile_id=profile_id,
                        name=person["name"],
                        title=person["title"],
                        company=person["company"],
                        industry="",
                        personality_traits="",
                        interests="",
                        connection_status="connection",
                        linkedin_url=person["linkedin_url"],
                    )
                    total_saved += 1
                except Exception as e:
                    if "duplicate" not in str(e).lower():
                        print(f"  Skipped {person['name']}: {e}")

        # ── Discover new prospects ──
        if mode in ("prospects", "both"):
            if not query:
                print("Error: You need to provide a search query with --query")
                print('Example: python scrape_leads.py --mode prospects --query "SaaS founder"')
                return

            print(f'\n--- Searching LinkedIn for new prospects: "{query}" ---')
            prospects = await browser.scrape_prospects(keywords=query, max_pages=max_pages)
            print(f"Found {len(prospects)} prospects. Saving to database...")

            for person in prospects:
                try:
                    profile_id = person["linkedin_url"].split("/in/")[-1].strip("/") if "/in/" in person["linkedin_url"] else person["name"].replace(" ", "-").lower()
                    db.add_person(
                        linkedin_profile_id=profile_id,
                        name=person["name"],
                        title=person["title"],
                        company=person["company"],
                        industry="",
                        personality_traits="",
                        interests="",
                        connection_status="prospect",
                        linkedin_url=person["linkedin_url"],
                    )
                    total_saved += 1
                except Exception as e:
                    if "duplicate" not in str(e).lower():
                        print(f"  Skipped {person['name']}: {e}")

        print(f"\n=== Done! Saved {total_saved} new leads to your database. ===")
        print("You can now run:  python auto_outreach.py --mode all")

    finally:
        await browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LinkedIn Lead Scraper")
    parser.add_argument("--mode", choices=["connections", "prospects", "both"], default="both",
                        help="What to scrape: your connections, new prospects, or both")
    parser.add_argument("--query", type=str, default="",
                        help='Search query for finding prospects (e.g. "SaaS founder", "Data Engineer")')
    parser.add_argument("--pages", type=int, default=3,
                        help="Number of pages to scrape (default: 3)")
    args = parser.parse_args()

    asyncio.run(scrape_and_save(mode=args.mode, query=args.query, max_pages=args.pages))
