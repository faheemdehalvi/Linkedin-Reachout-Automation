"""
Full verification script for all 4 LinkedIn Automation features.
Run this after creating tables in Supabase SQL Editor.

Step 1: Creates the tables (you need to do this manually in Supabase SQL Editor)
Step 2: Seeds test data (people + reference DMs)
Step 3: Tests each feature endpoint
"""
import json
import requests
import time
from supabase_database import SupabaseLinkedInDatabase

API_BASE = "http://127.0.0.1:8000"

def print_header(text):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def print_result(name, passed, detail=""):
    icon = "PASS" if passed else "FAIL"
    print(f"  [{icon}] {name}" + (f" -- {detail}" if detail else ""))

def step1_check_tables():
    """Check if Supabase tables exist"""
    print_header("Step 1: Checking Supabase Tables")
    db = SupabaseLinkedInDatabase()
    
    tables_ok = True
    for table in ['people', 'reference_dms', 'daily_suggestions', 'curated_texts', 'context_windows']:
        try:
            db.client.table(table).select("*").limit(1).execute()
            print_result(f"Table '{table}'", True, "exists")
        except Exception as e:
            print_result(f"Table '{table}'", False, str(e)[:80])
            tables_ok = False
    
    if not tables_ok:
        print("\n  ACTION REQUIRED: Run database_setup.sql in your Supabase SQL Editor!")
        print("  1. Go to https://supabase.com/dashboard")
        print("  2. Select your project")
        print("  3. Click 'SQL Editor' in the left sidebar")
        print("  4. Paste the contents of database_setup.sql")
        print("  5. Click 'Run'")
        print("  6. Then re-run this script")
    
    return tables_ok

def step2_seed_data():
    """Seed test people and reference DMs"""
    print_header("Step 2: Seeding Test Data")
    db = SupabaseLinkedInDatabase()
    
    # Add test connections
    test_connections = [
        ("conn-1", "Sarah Chen", "Product Manager", "Stripe", "Fintech", "analytical,curious", "payments,growth,product-led"),
        ("conn-2", "Marcus Rivera", "Head of Growth", "Notion", "SaaS", "strategic,data-driven", "PLG,retention,analytics"),
        ("conn-3", "Priya Patel", "ML Engineer", "Canva", "Design Tech", "technical,collaborative", "computer vision,ML ops"),
        ("conn-4", "James Liu", "Founder", "DataStack AI", "AI/ML", "visionary,fast-mover", "data pipelines,LLMs"),
        ("conn-5", "Emma Watson", "Analytics Lead", "Atlassian", "DevTools", "detail-oriented", "dashboards,metrics"),
    ]
    
    for pid, name, title, company, industry, traits, interests in test_connections:
        db.add_person(pid, name, title, company, industry, traits, interests, connection_status="connection")
    
    print_result("Added 5 test connections", True)
    
    # Add test prospects
    test_prospects = [
        ("pros-1", "Alex Zhao", "VP Engineering", "Scale AI", "AI Infrastructure", "technical leader", "ML infrastructure"),
        ("pros-2", "Nina Gupta", "Director of Data", "Razorpay", "Fintech", "strategic", "data engineering,analytics"),
        ("pros-3", "Tom Black", "CTO", "Buildkite", "DevOps", "builder,systems-thinker", "CI/CD,developer tools"),
    ]
    
    for pid, name, title, company, industry, traits, interests in test_prospects:
        db.add_person(pid, name, title, company, industry, traits, interests, connection_status="prospect")
    
    print_result("Added 3 test prospects", True)
    
    # Load reference DMs from existing file
    try:
        with open("faheem_reference_dms.json", "r") as f:
            data = json.load(f)
        
        for dm in data.get("reference_dms", [])[:5]:  # Load first 5
            db.add_reference_dm(
                dm["recipient_name"], dm["recipient_title"], dm["recipient_company"],
                dm["message"], dm["context"], dm["success_indicator"]
            )
        print_result("Loaded 5 reference DMs", True)
    except Exception as e:
        print_result("Loading reference DMs", False, str(e)[:80])
    
    # Verify counts
    people = db.get_all_people()
    connections = db.get_all_people("connection")
    prospects = db.get_all_people("prospect")
    dms = db.get_reference_dms()
    
    print(f"\n  Database totals:")
    print(f"    People: {len(people)}")
    print(f"    Connections: {len(connections)}")
    print(f"    Prospects: {len(prospects)}")
    print(f"    Reference DMs: {len(dms)}")
    
    return len(connections) > 0 and len(dms) > 0

