"""
Setup script to load reference DMs and people into the database
"""
import json
import sys
from database import LinkedInDatabase

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")

def add_reference_dms_interactive(db):
    """Interactive mode to add reference DMs"""
    print_header("📚 Add Your Old Successful DMs")
    print("These DMs will teach the agent your outreach style.\n")
    
    dms_added = 0
    
    while True:
        print(f"\n--- Reference DM #{dms_added + 1} ---")
        
        recipient_name = input("Recipient name: ").strip()
        if not recipient_name:
            break
        
        recipient_title = input("Recipient title (e.g., 'Product Manager'): ").strip()
        recipient_company = input("Recipient company: ").strip()
        
        print("\nPaste the DM message (end with 'END' on a new line):")
        message_lines = []
        while True:
            line = input()
            if line.strip() == "END":
                break
            message_lines.append(line)
        message = "\n".join(message_lines)
        
        context = input("\nContext/Reason for reaching out: ").strip()
        success_indicator = input("Did this lead to positive response? (yes/no): ").strip().lower() == "yes"
        
        db.add_reference_dm(
            recipient_name,
            recipient_title,
            recipient_company,
            message,
            context,
            "SUCCESS" if success_indicator else "UNKNOWN"
        )
        
        dms_added += 1
        
        another = input("\nAdd another DM? (yes/no): ").strip().lower()
        if another != "yes":
            break
    
    return dms_added

def add_people_interactive(db):
    """Interactive mode to add people to contact"""
    print_header("👥 Add People to Contact")
    print("These are people you want to reach out to.\n")
    
    people_added = 0
    
    while True:
        print(f"\n--- Person #{people_added + 1} ---")
        
        name = input("Name: ").strip()
        if not name:
            break
        
        profile_id = input("LinkedIn profile ID/URL: ").strip()
        title = input("Their title: ").strip()
        company = input("Company: ").strip()
        industry = input("Industry (e.g., 'Tech', 'Finance'): ").strip()
        traits = input("Personality traits (comma-separated): ").strip()
        interests = input("Their interests/skills: ").strip()
        notes = input("Any other notes: ").strip()
        
        db.add_person(
            profile_id,
            name,
            title,
            company,
            industry,
            traits,
            interests,
            notes
        )
        
        people_added += 1
        
        another = input("\nAdd another person? (yes/no): ").strip().lower()
        if another != "yes":
            break
    
    return people_added

def add_from_json(db, json_file):
    """Load data from JSON file"""
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        # Add reference DMs
        if 'reference_dms' in data:
            for dm in data['reference_dms']:
                db.add_reference_dm(
                    dm.get('recipient_name'),
                    dm.get('recipient_title'),
                    dm.get('recipient_company'),
                    dm.get('message'),
                    dm.get('context'),
                    dm.get('success_indicator', 'UNKNOWN')
                )
            print(f"✓ Added {len(data['reference_dms'])} reference DMs")
        
        # Add people
        if 'people' in data:
            for person in data['people']:
                db.add_person(
                    person.get('profile_id'),
                    person.get('name'),
                    person.get('title'),
                    person.get('company'),
                    person.get('industry'),
                    person.get('personality_traits', ''),
                    person.get('interests', ''),
                    person.get('notes', '')
                )
            print(f"✓ Added {len(data['people'])} people")
        
        return len(data.get('reference_dms', [])), len(data.get('people', []))
    
    except Exception as e:
        print(f"✗ Error loading JSON file: {e}")
        return 0, 0

def main():
    print_header("🚀 LinkedIn Automation Setup")
    
    db = LinkedInDatabase()
    
    print("\nHow would you like to add data?")
    print("1. Interactive mode (guided input)")
    print("2. Load from JSON file")
    print("3. Exit")
    
    choice = input("\nChoose option (1-3): ").strip()
    
    dms_added = 0
    people_added = 0
    
    if choice == "1":
        dms_added = add_reference_dms_interactive(db)
        people_added = add_people_interactive(db)
    
    elif choice == "2":
        json_file = input("Enter path to JSON file: ").strip()
        dms_added, people_added = add_from_json(db, json_file)
    
    else:
        print("Exiting...")
        return
    
    # Summary
    print_header("✓ Setup Complete!")
    print(f"Added {dms_added} reference DMs")
    print(f"Added {people_added} people to contact")
    print("\n🎯 Next step: Run 'python daily_agent.py' to get daily suggestions")

if __name__ == "__main__":
    main()
