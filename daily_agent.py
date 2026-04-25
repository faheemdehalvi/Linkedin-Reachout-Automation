"""
Daily LinkedIn Agent CLI
Run this every day to get personalized outreach suggestions
"""
import sys
from datetime import datetime
from supabase_database import SupabaseLinkedInDatabase
from agent import LinkedInAgent

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")

def print_suggestion(idx, suggestion):
    print(f"\n📌 Suggestion #{idx + 1}")
    print(f"   Name: {suggestion['name']}")
    print(f"   Title: {suggestion['title']}")
    print(f"   Company: {suggestion['company']}")
    print(f"   Confidence: {suggestion['confidence_score']*100:.0f}%")
    print(f"\n   📧 Suggested Message (in YOUR voice):")
    print("   " + "-"*56)
    for line in suggestion['suggested_message'].split('\n'):
        print(f"   {line}")
    print("   " + "-"*56)
    print(f"\n   ℹ️  Why this person: {suggestion['reasoning']}")
    print(f"   💡 Remember: personalize further before sending!")

def main():
    print_header("🤖 LinkedIn Daily Agent - " + datetime.now().strftime("%B %d, %Y"))
    
    # Initialize
    db = SupabaseLinkedInDatabase()
    agent = LinkedInAgent()
    
    # Check for people in database
    people = db.get_all_people()
    if not people:
        print("❌ No people in database yet. Please add people first.")
        print("\nUsage: python setup_data.py <your_dm_data.json>")
        return
    
    # Generate suggestions
    print("Generating daily suggestions...")
    suggestions = agent.generate_daily_suggestions(num_suggestions=5)
    
    if not suggestions:
        print("⚠️  Could not generate suggestions. Make sure you have:")
        print("   1. Added at least one reference DM")
        print("   2. Added people to reach out to")
        return
    
    # Display suggestions
    print_header(f"Today's Top {len(suggestions)} Suggestions")
    for idx, suggestion in enumerate(suggestions):
        print_suggestion(idx, suggestion)
    
    # Action menu
    print("\n" + "="*60)
    print("  What would you like to do?")
    print("="*60)
    print("\n1. ✅ Mark as contacted (and move to next person)")
    print("2. 📝 Refine suggestion for person #X")
    print("3. 💾 Save all for later")
    print("4. 🚪 Exit")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        person_idx = input("Enter person number (1-5): ").strip()
        try:
            person_idx = int(person_idx) - 1
            if 0 <= person_idx < len(suggestions):
                person_id = suggestions[person_idx]['person_id']
                db.update_person_contacted(person_id)
                print(f"\n✓ Marked {suggestions[person_idx]['name']} as contacted!")
            else:
                print("Invalid selection")
        except ValueError:
            print("Invalid input")
    
    elif choice == "2":
        person_idx = input("Enter person number to refine (1-5): ").strip()
        try:
            person_idx = int(person_idx) - 1
            if 0 <= person_idx < len(suggestions):
                print(f"\nCurrent message for {suggestions[person_idx]['name']}:")
                print("-"*56)
                print(suggestions[person_idx]['suggested_message'])
                print("-"*56)
                print("\nTips for refinement:")
                print("- Make it more personal")
                print("- Add specific details about their work")
                print("- Reference their recent activity/posts")
                print("\nUse the message above as a base and customize in LinkedIn")
            else:
                print("Invalid selection")
        except ValueError:
            print("Invalid input")
    
    elif choice == "3":
        print("\n✓ Suggestions saved to database")
        print("✓ You can review them later in the Supabase dashboard")
    
    elif choice == "4":
        print("\n👋 See you tomorrow!")
    
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()
