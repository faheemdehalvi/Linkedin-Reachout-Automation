from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import sys

# Add current directory to path to import agent
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent import LinkedInAgent

app = FastAPI(title="Faheem's LinkedIn AI")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Agent
agent = LinkedInAgent()

class ChatRequest(BaseModel):
    message: str

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
    
    # Very simple routing logic for the chat
    if "suggestion" in message or "who" in message or "contact" in message:
        suggestions = agent.generate_daily_suggestions(num_suggestions=3)
        
        if not suggestions:
            return {"response": "I couldn't find any people or reference DMs to generate suggestions from. Make sure your database has data!"}
            
        response_text = "Here are a few suggestions for today:\n\n"
        for s in suggestions:
            response_text += f"**{s['name']}** ({s['title']} at {s['company']})\n"
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
        # A generic fallback that uses the agent's system prompt conceptually
        return {"response": "I'm your LinkedIn outreach agent. I can generate personalized daily suggestions (`suggest people to contact`), analyze your reference DMs (`analyze patterns`), or remind you of your voice profile (`show voice profile`). What would you like to do?"}

# Mount static files
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
