# LinkedIn Automation AI Agent 🤖✨

**Automate, personalize, and scale your LinkedIn outreach with an LLM‑powered assistant.**  
This repository contains a production‑ready Python application that:

- 🔎 **Researches** target profiles in real‑time via web search.  
- 🧠 **Generates** custom connection request messages and follow‑up texts using a large language model, complete with a transparent “reasoning window”.  
- 📊 **Tracks** every interaction (sent, accepted, replied) in a Supabase database.  
- 📂 **Manages** reusable message templates and AI‑generated snippets through a clean, four‑panel dashboard.  
- ⚡ **Scales** to 50+ daily outreach actions with concurrent workers and robust error handling.

## 🚀 Features at a glance

| Feature | Description |
|---------|-------------|
| **Dynamic Prospect Research** | Browser‑less web‑search module (`web_search.py`) pulls current headlines, recent posts, and company info. |
| **LLM‑Generated Messaging** | `daily_agent.py` builds context windows with AI reasoning so you can audit the suggestions. |
| **Supabase Backend** | All data (templates, connection statuses, logs) stored in a PostgreSQL‑compatible Supabase schema (`database_setup.sql`). |
| **Template Management UI** | Simple HTML dashboard (`static/index.html`) lets you edit, preview, and version‑control message templates. |
| **Batch Scheduling** | `start_local.bat` launches the agent with optional concurrency flags. |
| **Extensible Config** | `config.py` centralises API keys, model selection, and rate‑limit settings. |

## 📦 Quick Start

```powershell
# 1️⃣ Clone the repo
git clone https://github.com/faheemdehalvi/linkedin-automation.git
cd linkedin-automation

# 2️⃣ Install dependencies (prefer a virtual env)
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

# 3️⃣ Initialise the Supabase database
psql -U your_user -d your_db -f database_setup.sql   # adjust as needed

# 4️⃣ Add your secrets to config.py (API keys, Supabase URL, etc.)

# 5️⃣ Run the agent locally
.\start_local.bat
```
