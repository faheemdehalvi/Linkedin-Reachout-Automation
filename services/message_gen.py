"""
Message Generation Service
Async wrapper around the existing LinkedInAgent.
Runs blocking LLM calls in a thread-pool so they don't block the event loop.
"""
import asyncio
from typing import List, Optional
from agent import LinkedInAgent

_agent: Optional[LinkedInAgent] = None


def get_agent() -> LinkedInAgent:
    global _agent
    if _agent is None:
        _agent = LinkedInAgent()
    return _agent


async def generate_dm_message(
    name: str,
    title: str,
    company: str,
    industry: str = "",
    interests: str = "",
    traits: str = "",
) -> dict:
    """
    Generate a personalised DM for an existing connection.
    Returns {"message": str, "web_context": str, "suggestion_id": int|None}
    """
    agent = get_agent()
    loop = asyncio.get_event_loop()

    def _generate():
        reference_dms = agent.analyze_reference_dms()
        if not reference_dms:
            return None
        matching_dm = agent._find_similar_reference_dm(title, company, industry, reference_dms)
        if not matching_dm:
            return None
        result = agent._personalize_message(
            matching_dm["message"], name, title, company, interests, traits,
            system_prompt=agent.system_prompt_connection,
        )
        return result  # {"message": str, "web_context": str}

    result = await loop.run_in_executor(None, _generate)
    if result is None:
        # Fallback message
        result = {
            "message": (
                f"Hi {name},\n\nCame across your profile at {company} and your work "
                f"resonated with how I think about turning raw data into actionable signals.\n\n"
                f"Still early, but feels relevant to what you're navigating in [{title or 'your role'}]. "
                f"How are you approaching this right now?\n\nThanks, Faheem"
            ),
            "web_context": "",
        }
    return result


async def generate_connection_request(
    name: str,
    title: str,
    company: str,
    industry: str = "",
    interests: str = "",
    traits: str = "",
) -> dict:
    """
    Generate a short connection-request note (<300 chars).
    Returns {"message": str, "web_context": str}
    """
    agent = get_agent()
    loop = asyncio.get_event_loop()

    def _generate():
        reference_dms = agent.analyze_reference_dms()
        if not reference_dms:
            return None
        matching_dm = agent._find_similar_reference_dm(title, company, industry, reference_dms)
        if not matching_dm:
            return None
        result = agent._personalize_message(
            matching_dm["message"], name, title, company, interests, traits,
            system_prompt=agent.system_prompt_request,
        )
        return result

    result = await loop.run_in_executor(None, _generate)
    if result is None:
        result = {
            "message": (
                f"Hey {name}, noticed your work at {company} — really interesting "
                f"how you're approaching [{title or 'your domain'}]. "
                f"Would love to connect and exchange ideas."
            )[:300],
            "web_context": "",
        }
    return result


async def generate_batch(leads: List[dict]) -> List[dict]:
    """
    Generate messages for a list of leads concurrently (thread-pool, max 8 workers).
    Each lead dict must have: name, title, company, industry, message_type ('dm'|'request')
    Adds 'generated_message' and 'web_context' keys to each lead.
    """
    semaphore = asyncio.Semaphore(8)

    async def _gen_one(lead: dict) -> dict:
        async with semaphore:
            fn = generate_dm_message if lead.get("message_type") != "request" else generate_connection_request
            result = await fn(
                name=lead.get("name", ""),
                title=lead.get("title", ""),
                company=lead.get("company", ""),
                industry=lead.get("industry", ""),
            )
            lead["generated_message"] = result["message"]
            lead["web_context"] = result.get("web_context", "")
            return lead

    tasks = [_gen_one(lead) for lead in leads]
    return await asyncio.gather(*tasks)
