# 🚀 Quick Start Guide

## Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

## Step 2: Set Up Supabase Tables

1. Go to [supabase.com](https://supabase.com) and log in
2. Create a new project if you don't have one (or use existing)
3. Go to **SQL Editor** and paste the contents of `database_setup.sql`
4. Run the SQL to create all tables

## Step 3: Verify Configuration

Check that your credentials in `config.py` are correct:
```python
SUPABASE_URL = "https://rschzmdnqfmorvuzzpva.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

These are already set for you!

## Step 4: Add Your Data

### Option A: Use the example data to test
```bash
python setup_data.py
# Select option 2, then provide: example_data.json
```

### Option B: Add your own DMs
```bash
python setup_data.py
# Select option 1 for interactive mode
# Add your 10-15 successful DMs
# Add people you want to contact
```

## Step 5: Run Daily Agent
```bash
python daily_agent.py
```

You should see:
- 5 suggested people to contact
- Personalized messages for each
- Confidence scores
- Interactive menu to mark as contacted

## 📋 What to Prepare

Have ready:
- **10-15 successful DMs** you've sent (copy the text)
- **List of people** you want to reach out to
  - Their name, title, company
  - Their interests or specialty
  - Industry they work in

## 💡 Pro Tips

1. **Start with example data**: Run the demo first to see how it works
2. **Be specific**: The more details you add, the better suggestions
3. **Track success**: Note which DMs got responses
4. **Run daily**: Best results when you check daily suggestions
5. **Refine messages**: The suggested messages are templates - personalize further!

## 📞 Next Steps

- Once you have data loaded, run `daily_agent.py` every morning
- It will suggest 5 people to contact
- You can mark people as contacted to move them to the bottom
- The system learns your style from your reference DMs

## ⚙️ Files Overview

- `config.py` - Configuration and API keys
- `supabase_database.py` - Database operations
- `agent.py` - Intelligence & suggestion generation
- `daily_agent.py` - Daily CLI tool (run this!)
- `setup_data.py` - Load your DMs and people
- `database_setup.sql` - Create tables in Supabase

**Ready? Start with:** `python setup_data.py`
