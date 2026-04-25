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

## Kakiyo Claude Conversion Guide Integration
Reference: https://kakiyo.notion.site/claude-conversion-guide

### Key Learning: TOP 1% Sales Reps Book 2-5 Meetings/Day Using CLAUDE + KAKIYO

**Critical Sections to Implement:**
1. **Why you're not booking meetings on LinkedIn** - Diagnostic of common outreach failures
2. **The EXACT prompts booking the top 1% sales reps 2-5 meetings/day** - Specific Claude prompts that drive conversions
3. **How to teach your AI what you sell** - Context window strategy for AI personalization
4. **Test before you burn your lead list** - Validation methodology before scaling

### Strategy Insights for Faheem's System
- Prompts need to be tested on a small batch before full deployment
- AI must learn the exact positioning/value prop (what Faheem sells)
- Pattern matching from past successful DMs is the foundation (already implemented)
- Personalization + specific reference to prospect's work = higher reply rates
- Tone consistency across all messages critical for brand trust

### Integration Points
- Update `agent.py` prompts with Kakiyo-validated message structures
- Implement A/B testing framework before bulk messaging
- Add confidence scoring tied to pattern matching (already in place)
- Voice profile should emphasize specific, data-driven positioning

## Useful Files
- `agent.py`
- `supabase_database.py`
- `linkedin_mcp_server.py`
- `faheem_voice.py`
- `faheem_reference_dms.json`
- `load_faheem_voice.py`
- `CONTEXT_WINDOW.md`

## Practical Handoff Summary
The project is in a good shape for a Kakiyo-aligned LinkedIn outreach system. The core voice model and pattern matching are in place. Next phase: integrate TOP 1% sales rep prompts, implement testing framework before scaling, and validate conversion methodology with small batch testing.
