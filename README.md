# LinkedIn Automation System

An intelligent automation tool that learns from your successful past LinkedIn DMs and suggests personalized outreach to new contacts daily.

## 🎯 Features

- **Pattern Learning**: Analyzes your successful past DMs to understand your outreach style
- **Smart Suggestions**: Suggests who to contact and what to say based on context
- **Contact Management**: Tracks all your contacts and outreach history
- **Daily Agent**: Run once a day to get personalized recommendations
- **Confidence Scoring**: Each suggestion includes a confidence score for likelihood of response

## 🛠️ Setup

### Prerequisites
- Python 3.8+
- Supabase account (free tier works great)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Create Supabase Tables

Go to your Supabase dashboard and run these SQL commands:

```sql
-- People table
CREATE TABLE people (
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

-- Reference DMs table
CREATE TABLE reference_dms (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  recipient_name TEXT,
  recipient_title TEXT,
  recipient_company TEXT,
  message TEXT NOT NULL,
  context TEXT,
  success_indicator TEXT,
  created_at TIMESTAMP DEFAULT now()
);

-- Daily suggestions table
CREATE TABLE daily_suggestions (
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

-- Messages table
CREATE TABLE messages (
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
```

### 3. Add Your Data

Choose one of two ways:

#### Option A: Interactive Setup
```bash
python setup_data.py
```
Follow the prompts to add:
- Your 10-15 successful old DMs
- People you want to contact

#### Option B: Load from JSON
```bash
python setup_data.py
# Then select option 2 and provide your JSON file
```

Use `example_data.json` as a template.

## 📖 Usage

### Run Daily Agent
```bash
python daily_agent.py
```

This will:
1. Analyze your reference DMs
2. Suggest 5 people to contact today
3. Provide personalized message drafts
4. Let you mark people as contacted

### Data Format

#### Reference DMs (in JSON):
```json
{
  "recipient_name": "John Doe",
  "recipient_title": "Product Manager",
  "recipient_company": "TechCorp",
  "message": "Hi [NAME], I came across your profile and was impressed...",
  "context": "Reached out after seeing their work",
  "success_indicator": "SUCCESS"
}
```

#### People to Contact (in JSON):
```json
{
  "profile_id": "johndoe123",
  "name": "John Doe",
  "title": "Senior PM",
  "company": "MegaCorp",
  "industry": "Technology",
  "personality_traits": "Data-driven, strategic",
  "interests": "Product strategy, AI/ML",
  "notes": "Recently promoted"
}
```

## 🤖 How It Works

1. **Analysis Phase**: Agent reads all your reference DMs to understand patterns
2. **Matching Phase**: For each person in your list, finds similar past interactions
3. **Personalization Phase**: Adapts successful messages to fit the new person
4. **Scoring Phase**: Calculates confidence based on profile similarity and history
5. **Suggestion Phase**: Presents top 5 recommendations with personalized messages

## 📊 Tracking

The system tracks:
- Contact count per person
- Last contact date
- Message effectiveness
- Daily suggestions and actions taken
- Response rates

## 💡 Tips for Best Results

- Include diverse successful DMs (different industries, titles, contexts)
- Add personality traits and interests for better matching
- Mark success indicators accurately
- Run the daily agent consistently for better patterns
- Review and adjust suggestions based on actual responses

## 🚀 Daily Workflow

1. Run `python daily_agent.py` in the morning
2. Review the 5 suggested contacts and messages
3. Personalize each message further if needed
4. Send on LinkedIn
5. Mark as contacted in the agent
6. Come back tomorrow for new suggestions!

## 📝 Notes

- The agent learns better with more diverse reference DMs
- At least 5-10 successful DMs recommended for best results
- Confidence scores improve as you add more people and track responses
- Your data is stored in Supabase - you own it completely

## 🔧 Troubleshooting

**"No suggestions generated"**
- Make sure you have at least 1 reference DM added
- Make sure you have at least 1 person in the database

**"Supabase connection error"**
- Check your SUPABASE_URL and SUPABASE_ANON_KEY in config.py
- Make sure tables are created in Supabase dashboard

**Messages not personalized**
- Check that people have title/company/interests filled in
- Add more detailed reference DMs for better matching

## 📞 Support

For issues or questions, check the database structure and ensure all required fields are filled.
