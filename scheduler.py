"""
Scheduler
Uses APScheduler AsyncIOScheduler to auto-trigger active campaigns every N hours.
Integrates with the Pipeline controller and LocalDB.
"""
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

_scheduler: AsyncIOScheduler = None


def start_scheduler(pipeline, db, interval_hours: int = 6):
    """
    Start the background scheduler.
    Call once at app startup (inside FastAPI lifespan).
    """
    global _scheduler
    if _scheduler and _scheduler.running:
        return

    _scheduler = AsyncIOScheduler()

    async def auto_trigger():
        """Trigger all active campaigns that have pending leads."""
        try:
            campaigns = await db.get_campaigns()
            active = [c for c in campaigns if c["status"] == "active"]
            print(f"[Scheduler] Auto-trigger: {len(active)} active campaign(s)")

            for campaign in active:
                # Skip if there's already a running job
                existing = await db.get_active_job(campaign["id"])
                if existing:
                    print(f"[Scheduler] Campaign '{campaign['name']}' already running — skip")
                    continue

                # Check there are pending leads
                pending = await db.get_pending_leads(campaign["id"], limit=1)
                if not pending:
                    print(f"[Scheduler] Campaign '{campaign['name']}' — no pending leads")
                    continue

                try:
                    job_id = await pipeline.trigger_campaign(campaign["id"])
                    print(f"[Scheduler] Started job {job_id} for campaign '{campaign['name']}'")
                except Exception as e:
                    print(f"[Scheduler] Could not trigger '{campaign['name']}': {e}")

        except Exception as e:
            print(f"[Scheduler] Auto-trigger error: {e}")

    _scheduler.add_job(
        auto_trigger,
        trigger=IntervalTrigger(hours=interval_hours),
        id="auto_trigger",
        replace_existing=True,
        max_instances=1,
    )
    _scheduler.start()
    print(f"[Scheduler] Started — auto-trigger every {interval_hours}h")


def stop_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        print("[Scheduler] Stopped")


def get_status() -> dict:
    if _scheduler is None or not _scheduler.running:
        return {"running": False, "jobs": []}
    jobs = []
    for job in _scheduler.get_jobs():
        next_run = job.next_run_time
        jobs.append({
            "id": job.id,
            "next_run": next_run.isoformat() if next_run else None,
        })
    return {"running": True, "jobs": jobs}
