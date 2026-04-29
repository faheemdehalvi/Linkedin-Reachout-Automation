"""
LinkedIn Automation API
FastAPI backend — all original features + new pipeline system:
1. Connection text recommendations
2. Curated text management
3. Context window viewer
4. Connection request recommendations
5. LinkedIn DM & connection request sending (via Playwright)
6. ── NEW ── Campaign pipeline with scheduling, queueing & analytics
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
import sys
import asyncio

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent import LinkedInAgent
from linkedin_browser import LinkedInBrowser
from auto_outreach import AutoOutreachEngine

# ── NEW pipeline imports ──────────────────────────────────────────────────────
from db.local_db import LocalDB
from pipeline import Pipeline
from scheduler import start_scheduler, stop_scheduler, get_status as scheduler_status
import services.browser_service as browser_svc

# ── App lifespan (startup / shutdown) ────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await local_db.init_db()
    start_scheduler(pipeline, local_db, interval_hours=6)
    yield
    # Shutdown
    stop_scheduler()
    await browser_svc.close_browser()

app = FastAPI(title="Faheem's LinkedIn AI", lifespan=lifespan)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Singletons ────────────────────────────────────────────────────────────────
agent          = LinkedInAgent()
linkedin_browser = LinkedInBrowser()
auto_engine    = AutoOutreachEngine()
local_db       = LocalDB()
pipeline       = Pipeline(local_db)

# Track batch job progress
batch_job = {
    "running": False,
    "type": None,          # "messages" or "requests"
    "total": 0,
    "completed": 0,
    "sent": 0,
    "failed": 0,
    "results": [],
    "error": None,
}

# ─────────────────────────────────────────────
# Request Models
# ─────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str

class CuratedTextCreate(BaseModel):
    title: str
    message_template: str
    target_industry: Optional[str] = ""
    target_role: Optional[str] = ""
    tags: Optional[str] = ""

class CuratedTextUpdate(BaseModel):
    title: Optional[str] = None
    message_template: Optional[str] = None
    target_industry: Optional[str] = None
    target_role: Optional[str] = None
    tags: Optional[str] = None
    is_active: Optional[bool] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class SendMessageRequest(BaseModel):
    person_name: str
    message: str
    linkedin_url: Optional[str] = None
    suggestion_id: Optional[int] = None

class SendBatchRequest(BaseModel):
    suggestions: List[dict]

class AutoOutreachRequest(BaseModel):
    mode: str = "all"       # "texts", "requests", or "all"
    count: int = 25          # messages per type
    email: Optional[str] = None
    password: Optional[str] = None
    headless: bool = False

# ─────────────────────────────────────────────
# Feature #1: Connection Text Recommendations
# ─────────────────────────────────────────────

@app.get("/api/connection-texts")
async def get_connection_texts():
    """Generate 25 personalized texts for existing connections"""
    try:
        suggestions = agent.generate_connection_texts(num_suggestions=25)
        return {
            "status": "success",
            "feature": "connection_texts",
            "total": len(suggestions),
            "suggestions": suggestions
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

# ─────────────────────────────────────────────
# Feature #2: Curated Text Management
# ─────────────────────────────────────────────

@app.get("/api/curated-texts")
async def get_curated_texts():
    """Get all curated text templates"""
    try:
        texts = agent.db.get_curated_texts(active_only=True)
        return {
            "status": "success",
            "feature": "curated_texts",
            "total": len(texts),
            "texts": texts
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

@app.get("/api/curated-texts/matched")
async def get_curated_matched():
    """Get curated texts matched to people"""
    try:
        result = agent.get_curated_suggestions(num_suggestions=25)
        return {"status": "success", **result}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

@app.post("/api/curated-texts")
async def create_curated_text(text: CuratedTextCreate):
    """Add a new curated text template"""
    try:
        result = agent.db.add_curated_text(
            title=text.title,
            message_template=text.message_template,
            target_industry=text.target_industry,
            target_role=text.target_role,
            tags=text.tags
        )
        if result:
            return {"status": "success", "text": result}
        return JSONResponse(status_code=400, content={"status": "error", "message": "Failed to create"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

@app.put("/api/curated-texts/{text_id}")
async def update_curated_text(text_id: int, text: CuratedTextUpdate):
    """Update an existing curated text template"""
    try:
        updates = {k: v for k, v in text.dict().items() if v is not None}
        result = agent.db.update_curated_text(text_id, updates)
        if result:
            return {"status": "success", "text": result}
        return JSONResponse(status_code=404, content={"status": "error", "message": "Not found"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

@app.delete("/api/curated-texts/{text_id}")
async def delete_curated_text(text_id: int):
    """Soft-delete a curated text template"""
    try:
        success = agent.db.delete_curated_text(text_id)
        if success:
            return {"status": "success", "message": f"Curated text #{text_id} deactivated"}
        return JSONResponse(status_code=404, content={"status": "error", "message": "Not found"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

# ─────────────────────────────────────────────
# Feature #3: Context Window
# ─────────────────────────────────────────────

@app.get("/api/context-window/{person_id}")
async def get_context_window(person_id: int):
    """Get the full AI reasoning context for a person"""
    try:
        context = agent.db.get_context_window(person_id)
        person = agent.db.get_person_by_id(person_id)
        if context:
            return {
                "status": "success",
                "person": person,
                "context_window": context
            }
        return JSONResponse(status_code=404, content={
            "status": "not_found",
            "message": "No context window found. Generate suggestions first.",
            "person": person
        })
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

@app.get("/api/context-window/suggestion/{suggestion_id}")
async def get_context_by_suggestion(suggestion_id: int):
    """Get context window for a specific suggestion"""
    try:
        context = agent.db.get_context_window_by_suggestion(suggestion_id)
        if context:
            return {"status": "success", "context_window": context}
        return JSONResponse(status_code=404, content={"status": "not_found", "message": "No context window for this suggestion"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

@app.get("/api/context-windows/today")
async def get_todays_context_windows():
    """Get all context windows generated today"""
    try:
        windows = agent.db.get_todays_context_windows()
        return {
            "status": "success",
            "total": len(windows),
            "context_windows": windows
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

# ─────────────────────────────────────────────
# Feature #4: Connection Request Recommendations
# ─────────────────────────────────────────────

@app.get("/api/connection-requests")
async def get_connection_requests():
    """Generate 25 personalized connection request notes for prospects"""
    try:
        suggestions = agent.generate_connection_requests(num_suggestions=25)
        return {
            "status": "success",
            "feature": "connection_requests",
            "total": len(suggestions),
            "suggestions": suggestions
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

# ─────────────────────────────────────────────
# Feature #5: LinkedIn Browser Automation
# ─────────────────────────────────────────────

@app.post("/api/linkedin/login")
async def linkedin_login(req: LoginRequest):
    """Login to LinkedIn (opens browser, saves session for future use)"""
    try:
        # Start browser (non-headless so user can handle captcha)
        already_logged_in = await linkedin_browser.start(headless=False)
        if already_logged_in:
            return {"status": "success", "message": "Already logged in", "logged_in": True}

        success = await linkedin_browser.login(req.email, req.password)
        return {
            "status": "success" if success else "error",
            "message": "Logged in" if success else "Login failed — check browser window",
            "logged_in": success,
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

@app.get("/api/linkedin/status")
async def linkedin_status():
    """Check LinkedIn login status and session stats"""
    stats = linkedin_browser.get_session_stats()
    stats["batch_job"] = {
        "running": batch_job["running"],
        "type": batch_job["type"],
        "total": batch_job["total"],
        "completed": batch_job["completed"],
        "sent": batch_job["sent"],
        "failed": batch_job["failed"],
    }
    return stats

@app.post("/api/linkedin/logout")
async def linkedin_logout():
    """Close browser session"""
    try:
        await linkedin_browser.close()
        return {"status": "success", "message": "Browser closed"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

@app.post("/api/linkedin/send-message")
async def send_single_message(req: SendMessageRequest):
    """Send a single DM to a LinkedIn connection"""
    if not linkedin_browser.is_logged_in:
        return JSONResponse(status_code=400, content={"status": "error", "message": "Not logged in. Login first."})

    result = await linkedin_browser.send_message(req.person_name, req.message, req.linkedin_url)

    # Update suggestion status in DB if suggestion_id provided
    if req.suggestion_id and result["status"] == "sent":
        agent.db.update_suggestion_status(req.suggestion_id, "sent", result.get("sent_at"))

    return result

@app.post("/api/linkedin/send-batch-messages")
async def send_batch_messages(req: SendBatchRequest, background_tasks: BackgroundTasks):
    """Send all generated connection texts as DMs (runs in background)"""
    if not linkedin_browser.is_logged_in:
        return JSONResponse(status_code=400, content={"status": "error", "message": "Not logged in. Login first."})

    if batch_job["running"]:
        return JSONResponse(status_code=409, content={"status": "error", "message": "A batch job is already running"})

    # Reset job state
    batch_job.update({
        "running": True,
        "type": "messages",
        "total": len(req.suggestions),
        "completed": 0,
        "sent": 0,
        "failed": 0,
        "results": [],
        "error": None,
    })

    background_tasks.add_task(_run_batch_messages, req.suggestions)
    return {"status": "started", "total": len(req.suggestions), "message": "Batch sending started"}

async def _run_batch_messages(suggestions):
    """Background task: send DMs one by one."""
    try:
        for i, s in enumerate(suggestions):
            name = s.get("name", "")
            message = s.get("suggested_message", "")
            url = s.get("linkedin_url")
            suggestion_id = s.get("suggestion_id")

            result = await linkedin_browser.send_message(name, message, url)
            result["index"] = i

            batch_job["completed"] = i + 1
            if result["status"] == "sent":
                batch_job["sent"] += 1
                if suggestion_id:
                    agent.db.update_suggestion_status(suggestion_id, "sent", result.get("sent_at"))
            else:
                batch_job["failed"] += 1
                if suggestion_id:
                    agent.db.update_suggestion_status(suggestion_id, "failed")

            batch_job["results"].append(result)

            if result.get("status") == "limit_reached":
                break
    except Exception as e:
        batch_job["error"] = str(e)
    finally:
        batch_job["running"] = False

@app.post("/api/linkedin/send-connection-request")
async def send_single_request(req: SendMessageRequest):
    """Send a single connection request"""
    if not linkedin_browser.is_logged_in:
        return JSONResponse(status_code=400, content={"status": "error", "message": "Not logged in. Login first."})

    result = await linkedin_browser.send_connection_request(req.person_name, req.message, req.linkedin_url)

    if req.suggestion_id and result["status"] == "sent":
        agent.db.update_suggestion_status(req.suggestion_id, "sent", result.get("sent_at"))

    return result

@app.post("/api/linkedin/send-batch-requests")
async def send_batch_requests(req: SendBatchRequest, background_tasks: BackgroundTasks):
    """Send all generated connection requests (runs in background)"""
    if not linkedin_browser.is_logged_in:
        return JSONResponse(status_code=400, content={"status": "error", "message": "Not logged in. Login first."})

    if batch_job["running"]:
        return JSONResponse(status_code=409, content={"status": "error", "message": "A batch job is already running"})

    batch_job.update({
        "running": True,
        "type": "requests",
        "total": len(req.suggestions),
        "completed": 0,
        "sent": 0,
        "failed": 0,
        "results": [],
        "error": None,
    })

    background_tasks.add_task(_run_batch_requests, req.suggestions)
    return {"status": "started", "total": len(req.suggestions), "message": "Batch requests started"}

async def _run_batch_requests(suggestions):
    """Background task: send connection requests one by one."""
    try:
        for i, s in enumerate(suggestions):
            name = s.get("name", "")
            note = s.get("suggested_message", "")
            url = s.get("linkedin_url")
            suggestion_id = s.get("suggestion_id")

            result = await linkedin_browser.send_connection_request(name, note, url)
            result["index"] = i

            batch_job["completed"] = i + 1
            if result["status"] == "sent":
                batch_job["sent"] += 1
                if suggestion_id:
                    agent.db.update_suggestion_status(suggestion_id, "sent", result.get("sent_at"))
            else:
                batch_job["failed"] += 1
                if suggestion_id:
                    agent.db.update_suggestion_status(suggestion_id, "failed")

            batch_job["results"].append(result)

            if result.get("status") == "limit_reached":
                break
    except Exception as e:
        batch_job["error"] = str(e)
    finally:
        batch_job["running"] = False

@app.get("/api/linkedin/batch-progress")
async def batch_progress():
    """Poll batch job progress"""
    return {
        "running": batch_job["running"],
        "type": batch_job["type"],
        "total": batch_job["total"],
        "completed": batch_job["completed"],
        "sent": batch_job["sent"],
        "failed": batch_job["failed"],
        "error": batch_job["error"],
        "results": batch_job["results"][-5:] if batch_job["results"] else [],
    }

# ─────────────────────────────────────────────
# Feature #6: Auto-Outreach (Generate → Send)
# ─────────────────────────────────────────────

@app.post("/api/auto-outreach/start")
async def auto_outreach_start(req: AutoOutreachRequest, background_tasks: BackgroundTasks):
    """Launch the full pipeline: Generate AI messages → Send to LinkedIn DMs"""
    if auto_engine.status["running"]:
        return JSONResponse(status_code=409, content={
            "status": "error",
            "message": "Auto-outreach is already running"
        })

    background_tasks.add_task(
        auto_engine.run,
        mode=req.mode,
        count=req.count,
        headless=req.headless,
        email=req.email,
        password=req.password,
    )
    return {"status": "started", "mode": req.mode, "count": req.count}

@app.get("/api/auto-outreach/status")
async def auto_outreach_status():
    """Poll auto-outreach progress in real-time"""
    s = auto_engine.status
    return {
        "running": s["running"],
        "phase": s["phase"],
        "mode": s["mode"],
        "gen_total": s["gen_total"],
        "gen_completed": s["gen_completed"],
        "gen_texts_count": len(s["gen_texts"]),
        "gen_requests_count": len(s["gen_requests"]),
        "send_total": s["send_total"],
        "send_completed": s["send_completed"],
        "send_sent": s["send_sent"],
        "send_failed": s["send_failed"],
        "send_results": s["send_results"][-5:],
        "started_at": s["started_at"],
        "finished_at": s["finished_at"],
        "error": s["error"],
        "log": s["log"][-15:],
    }

@app.post("/api/auto-outreach/stop")
async def auto_outreach_stop():
    """Stop auto-outreach and close browser"""
    try:
        auto_engine.status["running"] = False
        auto_engine.status["phase"] = "stopped"
        await auto_engine.close()
        return {"status": "stopped", "message": "Auto-outreach stopped"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

# ─────────────────────────────────────────────
# Legacy Chat Interface
# ─────────────────────────────────────────────

@app.get("/api/suggestions")
async def get_suggestions():
    try:
        suggestions = agent.generate_daily_suggestions(num_suggestions=5)
        return {"status": "success", "suggestions": suggestions}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

@app.post("/api/chat")
async def chat(request: ChatRequest):
    message = request.message.lower()
    
    # Route: 25 Connections to Text
    if "25 connections" in message or "25 recommendations to texts" in message:
        suggestions = agent.generate_connection_texts(num_suggestions=25)
        
        if not suggestions:
            return {"response": "I couldn't find any connections in your database. Make sure your database has people with connection_status='connection'!"}
            
        response_text = "Here are 25 highly personalized texts for your current connections:\n\n"
        for s in suggestions:
            response_text += f"**{s['name']}** ({s['title']} at {s['company']})\n"
            response_text += f"<details><summary>Context Window (Reasoning & Web Data)</summary>\n\n> {s['reasoning']}\n\n> **Live Web Context:**\n> {s['web_context']}\n</details>\n\n"
            response_text += f"> {s['suggested_message'].replace(chr(10), chr(10) + '> ')}\n\n---\n\n"
            
        return {"response": response_text}

    # Route: 25 Connection Requests
    elif "25 connection requests" in message or "send connection request to" in message:
        suggestions = agent.generate_connection_requests(num_suggestions=25)
        
        if not suggestions:
            return {"response": "I couldn't find any prospects in your database. Make sure your database has people with connection_status='prospect'!"}
            
        response_text = "Here are 25 highly personalized connection requests for new prospects:\n\n"
        for s in suggestions:
            response_text += f"**{s['name']}** ({s['title']} at {s['company']})\n"
            response_text += f"<details><summary>Context Window (Reasoning & Web Data)</summary>\n\n> {s['reasoning']}\n\n> **Live Web Context:**\n> {s['web_context']}\n</details>\n\n"
            response_text += f"> {s['suggested_message'].replace(chr(10), chr(10) + '> ')}\n\n---\n\n"
            
        return {"response": response_text}
        
    elif "suggestion" in message or "who" in message or "contact" in message:
        suggestions = agent.generate_daily_suggestions(num_suggestions=3)
        
        if not suggestions:
            return {"response": "I couldn't find any people or reference DMs to generate suggestions from. Make sure your database has data!"}
            
        response_text = "Here are a few suggestions for today:\n\n"
        for s in suggestions:
            response_text += f"**{s['name']}** ({s['title']} at {s['company']})\n"
            response_text += f"<details><summary>Context Window (Reasoning & Web Data)</summary>\n\n> {s['reasoning']}\n\n> **Live Web Context:**\n> {s['web_context']}\n</details>\n\n"
            response_text += f"> {s['suggested_message'].replace(chr(10), chr(10) + '> ')}\n\n"
            
        return {"response": response_text}
    
    elif "voice" in message or "style" in message or "pitch" in message:
        from faheem_voice import FAHEEM_VOICE_PROFILE
        themes = "\n- ".join(FAHEEM_VOICE_PROFILE.get("core_themes", []))
        return {"response": f"Your voice profile is set to:\n\nThemes:\n- {themes}\n\nTone: {FAHEEM_VOICE_PROFILE.get('tone', {}).get('authenticity', 'Genuine')}"}

    elif "analyze" in message or "reference" in message or "pattern" in message:
        analysis = agent.analyze_reference_dms()
        if not analysis:
            return {"response": "No reference DMs found to analyze."}
        return {"response": f"I've analyzed {analysis['total_dms']} successful DMs. I look for patterns matching your focus on 'signals vs noise'."}
        
    else:
        return {"response": "I'm your LinkedIn outreach agent. I can:\n\n• **25 Connections to Text** — personalized messages for your network\n• **25 Connection Requests** — intro notes for new prospects\n• **Curated Texts** — manage your message templates\n• **Context Window** — see the AI reasoning behind each suggestion\n• **Send Messages** — directly DM connections on LinkedIn\n• **Send Requests** — send connection requests to prospects\n\nUse the sidebar buttons or type a command!"}

# ─────────────────────────────────────────────
# People management
# ─────────────────────────────────────────────

@app.get("/api/people")
async def get_people(connection_status: Optional[str] = None):
    """Get all people, optionally filtered"""
    try:
        people = agent.db.get_all_people(connection_status=connection_status)
        return {"status": "success", "total": len(people), "people": people}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})


# ─────────────────────────────────────────────
# ── NEW: Campaign Pipeline API
# ─────────────────────────────────────────────

class CampaignCreate(BaseModel):
    name: str
    mode: str = "all"          # "texts" | "requests" | "all"
    daily_limit: int = 25

class CampaignTrigger(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None
    headless: bool = False

class LeadsImport(BaseModel):
    campaign_id: int
    connection_status: str = "connection"   # "connection" | "prospect"
    message_type: str = "dm"               # "dm" | "request"
    limit: int = 100


# ── Campaigns ─────────────────────────────────────────────────────────────────

@app.post("/api/campaigns")
async def create_campaign(req: CampaignCreate):
    """Create a new outreach campaign."""
    try:
        c = await local_db.create_campaign(req.name, req.mode, req.daily_limit)
        return {"status": "success", "campaign": c}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

@app.get("/api/campaigns")
async def list_campaigns():
    """List all campaigns with lead counts."""
    try:
        campaigns = await local_db.get_campaigns()
        # Attach active job info
        for c in campaigns:
            active = await local_db.get_active_job(c["id"])
            c["active_job"] = active["job_id"] if active else None
        return {"status": "success", "campaigns": campaigns}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

@app.get("/api/campaigns/{campaign_id}")
async def get_campaign(campaign_id: int):
    """Get a single campaign with its leads."""
    try:
        c = await local_db.get_campaign(campaign_id)
        if not c:
            return JSONResponse(status_code=404, content={"status": "error", "message": "Not found"})
        leads = await local_db.get_leads_by_campaign(campaign_id)
        c["leads"] = leads
        return {"status": "success", "campaign": c}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

@app.patch("/api/campaigns/{campaign_id}/status")
async def set_campaign_status(campaign_id: int, body: dict):
    """Pause or resume a campaign. Body: {"status": "active"|"paused"}"""
    try:
        new_status = body.get("status")
        if new_status not in ("active", "paused", "completed"):
            return JSONResponse(status_code=400, content={"status": "error", "message": "Invalid status"})
        await local_db.update_campaign(campaign_id, status=new_status)
        return {"status": "success", "campaign_status": new_status}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

@app.delete("/api/campaigns/{campaign_id}")
async def delete_campaign(campaign_id: int):
    """Delete a campaign and all its leads."""
    try:
        await local_db.delete_campaign(campaign_id)
        return {"status": "success"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})


# ── Leads ─────────────────────────────────────────────────────────────────────

@app.post("/api/leads/import")
async def import_leads_from_supabase(req: LeadsImport):
    """
    Import people from Supabase into a campaign as leads.
    Deduplicates automatically.
    """
    try:
        people = agent.db.get_all_people(connection_status=req.connection_status)
        if not people:
            return {"status": "success", "added": 0, "message": "No people found in Supabase with that status"}

        leads = [
            {
                "name": p.get("name"),
                "linkedin_url": p.get("linkedin_url"),
                "title": p.get("title"),
                "company": p.get("company"),
                "industry": p.get("industry"),
                "person_id": p.get("id"),
                "message_type": req.message_type,
            }
            for p in people[: req.limit]
        ]
        added = await local_db.bulk_add_leads(req.campaign_id, leads)
        return {"status": "success", "added": added, "total_available": len(people)}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

@app.get("/api/leads")
async def get_leads(campaign_id: int):
    """Get all leads for a campaign."""
    try:
        leads = await local_db.get_leads_by_campaign(campaign_id)
        return {"status": "success", "total": len(leads), "leads": leads}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})


# ── Pipeline Trigger ───────────────────────────────────────────────────────────

@app.post("/api/campaigns/{campaign_id}/run")
async def run_campaign(campaign_id: int, req: CampaignTrigger):
    """
    Manually trigger a campaign pipeline run.
    Returns job_id immediately; run is async in background.
    """
    try:
        job_id = await pipeline.trigger_campaign(
            campaign_id,
            email=req.email,
            password=req.password,
            headless=req.headless,
        )
        return {"status": "started", "job_id": job_id, "campaign_id": campaign_id}
    except ValueError as e:
        return JSONResponse(status_code=400, content={"status": "error", "message": str(e)})
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

@app.post("/api/jobs/{job_id}/cancel")
async def cancel_job(job_id: str):
    """Cancel a running pipeline job."""
    try:
        cancelled = await pipeline.cancel_job(job_id)
        return {"status": "success" if cancelled else "not_found", "job_id": job_id}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})


# ── Jobs ──────────────────────────────────────────────────────────────────────

@app.get("/api/jobs")
async def list_jobs(limit: int = 20):
    """List recent pipeline jobs."""
    try:
        jobs = await local_db.get_recent_jobs(limit=limit)
        active = pipeline.get_active_jobs()
        return {"status": "success", "jobs": jobs, "active_job_ids": active}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    """Poll a job for real-time status and log."""
    try:
        job = await local_db.get_job(job_id)
        if not job:
            return JSONResponse(status_code=404, content={"status": "error", "message": "Job not found"})
        job["is_active"] = job_id in pipeline.get_active_jobs()
        return {"status": "success", "job": job}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})


# ── Analytics ─────────────────────────────────────────────────────────────────

@app.get("/api/analytics")
async def get_analytics():
    """Overall system analytics."""
    try:
        data = await local_db.get_analytics()
        return {"status": "success", **data}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})


# ── Scheduler ─────────────────────────────────────────────────────────────────

@app.get("/api/scheduler/status")
async def get_scheduler_status():
    """Get scheduler info (next run times)."""
    return {"status": "success", "scheduler": scheduler_status()}

@app.post("/api/scheduler/interval")
async def set_scheduler_interval(body: dict):
    """Change the auto-trigger interval. Body: {"hours": N}"""
    try:
        hours = int(body.get("hours", 6))
        stop_scheduler()
        start_scheduler(pipeline, local_db, interval_hours=hours)
        return {"status": "success", "interval_hours": hours}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})


# ─────────────────────────────────────────────
# Mount static files
# ─────────────────────────────────────────────

static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_index():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r") as f:
            return f.read()
    return "UI not built yet."

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)

