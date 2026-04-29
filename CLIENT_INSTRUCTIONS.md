# LinkedIn AI Automation - Quick Start Guide

Welcome! This tool uses an AI agent to research your prospects on the web, craft highly personalized LinkedIn messages in your exact voice, and automatically send them on your behalf.

Here is how to set it up and run it every day.

## 1. First-Time Setup
*Note: You only need to do this once!*

1. **Install Dependencies**: Open your terminal/command prompt in this folder and run:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```
2. **Add API Keys**: Open the `.env` file in a text editor (like Notepad) and paste your **Supabase** and **OpenRouter** API keys. Save the file.
3. **Log Into LinkedIn**: Run the following command in your terminal:
   ```bash
   python login_linkedin.py
   ```
   A browser window will pop up. Log into your LinkedIn account. Once logged in, the script will securely save your session and close automatically. You will not need to do this again.

---

## 2. Adding Your Leads (Two Options)

### Option A: Auto-Scrape from LinkedIn (Recommended)
No spreadsheets needed! The bot will pull leads directly from your LinkedIn account.

**Scrape your existing connections:**
```bash
python scrape_leads.py --mode connections
```

**Discover new prospects by keyword search:**
```bash
python scrape_leads.py --mode prospects --query "SaaS founder"
```

**Do both at once:**
```bash
python scrape_leads.py --mode both --query "Product Manager fintech"
```

You can change the search query to anything -- "Data Engineer", "startup CEO", "marketing director healthcare", etc. The bot will search LinkedIn, extract names/titles/URLs, and save them into your database automatically.

### Option B: Upload from a Spreadsheet
If you prefer to manage a specific list manually:
1. Open the `leads.csv` file in Excel or Google Sheets.
2. Add your targets to the rows.
   - Under **`linkedin_url`**, paste their exact LinkedIn profile link.
   - Under **`connection_status`**, type `prospect` to send a Connection Request, or `connection` to send a DM.
3. Save the `leads.csv` file.
4. Run:
   ```bash
   python import_leads.py
   ```

---

## 3. Running the Automation
Once your leads are imported, it's time to let the AI do the work.

1. In your terminal, run:
   ```bash
   python auto_outreach.py --mode all
   ```
2. **Sit back and watch!** The browser will open on your screen. The AI will read your leads, research their companies on the web, generate personalized messages, and naturally type them out on LinkedIn.

*(Note: The bot uses random 30-90 second delays between actions to mimic human behavior and keep your LinkedIn account safe, so it will take a little while to process a large list!)*

---

## 4. Managing Templates & Analytics
If you want to view the AI's "reasoning" (to see exactly why it generated a specific message), or if you want to manage your personal text templates:
1. Double-click the `start_local.bat` file.
2. Open your web browser and go to `http://localhost:8000`.
