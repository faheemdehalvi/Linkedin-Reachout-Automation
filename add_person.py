from supabase_database import SupabaseLinkedInDatabase

def main():
    db = SupabaseLinkedInDatabase()
    
    # ---------------------------------------------------------
    # EDIT THESE DETAILS WITH A REAL PERSON's INFO
    # ---------------------------------------------------------
    person_data = {
        "linkedin_profile_id": "zaveriya-mulla", 
        "linkedin_url": "https://www.linkedin.com/in/zaveriya-mulla/", # The exact profile URL so the bot doesn't get lost searching!
        "name": "Zaveriya Mulla",
        "title": "Software Engineer", 
        "company": "Tech",
        "industry": "Software",
        "personality_traits": "curious, builder",
        "interests": "technology, data",
        "connection_status": "prospect" # 'prospect' sends a connection request. Change to 'connection' to send a DM
    }
    
    # Add to Supabase
    db.add_person(**person_data)
    print(f"\nSuccessfully added {person_data['name']} to the database!")

if __name__ == "__main__":
    main()
