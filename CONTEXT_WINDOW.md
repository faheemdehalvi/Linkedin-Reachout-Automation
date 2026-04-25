# Context Window Handoff

## Goal
Build a LinkedIn outreach system for Faheem that:
- learns from 10-15 older DMs
- stores context for each person in Supabase
- suggests who to message and what to say
- can be used daily
- can be exposed through Antigravity MCP in VS Code

## Current State
The LinkedIn automation project already exists in this folder and includes:
- `agent.py` - outreach agent and message generation logic
- `supabase_database.py` - Supabase CRUD layer
- `config.py` - Supabase URL and anon key already set
- `daily_agent.py` - CLI for daily suggestions
- `setup_data.py` - interactive or JSON data loader
- `faheem_voice.py` - voice/profile analysis
- `faheem_reference_dms.json` - 15 reference DMs and example people
- `load_faheem_voice.py` - loader for the reference DM dataset
- `README.md`, `QUICKSTART.md`, `database_setup.sql`

## Voice Profile Captured
Faheem's outreach style is now documented as:
- "data -> actionable signals" positioning
- curious builder tone
- specific reference to the person's work
- early-stage, humble, problem-focused framing
- asks for their perspective instead of hard selling
- casual but respectful, sometimes light emoji usage

## MCP Work Started
A local MCP server wrapper was added:
- `linkedin_mcp_server.py`

It exposes tools for:
- getting the voice profile
- loading reference DMs from file
- importing example people
- listing people
- generating daily suggestions
- marking a person as contacted

## Antigravity Docs Findings
From https://antigravity.google/docs/mcp:
- custom MCP servers are configured in `~/.gemini/antigravity/mcp_config.json`
- a server can use `command` + `args` for stdio transport
- Antigravity can also connect to remote MCP servers via `serverUrl`
- auth options include Google ADC, OAuth, and custom headers

## Important Note
The Antigravity config file and environment setup were not completed because the tool call was cancelled mid-step. Nothing was broken, but these next steps are still needed.

## What Still Needs To Be Done
1. Finish writing `C:\Users\Faheem\.gemini\antigravity\mcp_config.json`
2. Make sure the Python environment has the MCP package installed
3. Verify `linkedin_mcp_server.py` runs cleanly
4. Open Antigravity / VS Code and confirm the server shows up
5. Optionally load the reference data by running `load_faheem_voice.py`

## Recommended Next Step
Wire Antigravity to the local server with a config like:

```json
{
  "mcpServers": {
    "faheem-linkedin-automation": {
      "command": "python",
      "args": ["c:\\Users\\Faheem\\faheems crazy conspiracy theories\\linkedin automation\\linkedin_mcp_server.py"],
      "cwd": "c:\\Users\\Faheem\\faheems crazy conspiracy theories\\linkedin automation"
    }
  }
}
```

## Useful Files
- `agent.py`
- `supabase_database.py`
- `linkedin_mcp_server.py`
- `faheem_voice.py`
- `faheem_reference_dms.json`
- `load_faheem_voice.py`
- `CONTEXT_WINDOW.md`

## Practical Handoff Summary
The project is in a good shape for an Antigravity MCP setup. The app logic and voice model are already in place. The last mile is just installing the MCP runtime and registering the local server in Antigravity's config file.
