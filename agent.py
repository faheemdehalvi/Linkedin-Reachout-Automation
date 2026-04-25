"""
LinkedIn Automation Agent
Analyzes reference DMs, learns patterns, and suggests daily outreach
Powered by Faheem's authentic voice and outreach philosophy
"""
import json
from supabase_database import SupabaseLinkedInDatabase
from config import OPENAI_API_KEY
from faheem_voice import FAHEEM_VOICE_PROFILE, TARGET_PATTERNS

class LinkedInAgent:
    def __init__(self):
        self.db = SupabaseLinkedInDatabase()
        self.voice_profile = FAHEEM_VOICE_PROFILE
        
        self.system_prompt = """You are Faheem's LinkedIn outreach agent. 
Your job is to generate personalized messages that sound authentic to Faheem's voice.

Key principles:
1. Reference their SPECIFIC work - not generic praise
2. Connect Faheem's data→signals expertise to THEIR world specifically
3. Ask genuine questions about their problems, don't pitch features
4. Keep it concise, curious, respectful
5. Use phrases like: "curious builder", "still early", "would love to hear how you think about"
6. Avoid being salesy - focus on learning and value exchange

Message structure:
- Line 1: Reference their specific work (company/post/role)
- Line 2-3: Explain what Faheem builds (tailored to their industry)
- Line 4: Ask a genuine question about their world
- Closing: Casual, warm, no hard sell

Examples of good openers:
- "Saw your work at [company] around [specific thing]—really interesting"
- "Your point about [specific thing] really resonated with me"
- "I noticed you're thinking about [X], I've been exploring something adjacent"

Examples of good questions:
- "How do you think about [their problem]?"
- "What's actually made these systems useful for your team?"
- "Would love to hear your take on..."
- "Curious how you approach [their domain problem]?"

Tone: Genuine. Curious. Early-stage. Problem-focused not product-focused.
"""
    
    def analyze_reference_dms(self):
        """Analyze all reference DMs to extract patterns"""
        reference_dms = self.db.get_reference_dms()
        
        if not reference_dms:
            return None
        
        # Parse reference DMs into readable format
        dm_analysis = {
            "total_dms": len(reference_dms),
            "dms": []
        }
        
        for dm in reference_dms:
            dm_analysis["dms"].append({
                "recipient_name": dm[1],
                "recipient_title": dm[2],
                "recipient_company": dm[3],
                "message": dm[4],
                "context": dm[5],
                "success_indicator": dm[6]
            })
        
        return dm_analysis
    
    def generate_daily_suggestions(self, num_suggestions=5):
        """Generate daily suggestions for who to contact and what to say"""
        people = self.db.get_all_people()
        reference_dms = self.analyze_reference_dms()
        
        if not people:
            print("⚠ No people in database. Add some first!")
            return []
        
        if not reference_dms:
            print("⚠ No reference DMs. Add some successful DMs first!")
            return []
        
        suggestions = []
        
        # Simple pattern matching (without external API for now)
        for person in people[:num_suggestions]:
            person_id, profile_id, name, title, company, industry, traits, interests, last_contacted, contact_count, notes, _, _ = person
            
            # Find similar people in reference DMs
            matching_dm = self._find_similar_reference_dm(title, company, industry, reference_dms)
            
            if matching_dm:
                personalized_msg = self._personalize_message(
                    matching_dm["message"],
                    name,
                    title,
                    company,
                    interests,
                    traits
                )
                
                confidence = self._calculate_confidence(person, matching_dm, reference_dms)
                
                suggestions.append({
                    "person_id": person_id,
                    "name": name,
                    "title": title,
                    "company": company,
                    "suggested_message": personalized_msg,
                    "confidence_score": confidence,
                    "reasoning": f"Matched with successful pattern from {matching_dm['recipient_name']}"
                })
                
                # Save to database
                self.db.save_daily_suggestion(person_id, personalized_msg, confidence)
        
        return suggestions
    
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
    
    def _personalize_message(self, base_message, name, title, company, interests, traits):
        """Personalize a message template for specific person using Faheem's voice"""
        
        # Generate personalized message in Faheem's style
        if title:
            title_lower = title.lower()
            
            # Different hooks for different roles
            if any(word in title_lower for word in ['product', 'pm', 'manager']):
                hook = f"Your work on identifying what actually drives traction really resonated"
            elif any(word in title_lower for word in ['analyst', 'analytics', 'data', 'insights']):
                hook = f"Your approach to turning data into signals caught my eye"
            elif any(word in title_lower for word in ['founder', 'ceo', 'co-founder']):
                hook = f"What you're building at {company} is really interesting—especially around"
            elif any(word in title_lower for word in ['growth', 'lead', 'head']):
                hook = f"Following your work on {company}'s growth strategy"
            else:
                hook = f"Came across your profile at {company}"
        else:
            hook = f"Came across you at {company}"
        
        # Core Faheem pitch adapted to their role
        faheem_pitch = f"""I've been exploring how to turn raw data into clear actionable signals—segmentation, pattern detection, what's actually changing in workflows vs noise.

Still early, but it feels relevant to problems in [{title or 'your domain'}]."""
        
        # Generate personalized question based on their role
        if title:
            if any(word in title_lower for word in ['operations', 'ops']):
                question = "Curious what's the biggest friction point you see day-to-day that's hard to surface or automate?"
            elif any(word in title_lower for word in ['analytics', 'data', 'insights']):
                question = "Would love to hear what usually makes your signals strong enough to actually act on?"
            elif any(word in title_lower for word in ['product']):
                question = "How do you currently think about identifying what to double down on vs what's noise?"
            elif any(word in title_lower for word in ['growth']):
                question = "What usually gets in the way of surfacing patterns before they become obvious?"
            else:
                question = f"Would be really interested in how you're thinking about this in your world?"
        else:
            question = "Would love to hear your perspective on this."
        
        # Construct message in Faheem's voice
        message = f"Hi {name},\n\n{hook}.\n\n{faheem_pitch}\n\n{question}\n\nThanks,\nFaheem"
        
        # Add personality traits reference if available and strong
        if interests and len(interests) > 3:
            message += f"\n\n(I saw you're into {interests}—that's exactly the kind of domain knowledge that helps here)"
        
        return message
    
    def _calculate_confidence(self, person, matching_dm, reference_dms):
        """Calculate confidence score for a suggestion"""
        score = 0.7  # Base score
        
        # Adjust based on contact history
        _, _, _, _, _, _, _, _, _, contact_count, _, _, _ = person
        if contact_count < 3:
            score += 0.1
        
        # Adjust based on success indicator
        if matching_dm.get("success_indicator"):
            score += 0.1
        
        return min(score, 1.0)  # Cap at 1.0


if __name__ == "__main__":
    agent = LinkedInAgent()
    print("Agent initialized! Use this to generate daily suggestions.")