def step3_test_api():
    """Test all API endpoints"""
    print_header("Step 3: Testing API Endpoints")
    
    all_pass = True
    
    # Test 1: People endpoint
    try:
        r = requests.get(f"{API_BASE}/api/people", timeout=5)
        d = r.json()
        ok = d.get("status") == "success" and d.get("total", 0) > 0
        print_result("GET /api/people", ok, f"{d.get('total',0)} people found")
        all_pass = all_pass and ok
    except Exception as e:
        print_result("GET /api/people", False, str(e)[:80])
        all_pass = False
    
    # Test 2: Curated texts CRUD
    try:
        # Create
        r = requests.post(f"{API_BASE}/api/curated-texts", json={
            "title": "Test: Data Founder Hook",
            "message_template": "Hi {name},\n\nCame across {company} and really liked how you're approaching the data problem.\n\nI've been building a layer that turns raw data into clear signals. Still early.\n\nWould love your take.\n\nThanks,\nFaheem",
            "target_industry": "AI/ML",
            "target_role": "Founder",
            "tags": "data,AI,founder"
        }, timeout=5)
        d = r.json()
        created = d.get("status") == "success"
        text_id = d.get("text", {}).get("id")
        print_result("POST /api/curated-texts (create)", created, f"id={text_id}")
        
        # Read
        r = requests.get(f"{API_BASE}/api/curated-texts", timeout=5)
        d = r.json()
        has_texts = d.get("total", 0) > 0
        print_result("GET /api/curated-texts (read)", has_texts, f"{d.get('total',0)} texts")
        
        # Update
        if text_id:
            r = requests.put(f"{API_BASE}/api/curated-texts/{text_id}", json={"title": "Updated: Data Founder Hook"}, timeout=5)
            d = r.json()
            updated = d.get("status") == "success"
            print_result("PUT /api/curated-texts (update)", updated)
        
        all_pass = all_pass and created and has_texts
    except Exception as e:
        print_result("Curated Texts CRUD", False, str(e)[:80])
        all_pass = False
    
    # Test 3: Connection texts (Feature #1) — this calls the LLM so may take time
    print("\n  [INFO] Skipping LLM-dependent tests (connection-texts, connection-requests)")
    print("  [INFO] These require OpenRouter API key to be valid")
    print("  [INFO] Test them from the UI by clicking 'Generate 25'")
    
    # Test 4: Context window endpoint
    try:
        r = requests.get(f"{API_BASE}/api/context-windows/today", timeout=5)
        d = r.json()
        ok = d.get("status") == "success"
        print_result("GET /api/context-windows/today", ok, f"{d.get('total',0)} windows")
        all_pass = all_pass and ok
    except Exception as e:
        print_result("GET /api/context-windows/today", False, str(e)[:80])
        all_pass = False
    
    # Test 5: Chat endpoint
    try:
        r = requests.post(f"{API_BASE}/api/chat", json={"message": "hello"}, timeout=5)
        d = r.json()
        ok = "response" in d
        print_result("POST /api/chat", ok, "chat responding")
        all_pass = all_pass and ok
    except Exception as e:
        print_result("POST /api/chat", False, str(e)[:80])
        all_pass = False
    
    return all_pass

def step4_test_ui():
    """Instructions for manual UI testing"""
    print_header("Step 4: Manual UI Testing")
    print("""
  Open http://127.0.0.1:8000 in your browser and verify:
  
  1. CONNECTION TEXTS tab:
     - Click 'Generate 25' button
     - Cards should appear with person name, role, message, confidence %
     - Click any card -> Context Window panel slides open on the right
     
  2. CURATED TEXTS tab:
     - Click 'Add Template' -> form appears
     - Fill in title + message + industry/role/tags -> Save
     - Card appears in the list with Edit/Delete buttons
     - Test Edit and Delete
     
  3. CONNECTION REQUESTS tab:
     - Click 'Generate 25' button
     - Cards should appear for prospects with shorter intro messages
     - Click any card -> Context Window opens
     
  4. AGENT CHAT tab:
     - Type 'hello' -> agent responds
     - Type '25 connections' -> generates texts via chat
     
  5. CONTEXT WINDOW (right panel):
     - Shows: Person Analysis, Pattern Matching, Scores, Why This Person, Web Research
     - Voice Alignment and Confidence score bars should render
     - Close button (X) should close the panel
""")

def main():
    print("\n" + "#" * 60)
    print("  LINKEDIN AUTOMATION - FULL VERIFICATION")
    print("#" * 60)
    
    # Step 1: Check tables
    tables_ok = step1_check_tables()
    if not tables_ok:
        print("\n  STOPPING: Fix Supabase tables first, then re-run this script.")
        return
    
    # Step 2: Seed data
    data_ok = step2_seed_data()
    if not data_ok:
        print("\n  WARNING: Data seeding had issues, but continuing...")
    
    # Step 3: Test API
    api_ok = step3_test_api()
    
    # Step 4: UI instructions
    step4_test_ui()
    
    # Summary
    print_header("SUMMARY")
    print_result("Supabase Tables", tables_ok)
    print_result("Test Data Seeded", data_ok)
    print_result("API Endpoints", api_ok)
    print(f"\n  Server: http://127.0.0.1:8000")
    print(f"  All systems {'GO' if (tables_ok and api_ok) else 'NEED ATTENTION'}")

if __name__ == "__main__":
    main()
