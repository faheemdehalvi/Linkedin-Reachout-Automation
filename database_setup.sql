-- =====================================================
-- STEP 1: CREATE ALL TABLES
-- Copy this ENTIRE file, paste into Supabase SQL Editor, click Run
-- =====================================================

CREATE TABLE IF NOT EXISTS people (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  linkedin_profile_id TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  title TEXT,
  company TEXT,
  industry TEXT,
  personality_traits TEXT,
  interests TEXT,
  linkedin_url TEXT,
  last_contacted DATE,
  contact_count INTEGER DEFAULT 0,
  connection_status TEXT DEFAULT 'connection',
  notes TEXT,
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS reference_dms (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  recipient_name TEXT,
  recipient_title TEXT,
  recipient_company TEXT,
  message TEXT NOT NULL,
  context TEXT,
  success_indicator TEXT,
  created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS daily_suggestions (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  date DATE DEFAULT CURRENT_DATE,
  person_id BIGINT,
  suggested_message TEXT,
  confidence_score FLOAT,
  suggestion_type TEXT DEFAULT 'connection_text',
  action_taken BOOLEAN DEFAULT false,
  send_status TEXT DEFAULT 'pending',
  sent_at TIMESTAMP,
  result TEXT,
  created_at TIMESTAMP DEFAULT now(),
  FOREIGN KEY (person_id) REFERENCES people (id)
);

CREATE TABLE IF NOT EXISTS messages (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  person_id BIGINT,
  sender TEXT,
  receiver TEXT,
  message_content TEXT NOT NULL,
  timestamp DATE,
  response_received BOOLEAN DEFAULT false,
  effectiveness_score FLOAT,
  created_at TIMESTAMP DEFAULT now(),
  FOREIGN KEY (person_id) REFERENCES people (id)
);

CREATE TABLE IF NOT EXISTS curated_texts (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  title TEXT NOT NULL,
  message_template TEXT NOT NULL,
  target_industry TEXT,
  target_role TEXT,
  tags TEXT,
  is_active BOOLEAN DEFAULT true,
  usage_count INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS context_windows (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  person_id BIGINT,
  suggestion_id BIGINT,
  reasoning_chain JSONB DEFAULT '{}',
  web_research JSONB DEFAULT '{}',
  matched_pattern TEXT,
  voice_alignment_score FLOAT,
  connection_type TEXT DEFAULT 'connection',
  created_at TIMESTAMP DEFAULT now(),
  FOREIGN KEY (person_id) REFERENCES people (id),
  FOREIGN KEY (suggestion_id) REFERENCES daily_suggestions (id)
);

-- =====================================================
-- STEP 2: ENABLE API ACCESS (this is the key part!)
-- Grant the anon role SELECT/INSERT/UPDATE/DELETE on all tables
-- =====================================================

GRANT ALL ON people TO anon, authenticated;
GRANT ALL ON reference_dms TO anon, authenticated;
GRANT ALL ON daily_suggestions TO anon, authenticated;
GRANT ALL ON messages TO anon, authenticated;
GRANT ALL ON curated_texts TO anon, authenticated;
GRANT ALL ON context_windows TO anon, authenticated;

-- Grant sequence permissions (needed for INSERT with auto-generated IDs)
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;

-- =====================================================
-- STEP 3: DISABLE RLS (Row Level Security) so anon key works
-- Without this, the API returns empty results
-- =====================================================

ALTER TABLE people ENABLE ROW LEVEL SECURITY;
ALTER TABLE reference_dms ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_suggestions ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE curated_texts ENABLE ROW LEVEL SECURITY;
ALTER TABLE context_windows ENABLE ROW LEVEL SECURITY;

-- Create permissive policies for all operations
CREATE POLICY "Allow all on people" ON people FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all on reference_dms" ON reference_dms FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all on daily_suggestions" ON daily_suggestions FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all on messages" ON messages FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all on curated_texts" ON curated_texts FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all on context_windows" ON context_windows FOR ALL USING (true) WITH CHECK (true);

-- =====================================================
-- STEP 4: VERIFY (should return table names)
-- =====================================================

SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('people', 'reference_dms', 'daily_suggestions', 'messages', 'curated_texts', 'context_windows')
ORDER BY table_name;
