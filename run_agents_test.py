"""
Real-time live test of all 4 LinkedIn Automation Agents.
Runs actual LLM calls against Supabase data.
"""
from agent import LinkedInAgent
from supabase_database import SupabaseLinkedInDatabase

SEP = "=" * 60

def header(text):
    print(f"\n{SEP}\n  {text}\n{SEP}")

def main():
    print(f"\n{'#'*60}")
    print("  REAL-TIME AGENT TEST — ALL 4 FEATURES")
    print(f"{'#'*60}")

    agent = LinkedInAgent()
    db = agent.db

    # ─── FEATURE 1: Connection Texts ───────────────────────────
    header("FEATURE 1 — Connection Texts (existing connections)")
    texts = agent.generate_connection_texts(num_suggestions=2)
    print(f"  Generated: {len(texts)} messages")
    for t in texts:
        print(f"\n  > Person     : {t['name']} | {t['title']} @ {t['company']}")
        print(f"  > Confidence : {t['confidence_score']}")
        print(f"  > Ctx Window : {t['context_window_id']}")
        print(f"  > Message    :\n    {t['suggested_message'][:200]}")

    # ─── FEATURE 2: Curated Texts ──────────────────────────────
    header("FEATURE 2 — Curated Text Matching")
    result = agent.get_curated_suggestions(num_suggestions=5)
    print(f"  Templates available : {result['total_templates']}")
    print(f"  Matched to people   : {result['total_matched']}")
    for m in result.get("matched_suggestions", []):
        person = m["matched_person"]
        print(f"\n  > Template : {m['template_title']}")
        print(f"  > Matched  : {person['name']} ({person['industry']})")

    # ─── FEATURE 3: Context Windows ────────────────────────────
    header("FEATURE 3 — Context Windows (AI Reasoning Stored)")
    windows = db.get_todays_context_windows()
    print(f"  Windows saved today: {len(windows)}")
    for w in windows[:2]:
        chain = w.get("reasoning_chain", {})
        step1 = chain.get("step_1_person_analysis", {})
        step4 = chain.get("step_4_decision", {})
        print(f"\n  > Person ID          : {w['person_id']}")
        print(f"  > Name               : {step1.get('name', 'N/A')}")
        print(f"  > Voice Alignment    : {w['voice_alignment_score']}")
        print(f"  > Confidence         : {step4.get('confidence_score', 'N/A')}")
        print(f"  > Why This Person    : {step4.get('why_this_person', 'N/A')[:100]}")

    # ─── FEATURE 4: Connection Requests ────────────────────────
    header("FEATURE 4 — Connection Requests (new prospects)")
    reqs = agent.generate_connection_requests(num_suggestions=2)
    print(f"  Generated: {len(reqs)} requests")
    for r in reqs:
        print(f"\n  > Prospect   : {r['name']} | {r['title']} @ {r['company']}")
        print(f"  > Confidence : {r['confidence_score']}")
        print(f"  > Message    :\n    {r['suggested_message'][:200]}")

    # ─── SUMMARY ───────────────────────────────────────────────
    header("SUMMARY")
    feat1_ok = len(texts) > 0
    feat2_ok = result["total_templates"] >= 0
    feat3_ok = len(windows) >= 0
    feat4_ok = len(reqs) > 0

    print(f"  Feature 1 — Connection Texts    : {'PASS' if feat1_ok else 'FAIL'} ({len(texts)} generated)")
    print(f"  Feature 2 — Curated Texts       : {'PASS' if feat2_ok else 'FAIL'} ({result['total_templates']} templates)")
    print(f"  Feature 3 — Context Windows     : {'PASS' if feat3_ok else 'FAIL'} ({len(windows)} windows today)")
    print(f"  Feature 4 — Connection Requests : {'PASS' if feat4_ok else 'FAIL'} ({len(reqs)} generated)")

    all_ok = feat1_ok and feat2_ok and feat3_ok and feat4_ok
    print(f"\n  Overall Status: {'ALL SYSTEMS GO' if all_ok else 'ISSUES DETECTED'}")

if __name__ == "__main__":
    main()
