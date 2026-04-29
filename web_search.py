from ddgs import DDGS
from typing import Optional

def get_company_context(company_name: str, industry: Optional[str] = None) -> str:
    """
    Search DuckDuckGo for recent context about a company to help personalize the outreach.
    """
    if not company_name:
        return ""
        
    query = f"{company_name} company"
    if industry:
        query += f" {industry}"
    query += " recent news OR what do they do"
    
    try:
        results = DDGS().text(query, max_results=3)
        context = []
        for r in results:
            context.append(f"- {r.get('title', '')}: {r.get('body', '')}")
            
        if context:
            return "Recent Web Context for " + company_name + ":\n" + "\n".join(context)
        return ""
    except Exception as e:
        print(f"Web search warning: {e}")
        return ""

if __name__ == "__main__":
    # Test
    print(get_company_context("MegaCorp", "Technology"))
