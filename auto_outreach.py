"""
Auto Outreach Engine
Full pipeline: Generate AI messages → Send directly to LinkedIn DMs
Runs both connection texts and connection requests end-to-end.

Usage (CLI):
    python auto_outreach.py --mode all --count 5

Usage (from app.py):
    engine = AutoOutreachEngine()
    await engine.run(mode="all", count=25)
"""
import asyncio
import json
import os
from datetime import datetime

from agent import LinkedInAgent
from linkedin_browser import LinkedInBrowser


class AutoOutreachEngine:
    """
    Generates AI-crafted messages and sends them directly to LinkedIn.
    Tracks progress in real-time via self.status dict.
    """

    def __init__(self):
        self.agent = LinkedInAgent()
        self.browser = LinkedInBrowser()

        # Real-time status (polled by the frontend)
        self.status = {
            "running": False,
            "phase": "idle",           # idle | generating | sending | done | error
            "mode": None,              # "texts" | "requests" | "all"

            # Generation progress
            "gen_total": 0,
            "gen_completed": 0,
            "gen_texts": [],
            "gen_requests": [],

            # Sending progress
            "send_total": 0,
            "send_completed": 0,
            "send_sent": 0,
            "send_failed": 0,
            "send_results": [],

            # Metadata
            "started_at": None,
            "finished_at": None,
            "error": None,
            "log": [],
        }

    def _log(self, msg):
        ts = datetime.utcnow().strftime("%H:%M:%S")
        entry = f"[{ts}] {msg}"
        self.status["log"].append(entry)
        print(entry)

    def _reset(self, mode):
        self.status.update({
            "running": True,
            "phase": "generating",
            "mode": mode,
            "gen_total": 0,
            "gen_completed": 0,
            "gen_texts": [],
            "gen_requests": [],
            "send_total": 0,
            "send_completed": 0,
            "send_sent": 0,
            "send_failed": 0,
            "send_results": [],
            "started_at": datetime.utcnow().isoformat(),
            "finished_at": None,
            "error": None,
            "log": [],
        })

    # ─────────────────────────────────────────────
    # Main pipeline
    # ─────────────────────────────────────────────

    async def run(self, mode="all", count=25, headless=False, email=None, password=None):
        """
        Run the full pipeline.

        Args:
            mode: "texts" (DMs to connections), "requests" (connection requests), or "all" (both)
            count: Number of messages/requests to generate per type
            headless: Run browser in headless mode (not recommended)
            email/password: LinkedIn creds (only needed if not already logged in)
        """
        self._reset(mode)
        self._log(f"🚀 Auto-outreach started — mode={mode}, count={count}")

        try:
            # ── Phase 1: Generate AI messages ──
            self.status["phase"] = "generating"
            await self._generate(mode, count)

            # ── Phase 2: Launch browser & login ──
            self.status["phase"] = "logging_in"
            self._log("🌐 Starting LinkedIn browser...")
            logged_in = await self.browser.start(headless=headless)

            if not logged_in:
                if email and password:
                    self._log("🔑 Logging into LinkedIn...")
                    logged_in = await self.browser.login(email, password)
                else:
                    self._log("⚠️  Not logged in. Opening browser — please log in manually in the browser window.")
                    # Wait up to 3 minutes for manual login
                    for i in range(36):
                        await asyncio.sleep(5)
                        if await self.browser._check_login():
                            logged_in = True
                            break
                        if i % 6 == 0:
                            self._log(f"   Waiting for manual login... ({i*5}s)")

            if not logged_in:
                raise RuntimeError("Could not log in to LinkedIn. Aborting.")

            self._log("✅ LinkedIn login confirmed")

            # ── Phase 3: Send everything ──
            self.status["phase"] = "sending"

            # Send connection texts (DMs)
            if mode in ("texts", "all") and self.status["gen_texts"]:
                await self._send_messages(self.status["gen_texts"])

            # Send connection requests
            if mode in ("requests", "all") and self.status["gen_requests"]:
                await self._send_requests(self.status["gen_requests"])

            # ── Done ──
            self.status["phase"] = "done"
            self.status["finished_at"] = datetime.utcnow().isoformat()
            self._log(f"✅ Auto-outreach complete — {self.status['send_sent']} sent, {self.status['send_failed']} failed")

        except Exception as e:
            self.status["phase"] = "error"
            self.status["error"] = str(e)
            self._log(f"❌ Fatal error: {e}")

        finally:
            self.status["running"] = False

    # ─────────────────────────────────────────────
    # Phase 1: Generate
    # ─────────────────────────────────────────────

    async def _generate(self, mode, count):
        """Generate AI messages (runs LLM calls in a thread pool)."""
        loop = asyncio.get_event_loop()

        if mode in ("texts", "all"):
            self._log(f"🧠 Generating {count} connection texts (DMs)...")
            self.status["gen_total"] += count
            texts = await loop.run_in_executor(
                None, lambda: self.agent.generate_connection_texts(num_suggestions=count)
            )
            self.status["gen_texts"] = texts
            self.status["gen_completed"] += len(texts)
            self._log(f"   ✅ Generated {len(texts)} connection texts")

        if mode in ("requests", "all"):
            self._log(f"🧠 Generating {count} connection requests...")
            self.status["gen_total"] += count
            requests = await loop.run_in_executor(
                None, lambda: self.agent.generate_connection_requests(num_suggestions=count)
            )
            self.status["gen_requests"] = requests
            self.status["gen_completed"] += len(requests)
            self._log(f"   ✅ Generated {len(requests)} connection requests")

        total = len(self.status["gen_texts"]) + len(self.status["gen_requests"])
        self.status["send_total"] = total
        self._log(f"📊 Total to send: {total}")

    # ─────────────────────────────────────────────
    # Phase 3a: Send DMs to existing connections
    # ─────────────────────────────────────────────

    async def _send_messages(self, texts):
        """Send generated DMs to existing connections."""
        self._log(f"📤 Sending {len(texts)} DMs to connections...")

        for i, suggestion in enumerate(texts):
            name = suggestion.get("name", "")
            message = suggestion.get("suggested_message", "")
            person_id = suggestion.get("person_id")
            suggestion_id = suggestion.get("suggestion_id")

            self._log(f"   [{i+1}/{len(texts)}] DMing {name}...")

            result = await self.browser.send_message(
                person_name=name,
                message=message,
                linkedin_url=suggestion.get("linkedin_url"),
            )

            result["name"] = name
            result["type"] = "dm"
            self.status["send_results"].append(result)
            self.status["send_completed"] += 1

            if result["status"] == "sent":
                self.status["send_sent"] += 1
                self._log(f"   ✅ DM sent to {name}")

                # Update DB: mark as contacted + suggestion sent
                if person_id:
                    self.agent.db.update_person_contacted(person_id)
                if suggestion_id:
                    self.agent.db.update_suggestion_status(
                        suggestion_id, "sent", result.get("sent_at")
                    )
            elif result["status"] == "limit_reached":
                self._log(f"   ⚠️  Session limit reached — stopping DMs")
                break
            else:
                self.status["send_failed"] += 1
                self._log(f"   ❌ Failed to DM {name}: {result.get('message', '')}")
                if suggestion_id:
                    self.agent.db.update_suggestion_status(suggestion_id, "failed")

    # ─────────────────────────────────────────────
    # Phase 3b: Send connection requests to prospects
    # ─────────────────────────────────────────────

    async def _send_requests(self, requests):
        """Send connection requests to prospects."""
        self._log(f"📤 Sending {len(requests)} connection requests...")

        for i, suggestion in enumerate(requests):
            name = suggestion.get("name", "")
            note = suggestion.get("suggested_message", "")
            person_id = suggestion.get("person_id")
            suggestion_id = suggestion.get("suggestion_id")

            self._log(f"   [{i+1}/{len(requests)}] Connecting with {name}...")

            result = await self.browser.send_connection_request(
                person_name=name,
                note=note,
                linkedin_url=suggestion.get("linkedin_url"),
            )

            result["name"] = name
            result["type"] = "request"
            self.status["send_results"].append(result)
            self.status["send_completed"] += 1

            if result["status"] == "sent":
                self.status["send_sent"] += 1
                self._log(f"   ✅ Request sent to {name}")

                if person_id:
                    self.agent.db.update_person_contacted(person_id)
                if suggestion_id:
                    self.agent.db.update_suggestion_status(
                        suggestion_id, "sent", result.get("sent_at")
                    )
            elif result["status"] == "limit_reached":
                self._log(f"   ⚠️  Session limit reached — stopping requests")
                break
            else:
                self.status["send_failed"] += 1
                self._log(f"   ❌ Failed to connect with {name}: {result.get('message', '')}")
                if suggestion_id:
                    self.agent.db.update_suggestion_status(suggestion_id, "failed")

    # ─────────────────────────────────────────────
    # Cleanup
    # ─────────────────────────────────────────────

    async def close(self):
        """Close the browser."""
        await self.browser.close()


# ─────────────────────────────────────────────
# CLI Entry Point
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="LinkedIn Auto-Outreach")
    parser.add_argument("--mode", choices=["texts", "requests", "all"], default="all",
                        help="What to send: texts (DMs), requests, or all")
    parser.add_argument("--count", type=int, default=25,
                        help="Number per type (default: 25)")
    parser.add_argument("--headless", action="store_true",
                        help="Run browser in headless mode")
    parser.add_argument("--email", type=str, default=None,
                        help="LinkedIn email (optional if already logged in)")
    parser.add_argument("--password", type=str, default=None,
                        help="LinkedIn password (optional if already logged in)")
    args = parser.parse_args()

    async def main():
        engine = AutoOutreachEngine()
        try:
            await engine.run(
                mode=args.mode,
                count=args.count,
                headless=args.headless,
                email=args.email,
                password=args.password,
            )
        finally:
            await engine.close()

    asyncio.run(main())
