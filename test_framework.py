import sys
import os

# Add current directory to path to import agent
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent import LinkedInAgent
from config import OPENROUTER_API_KEY

def run_tests():
    print("=== LinkedIn Agent Testing Framework ===")
    print("Evaluating prompt performance and fallback logic...\n")
    
    agent = LinkedInAgent()
    
    # Check OpenRouter Key status
    if OPENROUTER_API_KEY == "your-key-here" or not OPENROUTER_API_KEY:
        print("WARNING: OPENROUTER_API_KEY is not set. The agent will use the fallback hardcoded logic.")
        print("To see true high-conversion generation, update config.py with a valid key.\n")
    else:
        print("OK: OPENROUTER_API_KEY is set. The agent will use OpenRouter for message generation.\n")

    # Sample profile to test against
    sample_profile = {
        "name": "Sarah",
        "title": "Head of Growth",
        "company": "TechFlow Inc",
        "interests": "customer acquisition, data analytics, PLG",
        "traits": "Data-driven, analytical",
        "base_message": "Hey Sarah, saw you were doing growth stuff. I do data."
    }
    
    print("--- Test Case 1: Head of Growth ---")
    print(f"Target: {sample_profile['name']} - {sample_profile['title']} at {sample_profile['company']}")
    
    msg1 = agent._personalize_message(
        sample_profile["base_message"],
        sample_profile["name"],
        sample_profile["title"],
        sample_profile["company"],
        sample_profile["interests"],
        sample_profile["traits"]
    )
    print("\nGenerated Message:")
    print("--------------------------------------------------")
    print(msg1)
    print("--------------------------------------------------\n")

    
    sample_profile_2 = {
        "name": "David",
        "title": "Data Analyst",
        "company": "FinStream",
        "interests": "SQL, Python, data pipelines",
        "traits": "Technical, precise",
        "base_message": "Hi David, I help analysts."
    }
    
    print("--- Test Case 2: Data Analyst ---")
    print(f"Target: {sample_profile_2['name']} - {sample_profile_2['title']} at {sample_profile_2['company']}")
    
    msg2 = agent._personalize_message(
        sample_profile_2["base_message"],
        sample_profile_2["name"],
        sample_profile_2["title"],
        sample_profile_2["company"],
        sample_profile_2["interests"],
        sample_profile_2["traits"]
    )
    print("\nGenerated Message:")
    print("--------------------------------------------------")
    print(msg2)
    print("--------------------------------------------------\n")

if __name__ == "__main__":
    run_tests()
