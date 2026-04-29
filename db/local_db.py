"""
Local SQLite database for pipeline state management.
Tracks campaigns, leads, and job logs.
Uses aiosqlite for non-blocking async I/O inside FastAPI.
"""
import aiosqlite
import json
from datetime import datetime, date
from pathlib import Path
from typing import Optional, List

DB_PATH = str(Path(__file__).parent.parent / "data" / "pipeline.db")


class LocalDB:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    async def init_db(self):
        """Create all tables if they don't exist."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript("""
                CREATE TABLE IF NOT EXISTS campaigns (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    name         TEXT NOT NULL,
                    mode         TEXT DEFAULT 'all',
                    daily_limit  INTEGER DEFAULT 25,
                    status       TEXT DEFAULT 'active',
                    created_at   TEXT DEFAULT (datetime('now')),
                    total_sent   INTEGER DEFAULT 0,
                    total_failed INTEGER DEFAULT 0,
                    last_run_at  TEXT
                );

                CREATE TABLE IF NOT EXISTS leads (
                    id                INTEGER PRIMARY KEY AUTOINCREMENT,
                    campaign_id       INTEGER REFERENCES campaigns(id) ON DELETE CASCADE,
                    name              TEXT NOT NULL,
                    linkedin_url      TEXT,
                    title             TEXT,
                    company           TEXT,
                    industry          TEXT,
                    status            TEXT DEFAULT 'pending',
                    message_type      TEXT DEFAULT 'dm',
                    generated_message TEXT,
                    person_id         INTEGER,
                    suggestion_id     INTEGER,
                    last_contacted    TEXT,
                    created_at        TEXT DEFAULT (datetime('now')),
                    error_msg         TEXT
                );

                CREATE TABLE IF NOT EXISTS job_logs (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id      TEXT UNIQUE NOT NULL,
                    campaign_id INTEGER,
                    status      TEXT DEFAULT 'queued',
                    phase       TEXT DEFAULT 'idle',
                    total       INTEGER DEFAULT 0,
                    completed   INTEGER DEFAULT 0,
                    sent        INTEGER DEFAULT 0,
                    failed      INTEGER DEFAULT 0,
                    log_entries TEXT DEFAULT '[]',
                    started_at  TEXT,
                    finished_at TEXT,
                    error       TEXT,
                    created_at  TEXT DEFAULT (datetime('now'))
                );

                CREATE INDEX IF NOT EXISTS idx_leads_campaign ON leads(campaign_id);
                CREATE INDEX IF NOT EXISTS idx_leads_status   ON leads(status);
                CREATE INDEX IF NOT EXISTS idx_jobs_campaign  ON job_logs(campaign_id);
            """)
            await db.commit()

    # ── Campaigns ─────────────────────────────────────────────────────────────

    async def create_campaign(self, name: str, mode: str = "all", daily_limit: int = 25) -> dict:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                "INSERT INTO campaigns (name, mode, daily_limit) VALUES (?,?,?)",
                (name, mode, daily_limit),
            )
            await db.commit()
            row = await (await db.execute(
                "SELECT * FROM campaigns WHERE id=?", (cur.lastrowid,)
            )).fetchone()
            return dict(row)

    async def get_campaigns(self) -> List[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            rows = await (await db.execute(
                "SELECT * FROM campaigns ORDER BY created_at DESC"
            )).fetchall()
            return [dict(r) for r in rows]

    async def get_campaign(self, campaign_id: int) -> Optional[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            row = await (await db.execute(
                "SELECT * FROM campaigns WHERE id=?", (campaign_id,)
            )).fetchone()
            return dict(row) if row else None

    async def update_campaign(self, campaign_id: int, **kwargs) -> bool:
        if not kwargs:
            return False
        cols = ", ".join(f"{k}=?" for k in kwargs)
        vals = list(kwargs.values()) + [campaign_id]
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(f"UPDATE campaigns SET {cols} WHERE id=?", vals)
            await db.commit()
        return True

    async def delete_campaign(self, campaign_id: int) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM campaigns WHERE id=?", (campaign_id,))
            await db.commit()
        return True

    # ── Leads ─────────────────────────────────────────────────────────────────

    async def bulk_add_leads(self, campaign_id: int, leads: List[dict]) -> int:
        """Add multiple leads, skip duplicates. Returns count added."""
        added = 0
        async with aiosqlite.connect(self.db_path) as db:
            for lead in leads:
                url = lead.get("linkedin_url")
                if url:
                    dup = await (await db.execute(
                        "SELECT id FROM leads WHERE campaign_id=? AND linkedin_url=?",
                        (campaign_id, url),
                    )).fetchone()
                else:
                    dup = await (await db.execute(
                        "SELECT id FROM leads WHERE campaign_id=? AND name=? AND company=?",
                        (campaign_id, lead.get("name"), lead.get("company")),
                    )).fetchone()

                if not dup:
                    await db.execute(
                        """INSERT INTO leads
                           (campaign_id, name, linkedin_url, title, company, industry, person_id, message_type)
                           VALUES (?,?,?,?,?,?,?,?)""",
                        (
                            campaign_id,
                            lead.get("name"),
                            lead.get("linkedin_url"),
                            lead.get("title"),
                            lead.get("company"),
                            lead.get("industry"),
                            lead.get("person_id"),
                            lead.get("message_type", "dm"),
                        ),
                    )
                    added += 1
            await db.commit()
        return added

    async def get_pending_leads(self, campaign_id: int, limit: int = 25) -> List[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            rows = await (await db.execute(
                "SELECT * FROM leads WHERE campaign_id=? AND status='pending' ORDER BY id LIMIT ?",
                (campaign_id, limit),
            )).fetchall()
            return [dict(r) for r in rows]

    async def get_leads_by_campaign(self, campaign_id: int) -> List[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            rows = await (await db.execute(
                "SELECT * FROM leads WHERE campaign_id=? ORDER BY created_at DESC",
                (campaign_id,),
            )).fetchall()
            return [dict(r) for r in rows]

    async def update_lead_status(
        self,
        lead_id: int,
        status: str,
        message: str = None,
        suggestion_id: int = None,
        error_msg: str = None,
    ) -> bool:
        contacted = datetime.utcnow().isoformat() if status == "sent" else None
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """UPDATE leads SET status=?, generated_message=?, suggestion_id=?,
                   error_msg=?, last_contacted=? WHERE id=?""",
                (status, message, suggestion_id, error_msg, contacted, lead_id),
            )
            await db.commit()
        return True

    async def get_today_sent_count(self, campaign_id: int) -> int:
        today = date.today().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            row = await (await db.execute(
                "SELECT COUNT(*) FROM leads WHERE campaign_id=? AND status='sent' AND last_contacted LIKE ?",
                (campaign_id, f"{today}%"),
            )).fetchone()
            return row[0] if row else 0

    # ── Job Logs ──────────────────────────────────────────────────────────────

    async def create_job(self, job_id: str, campaign_id: int) -> dict:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            await db.execute(
                "INSERT INTO job_logs (job_id, campaign_id, status, started_at) VALUES (?,?,?,?)",
                (job_id, campaign_id, "running", datetime.utcnow().isoformat()),
            )
            await db.commit()
            row = await (await db.execute(
                "SELECT * FROM job_logs WHERE job_id=?", (job_id,)
            )).fetchone()
            return dict(row)

    async def update_job(self, job_id: str, **kwargs) -> bool:
        if not kwargs:
            return False
        cols = ", ".join(f"{k}=?" for k in kwargs)
        vals = list(kwargs.values()) + [job_id]
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(f"UPDATE job_logs SET {cols} WHERE job_id=?", vals)
            await db.commit()
        return True

    async def append_job_log(self, job_id: str, message: str) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            row = await (await db.execute(
                "SELECT log_entries FROM job_logs WHERE job_id=?", (job_id,)
            )).fetchone()
            if row:
                entries = json.loads(row[0] or "[]")
                ts = datetime.utcnow().strftime("%H:%M:%S")
                entries.append(f"[{ts}] {message}")
                if len(entries) > 200:
                    entries = entries[-200:]
                await db.execute(
                    "UPDATE job_logs SET log_entries=? WHERE job_id=?",
                    (json.dumps(entries), job_id),
                )
                await db.commit()

    async def get_job(self, job_id: str) -> Optional[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            row = await (await db.execute(
                "SELECT * FROM job_logs WHERE job_id=?", (job_id,)
            )).fetchone()
            if not row:
                return None
            d = dict(row)
            d["log_entries"] = json.loads(d.get("log_entries") or "[]")
            return d

    async def get_recent_jobs(self, limit: int = 20) -> List[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            rows = await (await db.execute(
                "SELECT * FROM job_logs ORDER BY created_at DESC LIMIT ?", (limit,)
            )).fetchall()
            result = []
            for r in rows:
                d = dict(r)
                entries = json.loads(d.get("log_entries") or "[]")
                d["log_entries"] = entries[-10:]  # last 10 for list view
                result.append(d)
            return result

    async def get_active_job(self, campaign_id: int) -> Optional[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            row = await (await db.execute(
                """SELECT * FROM job_logs WHERE campaign_id=? AND status='running'
                   ORDER BY created_at DESC LIMIT 1""",
                (campaign_id,),
            )).fetchone()
            if not row:
                return None
            d = dict(row)
            d["log_entries"] = json.loads(d.get("log_entries") or "[]")
            return d

    # ── Analytics ─────────────────────────────────────────────────────────────

    async def get_analytics(self) -> dict:
        async with aiosqlite.connect(self.db_path) as db:
            total_leads = (await (await db.execute("SELECT COUNT(*) FROM leads")).fetchone())[0]
            sent = (await (await db.execute("SELECT COUNT(*) FROM leads WHERE status='sent'")).fetchone())[0]
            failed = (await (await db.execute("SELECT COUNT(*) FROM leads WHERE status='failed'")).fetchone())[0]
            pending = (await (await db.execute("SELECT COUNT(*) FROM leads WHERE status='pending'")).fetchone())[0]
            campaigns = (await (await db.execute("SELECT COUNT(*) FROM campaigns")).fetchone())[0]
            active_cmp = (await (await db.execute(
                "SELECT COUNT(*) FROM campaigns WHERE status='active'"
            )).fetchone())[0]

            # Daily breakdown (last 7 days)
            daily = await (await db.execute(
                """SELECT DATE(last_contacted) as day, COUNT(*) as cnt
                   FROM leads WHERE status='sent' AND last_contacted IS NOT NULL
                   GROUP BY day ORDER BY day DESC LIMIT 7"""
            )).fetchall()

            # Per-campaign stats
            cmp_stats = await (await db.execute(
                """SELECT c.name, c.mode, c.daily_limit, c.status,
                          COUNT(l.id) as total_leads,
                          SUM(CASE WHEN l.status='sent'    THEN 1 ELSE 0 END) as sent,
                          SUM(CASE WHEN l.status='failed'  THEN 1 ELSE 0 END) as failed,
                          SUM(CASE WHEN l.status='pending' THEN 1 ELSE 0 END) as pending
                   FROM campaigns c LEFT JOIN leads l ON l.campaign_id=c.id
                   GROUP BY c.id ORDER BY c.created_at DESC"""
            )).fetchall()

            return {
                "totals": {
                    "leads": total_leads,
                    "sent": sent,
                    "failed": failed,
                    "pending": pending,
                    "campaigns": campaigns,
                    "active_campaigns": active_cmp,
                    "success_rate": round(sent / total_leads * 100, 1) if total_leads else 0,
                },
                "daily": [{"day": r[0], "sent": r[1]} for r in daily],
                "campaigns": [
                    {
                        "name": r[0], "mode": r[1], "daily_limit": r[2],
                        "status": r[3], "total_leads": r[4] or 0,
                        "sent": r[5] or 0, "failed": r[6] or 0, "pending": r[7] or 0,
                    }
                    for r in cmp_stats
                ],
            }
