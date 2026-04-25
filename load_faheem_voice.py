"""
Quick loader for Faheem's reference DMs
Run this once to populate your reference database
"""
from supabase_database import SupabaseLinkedInDatabase
import json

def load_faheem_reference_dms():
    """Load the 15 DMs from faheem_reference_dms.json"""
    db = SupabaseLinkedInDatabase()
    
    try:
        with open('faheem_reference_dms.json', 'r') as f:
            data = json.load(f)
        
        print("📚 Loading Faheem's reference DMs...\n")
        
        count = 0
        for dm in data['reference_dms']:
            db.add_reference_dm(
                dm.get('recipient_name'),
                dm.get('recipient_title'),
                dm.get('recipient_company'),
                dm.get('message'),
                dm.get('context'),
                dm.get('success_indicator', 'UNKNOWN')
            )
            count += 1
        
        print(f"\n✓ Loaded {count} reference DMs!")
        print("\n✓ The agent now understands Faheem's voice:")
        print("   - Reference real work (not generic praise)")
        print("   - Connect to THEIR world specifically")
        print("   - Ask genuine questions about problems")
        print("   - Position as curious builder, still learning")
        print("   - Data → signals is the core pitch")
        
    except FileNotFoundError:
        print("❌ faheem_reference_dms.json not found")

if __name__ == "__main__":
    load_faheem_reference_dms()
