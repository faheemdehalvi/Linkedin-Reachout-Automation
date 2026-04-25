import sqlite3
from pathlib import Path
from datetime import datetime
from config import DATABASE_PATH

class LinkedInDatabase:
    def __init__(self, db_path=DATABASE_PATH):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # People table - stores context about each person
        c.execute('''CREATE TABLE IF NOT EXISTS people (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            linkedin_profile_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            title TEXT,
            company TEXT,
            industry TEXT,
            personality_traits TEXT,
            interests TEXT,
            last_contacted DATE,
            contact_count INTEGER DEFAULT 0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # Messages table - stores sent/received messages for reference
        c.execute('''CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER NOT NULL,
            sender TEXT,
            receiver TEXT,
            message_content TEXT NOT NULL,
            timestamp DATE,
            response_received BOOLEAN DEFAULT 0,
            effectiveness_score FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (person_id) REFERENCES people (id)
        )''')
        
        # Reference DMs table - stores your old DMs for pattern analysis
        c.execute('''CREATE TABLE IF NOT EXISTS reference_dms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipient_name TEXT,
            recipient_title TEXT,
            recipient_company TEXT,
            message TEXT NOT NULL,
            context TEXT,
            success_indicator TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # Daily suggestions table - tracks what was suggested each day
        c.execute('''CREATE TABLE IF NOT EXISTS daily_suggestions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE DEFAULT CURRENT_DATE,
            person_id INTEGER,
            suggested_message TEXT,
            confidence_score FLOAT,
            action_taken BOOLEAN DEFAULT 0,
            result TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (person_id) REFERENCES people (id)
        )''')
        
        conn.commit()
        conn.close()
        print(f"✓ Database initialized at {self.db_path}")
    
    def add_reference_dm(self, recipient_name, recipient_title, recipient_company, message, context, success_indicator):
        """Add an old DM as reference for the agent to learn from"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''INSERT INTO reference_dms 
                     (recipient_name, recipient_title, recipient_company, message, context, success_indicator)
                     VALUES (?, ?, ?, ?, ?, ?)''',
                  (recipient_name, recipient_title, recipient_company, message, context, success_indicator))
        
        conn.commit()
        conn.close()
        print(f"✓ Added reference DM for {recipient_name}")
    
    def add_person(self, linkedin_profile_id, name, title, company, industry, personality_traits, interests, notes=""):
        """Add a new person to the database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        try:
            c.execute('''INSERT INTO people 
                         (linkedin_profile_id, name, title, company, industry, personality_traits, interests, notes)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                      (linkedin_profile_id, name, title, company, industry, personality_traits, interests, notes))
            conn.commit()
            print(f"✓ Added person: {name}")
        except sqlite3.IntegrityError:
            print(f"⚠ Person already exists: {name}")
        finally:
            conn.close()
    
    def get_reference_dms(self):
        """Get all reference DMs for agent analysis"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('SELECT * FROM reference_dms ORDER BY created_at DESC')
        dms = c.fetchall()
        conn.close()
        
        return dms
    
    def get_all_people(self):
        """Get all people in database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('SELECT * FROM people ORDER BY last_contacted')
        people = c.fetchall()
        conn.close()
        
        return people
    
    def save_daily_suggestion(self, person_id, suggested_message, confidence_score):
        """Save daily suggestion from agent"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''INSERT INTO daily_suggestions 
                     (person_id, suggested_message, confidence_score)
                     VALUES (?, ?, ?)''',
                  (person_id, suggested_message, confidence_score))
        
        conn.commit()
        conn.close()


if __name__ == "__main__":
    db = LinkedInDatabase()
    print("Database initialized successfully!")
