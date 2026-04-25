-- LinkedIn Automation Database Setup
-- Run these commands in Supabase SQL Editor to set up all tables

-- 1. People table - stores contacts you want to reach out to
CREATE TABLE IF NOT EXISTS people (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
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
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP DEFAULT now()
);

-- 2. Reference DMs table - your successful old DMs for learning
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

-- 3. Daily suggestions table - tracks daily recommendations
CREATE TABLE IF NOT EXISTS daily_suggestions (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  date DATE DEFAULT CURRENT_DATE,
  person_id BIGINT,
  suggested_message TEXT,
  confidence_score FLOAT,
  action_taken BOOLEAN DEFAULT false,
  result TEXT,
  created_at TIMESTAMP DEFAULT now(),
  FOREIGN KEY (person_id) REFERENCES people (id)
);

-- 4. Messages table - tracks all sent/received messages
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

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_people_last_contacted ON people(last_contacted);
CREATE INDEX IF NOT EXISTS idx_daily_suggestions_date ON daily_suggestions(date);
CREATE INDEX IF NOT EXISTS idx_reference_dms_company ON reference_dms(recipient_company);
