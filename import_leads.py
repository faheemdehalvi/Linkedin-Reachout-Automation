import csv
import sys
import os
from supabase_database import SupabaseLinkedInDatabase

def import_csv(file_path):
    if not os.path.exists(file_path):
        print(f"Error: Could not find {file_path}")
        print("Please make sure you have a 'leads.csv' file in this folder.")
        return

    db = SupabaseLinkedInDatabase()
    added_count = 0

    print(f"\nImporting leads from {file_path}...")
    
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        # Verify required columns exist
        required_cols = ['name', 'linkedin_url', 'connection_status']
        for col in required_cols:
            if col not in reader.fieldnames:
                print(f"Error: CSV is missing required column: '{col}'")
                return
                
        for row in reader:
            try:
                name = row.get('name', '').strip()
                if not name:
                    continue
                    
                # The script expects 'linkedin_profile_id' as a required field in the DB schema, 
                # but we can just use the name or a slug if the URL is provided.
                linkedin_url = row.get('linkedin_url', '').strip()
                profile_id = linkedin_url.split('/in/')[-1].strip('/') if '/in/' in linkedin_url else name.replace(' ', '-').lower()
                
                db.add_person(
                    linkedin_profile_id=profile_id,
                    name=name,
                    title=row.get('title', ''),
                    company=row.get('company', ''),
                    industry=row.get('industry', ''),
                    personality_traits=row.get('personality_traits', ''),
                    interests=row.get('interests', ''),
                    connection_status=row.get('connection_status', 'prospect'),
                    notes=row.get('notes', ''),
                    linkedin_url=linkedin_url
                )
                added_count += 1
            except Exception as e:
                print(f"Failed to add {row.get('name')}: {e}")

    print(f"\nDone! Successfully imported {added_count} leads into the database.")

if __name__ == "__main__":
    import_csv("leads.csv")
