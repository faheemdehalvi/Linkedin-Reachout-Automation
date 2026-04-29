"""
Supabase Database Integration for LinkedIn Automation
Supports: connections, curated texts, context windows, connection requests
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
            print("SUCCESS: Connected to Supabase")
        except Exception as e:
            print(f"WARNING: Supabase connection error: {e}")
            print("Make sure tables are created in Supabase dashboard")
    
    # ─────────────────────────────────────────────
    # PEOPLE (existing)
    # ─────────────────────────────────────────────
    
    def add_person(self, linkedin_profile_id, name, title, company, industry, personality_traits, interests, connection_status="connection", notes="", linkedin_url=None):
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
                'connection_status': connection_status,
                'notes': notes,
                'linkedin_url': linkedin_url,
                'contact_count': 0,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }).execute()
            print(f"OK: Added person: {name}")
        except Exception as e:
            if "duplicate" in str(e).lower():
                print(f"WARNING: Person already exists: {name}")
            else:
                print(f"ERROR: Error adding person: {e}")
    
    def get_all_people(self, connection_status=None):
        """Get all people in database, optionally filtered by connection_status"""
        try:
            query = self.client.table('people').select("*")
            if connection_status:
                query = query.eq('connection_status', connection_status)
            response = query.order('last_contacted').execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"ERROR: Error fetching people: {e}")
            return []
    
    def get_person_by_id(self, person_id):
        """Get a single person by ID"""
        try:
            response = self.client.table('people').select("*").eq('id', person_id).single().execute()
            return response.data
        except Exception as e:
            print(f"ERROR: Error fetching person: {e}")
            return None
    
    def get_people_by_industry(self, industry):
        """Get people filtered by industry"""
        try:
            response = self.client.table('people').select("*").eq('industry', industry).execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"ERROR: Error fetching people by industry: {e}")
            return []
    
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
                
                print(f"OK: Updated person contact record (total contacts: {current_count + 1})")
        except Exception as e:
            print(f"ERROR: Error updating contact: {e}")
    
    # ─────────────────────────────────────────────
    # REFERENCE DMs (existing)
    # ─────────────────────────────────────────────
    
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
            print(f"OK: Added reference DM for {recipient_name}")
        except Exception as e:
            print(f"ERROR: Error adding reference DM: {e}")
    
    def get_reference_dms(self):
        """Get all reference DMs for agent analysis"""
        try:
            response = self.client.table('reference_dms').select("*").order('created_at', desc=True).execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"ERROR: Error fetching reference DMs: {e}")
            return []
    
    # ─────────────────────────────────────────────
    # DAILY SUGGESTIONS (updated with suggestion_type)
    # ─────────────────────────────────────────────
    
    def save_daily_suggestion(self, person_id, suggested_message, confidence_score, suggestion_type="connection_text"):
        """Save daily suggestion from agent with type tracking"""
        try:
            response = self.client.table('daily_suggestions').insert({
                'person_id': person_id,
                'suggested_message': suggested_message,
                'confidence_score': confidence_score,
                'suggestion_type': suggestion_type,
                'date': datetime.utcnow().date().isoformat(),
                'created_at': datetime.utcnow().isoformat()
            }).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"ERROR: Error saving suggestion: {e}")
            return None
    
    def get_todays_suggestions(self, suggestion_type=None):
        """Get today's suggestions that haven't been acted on"""
        try:
            today = datetime.utcnow().date().isoformat()
            query = self.client.table('daily_suggestions').select("*").eq('date', today).eq('action_taken', False)
            if suggestion_type:
                query = query.eq('suggestion_type', suggestion_type)
            response = query.execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"ERROR: Error fetching today's suggestions: {e}")
            return []
    
    def update_suggestion_status(self, suggestion_id, send_status, sent_at=None):
        """Update send status of a suggestion (pending/sent/failed)"""
        try:
            update_data = {
                'send_status': send_status,
                'action_taken': send_status == 'sent',
            }
            if sent_at:
                update_data['sent_at'] = sent_at
            self.client.table('daily_suggestions').update(update_data).eq('id', suggestion_id).execute()
            print(f"OK: Suggestion #{suggestion_id} status → {send_status}")
        except Exception as e:
            print(f"ERROR: Error updating suggestion status: {e}")
    
    # ─────────────────────────────────────────────
    # CURATED TEXTS (new - Feature #2)
    # ─────────────────────────────────────────────
    
    def add_curated_text(self, title, message_template, target_industry="", target_role="", tags=""):
        """Add a personally curated text template"""
        try:
            response = self.client.table('curated_texts').insert({
                'title': title,
                'message_template': message_template,
                'target_industry': target_industry,
                'target_role': target_role,
                'tags': tags,
                'is_active': True,
                'usage_count': 0,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }).execute()
            print(f"OK: Added curated text: {title}")
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"ERROR: Error adding curated text: {e}")
            return None
    
    def get_curated_texts(self, active_only=True):
        """Get all curated text templates"""
        try:
            query = self.client.table('curated_texts').select("*")
            if active_only:
                query = query.eq('is_active', True)
            response = query.order('created_at', desc=True).execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"ERROR: Error fetching curated texts: {e}")
            return []
    
    def update_curated_text(self, text_id, updates):
        """Update a curated text template"""
        try:
            updates['updated_at'] = datetime.utcnow().isoformat()
            response = self.client.table('curated_texts').update(updates).eq('id', text_id).execute()
            print(f"OK: Updated curated text #{text_id}")
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"ERROR: Error updating curated text: {e}")
            return None
    
    def delete_curated_text(self, text_id):
        """Soft delete a curated text (set is_active=false)"""
        try:
            self.client.table('curated_texts').update({
                'is_active': False,
                'updated_at': datetime.utcnow().isoformat()
            }).eq('id', text_id).execute()
            print(f"OK: Deactivated curated text #{text_id}")
            return True
        except Exception as e:
            print(f"ERROR: Error deleting curated text: {e}")
            return False
    
    def increment_curated_text_usage(self, text_id):
        """Increment usage count for a curated text"""
        try:
            response = self.client.table('curated_texts').select('usage_count').eq('id', text_id).execute()
            if response.data:
                current = response.data[0].get('usage_count', 0) or 0
                self.client.table('curated_texts').update({
                    'usage_count': current + 1,
                    'updated_at': datetime.utcnow().isoformat()
                }).eq('id', text_id).execute()
        except Exception as e:
            print(f"ERROR: Error incrementing usage: {e}")
    
    # ─────────────────────────────────────────────
    # CONTEXT WINDOWS (new - Feature #3)
    # ─────────────────────────────────────────────
    
    def save_context_window(self, person_id, suggestion_id, reasoning_chain, web_research, matched_pattern, voice_alignment_score, connection_type="connection"):
        """Save full AI reasoning context for a suggestion"""
        try:
            response = self.client.table('context_windows').insert({
                'person_id': person_id,
                'suggestion_id': suggestion_id,
                'reasoning_chain': reasoning_chain,
                'web_research': web_research,
                'matched_pattern': matched_pattern,
                'voice_alignment_score': voice_alignment_score,
                'connection_type': connection_type,
                'created_at': datetime.utcnow().isoformat()
            }).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"ERROR: Error saving context window: {e}")
            return None
    
    def get_context_window(self, person_id):
        """Get the most recent context window for a person"""
        try:
            response = self.client.table('context_windows').select("*").eq('person_id', person_id).order('created_at', desc=True).limit(1).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"ERROR: Error fetching context window: {e}")
            return None
    
    def get_context_window_by_suggestion(self, suggestion_id):
        """Get context window for a specific suggestion"""
        try:
            response = self.client.table('context_windows').select("*").eq('suggestion_id', suggestion_id).single().execute()
            return response.data
        except Exception as e:
            print(f"ERROR: Error fetching context window: {e}")
            return None
    
    def get_todays_context_windows(self, connection_type=None):
        """Get all context windows generated today"""
        try:
            today = datetime.utcnow().date().isoformat()
            query = self.client.table('context_windows').select("*").gte('created_at', today)
            if connection_type:
                query = query.eq('connection_type', connection_type)
            response = query.order('created_at', desc=True).execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"ERROR: Error fetching today's context windows: {e}")
            return []


if __name__ == "__main__":
    db = SupabaseLinkedInDatabase()
    print("Supabase database initialized!")
