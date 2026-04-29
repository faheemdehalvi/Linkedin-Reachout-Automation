"""
LinkedIn Automation Agent
Analyzes reference DMs, learns patterns, and suggests daily outreach
Powered by Faheem's authentic voice and outreach philosophy

Features:
1. 25 connection text recommendations
2. 25 personally curated text matching
3. Context window builder (per-person AI reasoning)
4. 25 connection request recommendations
"""
import json
import concurrent.futures
from openai import OpenAI
from supabase_database import SupabaseLinkedInDatabase
from config import (
    OPENAI_API_KEY, OPENROUTER_API_KEY, OPENROUTER_MODEL,
    MAX_CONNECTION_TEXTS, MAX_CONNECTION_REQUESTS, MAX_CURATED_TEXTS
)
from faheem_voice import FAHEEM_VOICE_PROFILE, TARGET_PATTERNS
from web_search import get_company_context

class LinkedInAgent:
    def __init__(self):
        self.db = SupabaseLinkedInDatabase()
        self.voice_profile = FAHEEM_VOICE_PROFILE
        
        self.llm_client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY if OPENROUTER_API_KEY and OPENROUTER_API_KEY != "your-openrouter-key" else "dummy-key"
        )
        self.model = OPENROUTER_MODEL
        
        # System prompt for connection texts (existing connections)
        self.system_prompt_connection = """You are ghostwriting LinkedIn DMs as Faheem Dehalvi. 
Your job is to replicate HOW FAHEEM ACTUALLY TEXTS — not how an AI writes.

CRITICAL INSTRUCTION: NEVER use words like "delve", "synergy", "navigate", "testament", "impressive", "dynamic", "transformative", "elevate", "innovative", or other common AI buzzwords. Write like a human in their early 20s. Do NOT use overly formal or corporate phrasing.

STUDY THESE REAL EXAMPLES FROM FAHEEM (this is exactly how he types):

EXAMPLE 1 (Professional/Senior):
"Came across your work at Fever and Dice, really interesting space especially around scaling partnerships and experiences.
I have been exploring how data can be used to understand which events, audiences, and partnerships actually drive the most traction, turning raw engagement data into clearer signals on what to double down on.
Still early, but it feels relevant to partnership and growth decisions in experience led platforms.
Would love to hear how you currently think about identifying high performing partnerships.
Thanks,
Faheem"

EXAMPLE 2 (Casual Peer):
"Heyy Heera,
Hows it going, I see youre working as a Senior VC Coordinator. Actually im into the same field and work with data as a free lance data scientist how has done multiple realtime impact projects I was interested to know how you came across this opportunity and what youve been upto these days.
Pls hit me back 
Regards 
Faheem Dehalvi"

EXAMPLE 3 (Tech Peer):
"Hey Hey Rye,
I was at the last Claude Code meetup at stone and chalk
I'm jus a curious student and a builder.
Imagine Raw data converted to insights automatically
I'm building a budget-aware autonomous data processing pipeline.
It segments data, runs deterministic transforms, and only escalates to AI when a decision boundary is reached.
Net effect: lower token cost + more controlled decision-making.
Would appreciate your thoughts on where this kind of system could be applied
Thankyou so much for the read 😊
Regards
Faheem Dehalvi"

RULES — THESE ARE NON-NEGOTIABLE:
1. Sound EXACTLY like Faheem. He types casually. Do not use perfect grammar. Use abbreviations occasionally (im, jus, uk, ofc, pls, heyy).
2. NEVER use AI cliches ("I hope this message finds you well", "I wanted to reach out", "I was impressed by").
3. His core pitch is usually: "im building an ML pipeline that converts raw data to properly segmented and sensible insight" or "turning raw data into clearer signals".
4. Use his phrases: "curious builder", "still early", "raw data to clear signals", "would love to hear how you think about", "I've been exploring", "really interesting space".
5. Sign off with: "Thanks,\\nFaheem" or "Regards\\nFaheem Dehalvi".
6. Reference SPECIFIC things about their work/company based on the context, but don't force it unnaturally.
7. Always end with a GENUINE question about their experience.
8. Keep it 3-4 short paragraphs MAX. Mobile-friendly spacing (double newlines).
9. Output ONLY the message. No "Here's the message:" or any meta-text.
"""
        
        # System prompt for connection requests (new prospects)
        self.system_prompt_request = """You are ghostwriting LinkedIn connection request notes as Faheem Dehalvi.
These must be UNDER 300 characters and sound like Faheem actually types. DO NOT sound like an AI.

CRITICAL INSTRUCTION: NEVER use words like "delve", "synergy", "navigate", "impressive profile", "dynamic", "keen to connect" or other common AI buzzwords. Write like a human.

REAL EXAMPLES FROM FAHEEM:
- "Heyy [name], I'm a curious builder i am building a ML pipeline that converts raw data to properly segmented and sensible insight. id love feedback on it. Regards Faheem Dehalvi"
- "Came across your work at [company], really interesting space. I've been exploring how data can turn into clearer signals. Would love to connect."
- "Hey, im an RMIT student (ex-NVIDIA) building in data/analytics. Your work at [company] caught my eye — would love to connect and exchange thoughts."

RULES:
1. Sound like Faheem — casual, real, not corporate. Occasional lowercase ("im", "jus").
2. DO NOT use AI cliches. Keep it extremely conversational and direct.
3. Mention ONE specific thing about their work/company.
4. Say what you're building: "ML pipeline", "raw data to insights", "curious builder", "turning raw data into signals".
5. Start with "Hey [name]" or "Heyy [name]" or "Hi [name]".
6. NO pitch, NO selling. Just genuine connection.
7. UNDER 300 characters total. Ultra-brief.
8. Output ONLY the note text. Nothing else.
"""
    
    # ─────────────────────────────────────────────
    # Feature #1: 25 Connection Text Recommendations
    # ─────────────────────────────────────────────
    
    def generate_connection_texts(self, num_suggestions=25):
        """Generate personalized texts for existing connections"""
        return self._generate_suggestions(
            num_suggestions=num_suggestions,
            connection_status="connection",
            suggestion_type="connection_text",
            system_prompt=self.system_prompt_connection
        )
    
    # ─────────────────────────────────────────────
    # Feature #2: 25 Personally Curated Texts
    # ─────────────────────────────────────────────
    
    def get_curated_suggestions(self, num_suggestions=25):
        """Match curated text templates to people based on industry/role"""
        curated_texts = self.db.get_curated_texts(active_only=True)
        people = self.db.get_all_people(connection_status="connection")
        
        if not curated_texts:
            return {"curated_texts": [], "matched_suggestions": [], "message": "No curated texts found. Add some from the UI."}
        
        if not people:
            return {"curated_texts": curated_texts, "matched_suggestions": [], "message": "No connections in database to match."}
        
        # Match curated texts to people
        matched = []
        for text in curated_texts[:num_suggestions]:
            # Find best matching person based on industry/role
            best_match = self._match_curated_to_person(text, people)
            if best_match:
                matched.append({
                    "curated_text_id": text.get('id'),
                    "template_title": text.get('title'),
                    "template_message": text.get('message_template'),
                    "target_industry": text.get('target_industry', ''),
                    "target_role": text.get('target_role', ''),
                    "tags": text.get('tags', ''),
                    "usage_count": text.get('usage_count', 0),
                    "matched_person": {
                        "person_id": best_match.get('id'),
                        "name": best_match.get('name'),
                        "title": best_match.get('title'),
                        "company": best_match.get('company'),
                        "industry": best_match.get('industry')
                    }
                })
        
        return {
            "curated_texts": curated_texts,
            "matched_suggestions": matched,
            "total_templates": len(curated_texts),
            "total_matched": len(matched)
        }
    
    def _match_curated_to_person(self, curated_text, people):
        """Find the best person match for a curated text template"""
        target_industry = (curated_text.get('target_industry') or '').lower()
        target_role = (curated_text.get('target_role') or '').lower()
        
        best_match = None
        best_score = 0
        
        for person in people:
            score = 0
            person_industry = (person.get('industry') or '').lower()
            person_title = (person.get('title') or '').lower()
            
            # Industry match
            if target_industry and person_industry:
                if target_industry in person_industry or person_industry in target_industry:
                    score += 3
                elif any(word in person_industry for word in target_industry.split()):
                    score += 1
            
            # Role match
            if target_role and person_title:
                if target_role in person_title or person_title in target_role:
                    score += 3
                elif any(word in person_title for word in target_role.split()):
                    score += 1
            
            # Prefer people not recently contacted
            if not person.get('last_contacted'):
                score += 1
            
            if score > best_score:
                best_score = score
                best_match = person
        
        # Return first person if no good match found
        return best_match or (people[0] if people else None)
    
    # ─────────────────────────────────────────────
    # Feature #3: Context Window Builder
    # ─────────────────────────────────────────────
    
    def build_context_window(self, person_id, suggestion_id, person_data, web_context, matched_dm, confidence, connection_type="connection"):
        """Build and persist the full AI reasoning context for a suggestion"""
        reasoning_chain = {
            "step_1_person_analysis": {
                "name": person_data.get('name'),
                "title": person_data.get('title'),
                "company": person_data.get('company'),
                "industry": person_data.get('industry'),
                "traits": person_data.get('personality_traits', ''),
                "interests": person_data.get('interests', ''),
                "contact_history": {
                    "total_contacts": person_data.get('contact_count', 0),
                    "last_contacted": person_data.get('last_contacted')
                }
            },
            "step_2_pattern_matching": {
                "matched_reference_dm": matched_dm.get('recipient_name') if matched_dm else None,
                "matched_context": matched_dm.get('context') if matched_dm else None,
                "success_indicator": matched_dm.get('success_indicator') if matched_dm else None,
                "match_reason": f"Title/industry alignment with {matched_dm.get('recipient_name')}'s profile" if matched_dm else "No match found"
            },
            "step_3_voice_alignment": {
                "core_themes_used": self.voice_profile.get('core_themes', [])[:3],
                "tone_applied": self.voice_profile.get('tone', {}).get('authenticity', 'Genuine'),
                "key_phrases_available": self.voice_profile.get('key_phrases', [])[:4]
            },
            "step_4_decision": {
                "confidence_score": confidence,
                "connection_type": connection_type,
                "why_this_person": self._generate_why_this_person(person_data, matched_dm)
            }
        }
        
        web_research = {
            "raw_context": web_context,
            "company": person_data.get('company'),
            "search_performed": bool(web_context),
            "timestamp": __import__('datetime').datetime.utcnow().isoformat()
        }
        
        matched_pattern = matched_dm.get('recipient_name', 'none') if matched_dm else 'none'
        voice_score = self._calculate_voice_alignment(person_data)
        
        # Persist to Supabase
        context = self.db.save_context_window(
            person_id=person_id,
            suggestion_id=suggestion_id,
            reasoning_chain=reasoning_chain,
            web_research=web_research,
            matched_pattern=matched_pattern,
            voice_alignment_score=voice_score,
            connection_type=connection_type
        )
        
        return context
    
    def _generate_why_this_person(self, person_data, matched_dm):
        """Generate a human-readable reason for targeting this person"""
        reasons = []
        
        title = person_data.get('title', '')
        company = person_data.get('company', '')
        industry = person_data.get('industry', '')
        contact_count = person_data.get('contact_count', 0)
        
        if title:
            for role in TARGET_PATTERNS.get('best_fit', []):
                if any(word.lower() in title.lower() for word in role.split()):
                    reasons.append(f"Role '{title}' fits target profile: {role}")
                    break
        
        if company:
            reasons.append(f"At {company} — relevant company in focus area")
        
        if contact_count == 0:
            reasons.append("Never contacted — fresh opportunity")
        elif contact_count < 3:
            reasons.append(f"Low contact count ({contact_count}) — room to build relationship")
        
        if matched_dm:
            reasons.append(f"Pattern match with successful DM to {matched_dm.get('recipient_name', 'unknown')}")
        
        return " | ".join(reasons) if reasons else "General outreach candidate"
    
    def _calculate_voice_alignment(self, person_data):
        """Calculate how well this person fits Faheem's voice/approach"""
        score = 0.6  # Base
        
        title = (person_data.get('title') or '').lower()
        interests = (person_data.get('interests') or '').lower()
        
        # Check against best-fit roles
        for role in TARGET_PATTERNS.get('best_fit', []):
            if any(word.lower() in title for word in role.split()):
                score += 0.15
                break
        
        # Check for theme alignment
        for theme in self.voice_profile.get('core_themes', []):
            theme_words = theme.lower().split()
            if any(word in interests for word in theme_words if len(word) > 3):
                score += 0.05
        
        return min(round(score, 2), 1.0)
    
    # ─────────────────────────────────────────────
    # Feature #4: 25 Connection Request Recommendations
    # ─────────────────────────────────────────────
    
    def generate_connection_requests(self, num_suggestions=25):
        """Generate personalized connection request notes for prospects"""
        return self._generate_suggestions(
            num_suggestions=num_suggestions,
            connection_status="prospect",
            suggestion_type="connection_request",
            system_prompt=self.system_prompt_request
        )
    
    # ─────────────────────────────────────────────
    # Core Generation Engine (shared)
    # ─────────────────────────────────────────────
    
    def analyze_reference_dms(self):
        """Analyze all reference DMs to extract patterns"""
        reference_dms = self.db.get_reference_dms()
        
        if not reference_dms:
            return None
        
        dm_analysis = {
            "total_dms": len(reference_dms),
            "dms": []
        }
        
        for dm in reference_dms:
            # Supabase returns dicts
            dm_analysis["dms"].append({
                "recipient_name": dm.get('recipient_name'),
                "recipient_title": dm.get('recipient_title'),
                "recipient_company": dm.get('recipient_company'),
                "message": dm.get('message'),
                "context": dm.get('context'),
                "success_indicator": dm.get('success_indicator')
            })
        
        return dm_analysis
    
    def _generate_suggestions(self, num_suggestions, connection_status, suggestion_type, system_prompt):
        """Core suggestion generation — used by both connection texts and connection requests"""
        people = self.db.get_all_people(connection_status=connection_status)
        reference_dms = self.analyze_reference_dms()
        
        if not people:
            print(f"WARNING: No people in database with status '{connection_status}'")
            return []
        
        if not reference_dms:
            print("WARNING: No reference DMs. Add some successful DMs first!")
            return []
        
        suggestions = []
        target_people = people[:num_suggestions]
        
        def process_person(person):
            person_id = person.get('id')
            name = person.get('name')
            title = person.get('title')
            company = person.get('company')
            industry = person.get('industry')
            traits = person.get('personality_traits', '')
            interests = person.get('interests', '')
            contact_count = person.get('contact_count', 0)
            
            matching_dm = self._find_similar_reference_dm(title, company, industry, reference_dms)
            
            if matching_dm:
                context_data = self._personalize_message(
                    matching_dm["message"],
                    name, title, company, interests, traits,
                    system_prompt=system_prompt
                )
                
                confidence = self._calculate_confidence(person, matching_dm, reference_dms)
                
                # Save suggestion to DB
                suggestion_record = self.db.save_daily_suggestion(
                    person_id, context_data["message"], confidence,
                    suggestion_type=suggestion_type
                )
                suggestion_id = suggestion_record.get('id') if suggestion_record else None
                
                # Build and persist context window (Feature #3)
                context_window = None
                if suggestion_id:
                    context_window = self.build_context_window(
                        person_id=person_id,
                        suggestion_id=suggestion_id,
                        person_data=person,
                        web_context=context_data["web_context"],
                        matched_dm=matching_dm,
                        confidence=confidence,
                        connection_type="connection" if suggestion_type == "connection_text" else "prospect"
                    )
                
                return {
                    "person_id": person_id,
                    "suggestion_id": suggestion_id,
                    "name": name,
                    "title": title,
                    "company": company,
                    "industry": industry,
                    "suggested_message": context_data["message"],
                    "web_context": context_data["web_context"],
                    "confidence_score": confidence,
                    "suggestion_type": suggestion_type,
                    "reasoning": f"Matched with successful pattern from {matching_dm['recipient_name']}",
                    "context_window_id": context_window.get('id') if context_window else None
                }
            return None

        # Process all people concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(process_person, target_people))
            
        for r in results:
            if r:
                suggestions.append(r)
                
        return suggestions
    
    def generate_daily_suggestions(self, num_suggestions=5, connection_status="connection"):
        """Legacy method for backward compatibility"""
        suggestion_type = "connection_text" if connection_status == "connection" else "connection_request"
        system_prompt = self.system_prompt_connection if connection_status == "connection" else self.system_prompt_request
        return self._generate_suggestions(
            num_suggestions=num_suggestions,
            connection_status=connection_status,
            suggestion_type=suggestion_type,
            system_prompt=system_prompt
        )
    
    def _find_similar_reference_dm(self, title, company, industry, reference_dms):
        """Find a reference DM from someone with similar profile"""
        for dm in reference_dms["dms"]:
            # Simple matching - can be enhanced
            title_match = title and dm["recipient_title"] and any(
                word.lower() in title.lower() for word in dm["recipient_title"].split()
            )
            
            if title_match or industry:
                return dm
        
        # Default to first DM if no match
        return reference_dms["dms"][0] if reference_dms["dms"] else None
    
    def _personalize_message(self, base_message, name, title, company, interests, traits, system_prompt=None):
        """Personalize a message template for specific person using Faheem's voice via OpenRouter"""
        
        # 1. Fetch web context
        web_context = get_company_context(company)
        
        # 2. Build the prompt
        user_prompt = f"""
Write a LinkedIn DM from Faheem to this person. Make it sound EXACTLY like Faheem typed it himself.
DO NOT use overly formal language, marketing jargon, or AI-like phrasing. Be human, casual, and slightly imperfect.

Person: {name}
Their Role: {title}
Their Company: {company}
Their Interests: {interests}
Their Traits: {traits}

Web context about their company (use this to personalize, but don't just repeat it back to them):
{web_context}

Reference pattern (match this TONE and STYLE, not the exact words):
{base_message}

IMPORTANT:
- Sound like a real person texting, NOT like an AI.
- NEVER use words like "delve", "transformative", "impressive", "eager", "testament", "synergy", "dynamic", "elevate".
- Use Faheem's casual style: abbreviations, lowercase where appropriate, conversational flow.
- Reference their specific work at {company}.
- Mention what Faheem is building (raw data → insights, ML pipeline, segmentation).
- End with a genuine question about their experience.
- Output ONLY the message. Nothing else.
"""
        try:
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt or self.system_prompt_connection},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=250,
                temperature=0.7
            )
            return {"message": response.choices[0].message.content.strip(), "web_context": web_context}
        except Exception as e:
            print(f"LLM generation failed: {e}")
            # Fallback in Faheem's actual voice
            fallback = f"Heyy {name},\n\nCame across your work at {company}, really interesting space.\n\nIm a curious builder, been exploring how raw data can be turned into properly segmented insights and clear signals — segmentation, pattern detection, whats actually changing vs noise.\n\nStill early but it feels relevant to what youre doing in {title or 'your domain'}.\n\nWould love to hear how you think about this in your world?\n\nThanks,\nFaheem"
            return {"message": fallback, "web_context": web_context}
    
    def _calculate_confidence(self, person, matching_dm, reference_dms):
        """Calculate confidence score for a suggestion"""
        score = 0.7  # Base score
        
        # person is a dict (Supabase)
        contact_count = person.get('contact_count', 0) if isinstance(person, dict) else 0
        if contact_count < 3:
            score += 0.1
        
        # Adjust based on success indicator
        if matching_dm.get("success_indicator") == "SUCCESS":
            score += 0.15
        elif matching_dm.get("success_indicator") == "ENGAGEMENT":
            score += 0.1
        elif matching_dm.get("success_indicator"):
            score += 0.05
        
        return min(round(score, 2), 1.0)


if __name__ == "__main__":
    agent = LinkedInAgent()
    print("Agent initialized! Use this to generate daily suggestions.")
