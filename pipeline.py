"""
Pipeline Controller
Central automation engine.

Flow:
  trigger_campaign()
      → enforce daily limits
      → fetch pending leads
      → generate AI messages (concurrent)
      → login to LinkedIn
      → send each lead (DM or connection request) with human delays
      → update lead + job status after each action
      → update campaign totals
"""
import asyncio
import random
import uuid
from datetime import datetime
from typing import Optional

from db.local_db import LocalDB
from services import message_gen, browser_service

# Human-like delay range between LinkedIn actions (seconds)
MIN_DELAY = 20
MAX_DELAY = 60


class Pipeline:
    def __init__(self, db: LocalDB):
        self.db = db
        # Active asyncio Tasks keyed by job_id
        self._tasks: dict[str, asyncio.Task] = {}

    # ── Public API ────────────────────────────────────────────────────────────

    async def trigger_campaign(
        self,
        campaign_id: int,
        email: str = None,
        password: str = None,
        headless: bool = False,
    ) -> str:
        """
        Enqueue and start a campaign run as a background asyncio Task.
        Returns job_id.  Raises if campaign doesn't exist or is paused.
        """
        campaign = await self.db.get_campaign(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")
        if campaign["status"] == "paused":
            raise ValueError("Campaign is paused — resume it first")

        # Only one active job per campaign
        active = await self.db.get_active_job(campaign_id)
        if active:
            raise ValueError(f"Campaign already has a running job: {active['job_id']}")

        job_id = str(uuid.uuid4())
        await self.db.create_job(job_id, campaign_id)

        task = asyncio.create_task(
            self._run(campaign_id, job_id, email, password, headless),
            name=f"pipeline-{job_id}",
        )
        self._tasks[job_id] = task
        task.add_done_callback(lambda t: self._tasks.pop(job_id, None))
        return job_id

    async def cancel_job(self, job_id: str) -> bool:
        task = self._tasks.get(job_id)
        if task and not task.done():
            task.cancel()
            await self.db.update_job(
                job_id,
                status="stopped",
                phase="stopped",
                finished_at=datetime.utcnow().isoformat(),
            )
            return True
        return False

    def get_active_jobs(self) -> list:
        return [jid for jid, t in self._tasks.items() if not t.done()]

    # ── Internal pipeline ─────────────────────────────────────────────────────

    async def _run(
        self,
        campaign_id: int,
        job_id: str,
        email: str,
        password: str,
        headless: bool,
    ):
        """Full pipeline execution for one campaign run."""
        log = lambda msg: asyncio.create_task(
            self.db.append_job_log(job_id, msg)
        )

        async def update(**kw):
            await self.db.update_job(job_id, **kw)

        try:
            campaign = await self.db.get_campaign(campaign_id)
            daily_limit = campaign["daily_limit"]
            mode = campaign["mode"]

            await update(phase="checking_limits")
            log(f"🚀 Campaign '{campaign['name']}' started — mode={mode}, limit={daily_limit}/day")

            # ── 1. Enforce daily limit ────────────────────────────────────────
            today_sent = await self.db.get_today_sent_count(campaign_id)
            remaining = daily_limit - today_sent
            if remaining <= 0:
                await update(
                    status="completed",
                    phase="done",
                    finished_at=datetime.utcnow().isoformat(),
                )
                log(f"⚠️  Daily limit already reached ({today_sent}/{daily_limit}) — skipping")
                return

            log(f"📊 Daily budget: {today_sent} sent today, {remaining} remaining")

            # ── 2. Fetch pending leads ────────────────────────────────────────
            await update(phase="fetching_leads")
            leads = await self.db.get_pending_leads(campaign_id, limit=remaining)
            if not leads:
                await update(
                    status="completed",
                    phase="done",
                    finished_at=datetime.utcnow().isoformat(),
                )
                log("ℹ️  No pending leads — import more leads to this campaign")
                return

            # Filter by mode
            if mode == "texts":
                leads = [l for l in leads if l.get("message_type") != "request"]
            elif mode == "requests":
                leads = [l for l in leads if l.get("message_type") == "request"]

            await update(total=len(leads), phase="generating")
            log(f"👥 Found {len(leads)} pending leads to process")

            # ── 3. Generate AI messages concurrently ─────────────────────────
            log("🧠 Generating AI messages...")
            for lead in leads:
                await self.db.update_lead_status(lead["id"], "generating")

            enriched_leads = await message_gen.generate_batch(leads)
            log(f"✅ Generated {len(enriched_leads)} messages")

            # ── 4. Login to LinkedIn ──────────────────────────────────────────
            await update(phase="logging_in")
            log("🌐 Connecting to LinkedIn...")
            logged_in = await browser_service.ensure_logged_in(email, password, headless)
            if not logged_in:
                raise RuntimeError("Could not log in to LinkedIn — check credentials or log in manually")
            log("✅ LinkedIn session active")

            # ── 5. Send messages ──────────────────────────────────────────────
            await update(phase="sending")
            sent = 0
            failed = 0

            for i, lead in enumerate(enriched_leads):
                # Re-check daily limit mid-run
                today_sent = await self.db.get_today_sent_count(campaign_id)
                if today_sent >= daily_limit:
                    log(f"⚠️  Daily limit hit mid-run ({today_sent}/{daily_limit}) — stopping")
                    break

                name = lead.get("name", "")
                message = lead.get("generated_message", "")
                url = lead.get("linkedin_url")
                msg_type = lead.get("message_type", "dm")
                lead_id = lead["id"]

                log(f"[{i+1}/{len(enriched_leads)}] {'📨' if msg_type=='dm' else '🤝'} {msg_type.upper()} → {name}")

                # Send
                if msg_type == "request":
                    result = await browser_service.send_connection_request(name, message, url)
                else:
                    result = await browser_service.send_dm(name, message, url)

                status = result.get("status")

                if status == "sent":
                    sent += 1
                    await self.db.update_lead_status(lead_id, "sent", message=message)
                    log(f"   ✅ Sent to {name}")
                elif status == "limit_reached":
                    await self.db.update_lead_status(lead_id, "pending")
                    log(f"   ⚠️  LinkedIn session limit reached — stopping")
                    break
                else:
                    failed += 1
                    err = result.get("message", "Unknown error")
                    await self.db.update_lead_status(lead_id, "failed", error_msg=err)
                    log(f"   ❌ Failed: {err}")

                await update(completed=i + 1, sent=sent, failed=failed)

                # Human-like delay (skip after last item)
                if i < len(enriched_leads) - 1:
                    delay = random.randint(MIN_DELAY, MAX_DELAY)
                    log(f"   ⏳ Waiting {delay}s before next action...")
                    await asyncio.sleep(delay)

            # ── 6. Finalise ───────────────────────────────────────────────────
            await self.db.update_campaign(
                campaign_id,
                total_sent=campaign["total_sent"] + sent,
                total_failed=campaign["total_failed"] + failed,
                last_run_at=datetime.utcnow().isoformat(),
            )
            await update(
                status="completed",
                phase="done",
                sent=sent,
                failed=failed,
                finished_at=datetime.utcnow().isoformat(),
            )
            log(f"🏁 Run complete — {sent} sent, {failed} failed")

        except asyncio.CancelledError:
            await self.db.update_job(
                job_id,
                status="stopped",
                phase="stopped",
                finished_at=datetime.utcnow().isoformat(),
            )

        except Exception as exc:
            err = str(exc)
            await self.db.update_job(
                job_id,
                status="failed",
                phase="error",
                error=err,
                finished_at=datetime.utcnow().isoformat(),
            )
            await self.db.append_job_log(job_id, f"❌ Fatal error: {err}")
            print(f"[Pipeline] Job {job_id} failed: {exc}")
