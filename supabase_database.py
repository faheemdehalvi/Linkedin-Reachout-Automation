"""
Supabase Database Integration for LinkedIn Automation
"""
from supabase import create_client, Client
from datetime import datetime
from config import SUPABASE_URL, SUPABASE_ANON_KEY

class SupabaseLinkedInDatabase:
    def __init__(self):
        self.client: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        self.init_db()
    
    def init_db(self):
        """Initialize database tables via Supabase"""
        try:
            # Test connection
            response = self.client.table('people').select("*").limit(1).execute()
            print("✓ Connected to Supabase")
        except Exception as e:
            print(f"⚠ Supabase connection error: {e}")
            print("Make sure tables are created in Supabase dashboard")
    
    def add_reference_dm(self, recipient_name, recipient_title, recipient_company, message, context, success_indicator):
        """Add an old DM as reference for the agent to learn from"""
        try:
            self.client.table('reference_dms').insert({
                'recipient_name': recipient_name,
                'recipient_title': recipient_title,
                'recipient_company': recipient_company,
                'message': message,
                'context': context,
                'success_indicator': success_indicator,
                'created_at': datetime.utcnow().isoformat()
            }).execute()
            print(f"✓ Added reference DM for {recipient_name}")
        except Exception as e:
            print(f"✗ Error adding reference DM: {e}")
    
    def add_person(self, linkedin_profile_id, name, title, company, industry, personality_traits, interests, notes=""):
        """Add a new person to the database"""
        try:
            self.client.table('people').insert({
                'linkedin_profile_id': linkedin_profile_id,
                'name': name,
                'title': title,
                'company': company,
                'industry': industry,
                'personality_traits': personality_traits,
                'interests': interests,
                'notes': notes,
                'contact_count': 0,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }).execute()
            print(f"✓ Added person: {name}")
        except Exception as e:
            if "duplicate" in str(e).lower():
                print(f"⚠ Person already exists: {name}")
            else:
                print(f"✗ Error adding person: {e}")
    
    def get_reference_dms(self):
        """Get all reference DMs for agent analysis"""
        try:
            response = self.client.table('reference_dms').select("*").order('created_at', desc=True).execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"✗ Error fetching reference DMs: {e}")
            return []
    
    def get_all_people(self):
        """Get all people in database"""
        try:
            response = self.client.table('people').select("*").order('last_contacted').execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"✗ Error fetching people: {e}")
            return []
    
    def get_people_by_industry(self, industry):
        """Get people filtered by industry"""
        try:
            response = self.client.table('people').select("*").eq('industry', industry).execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"✗ Error fetching people by industry: {e}")
            return []
    
    def save_daily_suggestion(self, person_id, suggested_message, confidence_score):
        """Save daily suggestion from agent"""
        try:
            self.client.table('daily_suggestions').insert({
                'person_id': person_id,
                'suggested_message': suggested_message,
                'confidence_score': confidence_score,
                'date': datetime.utcnow().date().isoformat(),
                'created_at': datetime.utcnow().isoformat()
            }).execute()
        except Exception as e:
            print(f"✗ Error saving suggestion: {e}")
    
    def update_person_contacted(self, person_id):
        """Update person's last contact date and increment contact count"""
        try:
            # Get current contact count
            response = self.client.table('people').select('contact_count').eq('id', person_id).execute()
            if response.data:
                current_count = response.data[0].get('contact_count', 0) or 0
                
                # Update record
                self.client.table('people').update({
                    'last_contacted': datetime.utcnow().date().isoformat(),
                    'contact_count': current_count + 1,
                    'updated_at': datetime.utcnow().isoformat()
                }).eq('id', person_id).execute()
                
                print(f"✓ Updated person contact record (total contacts: {current_count + 1})")
        except Exception as e:
            print(f"✗ Error updating contact: {e}")
    
    def get_todays_suggestions(self):
        """Get today's suggestions that haven't been acted on"""
        try:
            today = datetime.utcnow().date().isoformat()
            response = self.client.table('daily_suggestions').select("*").eq('date', today).eq('action_taken', False).execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"✗ Error fetching today's suggestions: {e}")
            return []


if __name__ == "__main__":
    db = SupabaseLinkedInDatabase()
    print("Supabase database initialized!")
