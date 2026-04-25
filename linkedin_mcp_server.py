"""
LinkedIn Automation MCP Server for Antigravity
Exposes Faheem's outreach workflow as MCP tools.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from agent import LinkedInAgent
from supabase_database import SupabaseLinkedInDatabase

APP_DIR = Path(__file__).resolve().parent
VOICE_FILE = APP_DIR / "faheem_voice.py"
REFERENCE_FILE = APP_DIR / "faheem_reference_dms.json"

mcp = FastMCP("faheem-linkedin-automation")


def _load_reference_payload() -> dict[str, Any]:
    if not REFERENCE_FILE.exists():
        return {"reference_dms": [], "people": []}
    with REFERENCE_FILE.open("r", encoding="utf-8") as handle:
        return json.load(handle)


@mcp.tool()
def get_voice_profile() -> dict[str, Any]:
    """Return Faheem's LinkedIn voice profile and targeting patterns."""
    from faheem_voice import FAHEEM_VOICE_PROFILE, TARGET_PATTERNS

    return {
        "voice_profile": FAHEEM_VOICE_PROFILE,
        "target_patterns": TARGET_PATTERNS,
    }


@mcp.tool()
def load_reference_dms_from_file() -> dict[str, Any]:
    """Load the reference DMs from the bundled JSON file into Supabase."""
    db = SupabaseLinkedInDatabase()
    payload = _load_reference_payload()
    loaded = 0

    for dm in payload.get("reference_dms", []):
        db.add_reference_dm(
            dm.get("recipient_name"),
            dm.get("recipient_title"),
            dm.get("recipient_company"),
            dm.get("message"),
            dm.get("context"),
            dm.get("success_indicator", "UNKNOWN"),
        )
        loaded += 1

    return {"loaded": loaded, "status": "ok"}


@mcp.tool()
def import_people_from_file() -> dict[str, Any]:
    """Import the bundled example people list into Supabase."""
    db = SupabaseLinkedInDatabase()
    payload = _load_reference_payload()
    loaded = 0

    for person in payload.get("people", []):
        db.add_person(
            person.get("profile_id"),
            person.get("name"),
            person.get("title"),
            person.get("company"),
            person.get("industry"),
            person.get("personality_traits", ""),
            person.get("interests", ""),
            person.get("notes", ""),
        )
        loaded += 1

    return {"loaded": loaded, "status": "ok"}


@mcp.tool()
def list_people() -> dict[str, Any]:
    """List people stored in the outreach database."""
    db = SupabaseLinkedInDatabase()
    return {"people": db.get_all_people()}


@mcp.tool()
def generate_daily_suggestions(limit: int = 5) -> dict[str, Any]:
    """Generate outreach suggestions using Faheem's voice."""
    agent = LinkedInAgent()
    suggestions = agent.generate_daily_suggestions(num_suggestions=limit)
    return {"count": len(suggestions), "suggestions": suggestions}


@mcp.tool()
def mark_person_contacted(person_id: int) -> dict[str, Any]:
    """Mark a person as contacted and update their contact history."""
    db = SupabaseLinkedInDatabase()
    db.update_person_contacted(person_id)
    return {"person_id": person_id, "status": "updated"}


if __name__ == "__main__":
    mcp.run()
