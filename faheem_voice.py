"""
Faheem's LinkedIn Voice & Patterns
Analysis of successful outreach strategy
"""

FAHEEM_VOICE_PROFILE = {
    "core_themes": [
        "Converting raw data into actionable signals",
        "ML pipelines for real-world problems",
        "Pattern detection and segmentation",
        "Automation vs. manual processes",
        "Understanding systems and how they actually work",
    ],
    
    "tone": {
        "authenticity": "Genuine and curious, not salesy",
        "stage": "Always positions as early-stage, learning",
        "confidence": "High on problems, humble on solutions",
        "formality": "Adjusts to person - casual for peers, respectful for mentors",
        "personality": "Uses emojis sparingly, authentic reactions (🥲 😅 🥳)",
    },
    
    "opening_patterns": [
        "Reference specific work/company/post they've done",
        "Explain what you're building (data→insights, not product pitch)",
        "Connect it to *their* world (not generic)",
        "Ask a genuine question or propose real conversation",
    ],
    
    "pitch_structure": {
        "step_1": "Acknowledge their specific work (not generic praise)",
        "step_2": "Explain the problem you're solving (data to signals)",
        "step_3": "Show how it connects to *their* domain",
        "step_4": "Ask for perspective or offer value (ask don't sell)",
    },
    
    "successful_hooks": [
        "How do you think about identifying X?",
        "Would love to hear your take on...",
        "Curious if you run into this problem...",
        "Would be really interested to hear how you think about...",
        "What usually makes these systems actually useful?",
    ],
    
    "what_worked": {
        "with_heera": "Listened to her setup, pivoted to automation angle with real empathy",
        "with_ayodeji": "Shared concrete demo, casual friendly tone, got call",
        "with_simon": "Listed specific industry applications, showed flexibility",
        "with_rye": "Clear explanation of cost-efficiency + AI framing",
        "with_athy": "Asked questions about what makes systems *actually used* not just built",
    },
    
    "red_flags_to_avoid": [
        "Generic praise ('love what you're doing')",
        "Immediate ask for intro/demo",
        "Selling features not solving problems",
        "Not showing you understand their specific role",
        "Being too formal or stiff",
    ],
    
    "key_phrases": [
        "curious builder",
        "still early",
        "turning raw data into clear signals",
        "what actually makes [X] useful",
        "would love to hear how you think about",
        "I've been exploring",
        "feels aligned with",
        "convert raw data to insights",
    ],
    
    "signature_elements": [
        "Always personalize to their specific role/company",
        "Show you've done research (specific references)",
        "Position as learning/exploring not selling",
        "Ask questions that show genuine curiosity",
        "Offer perspective or value not just pitch",
        "Keep it concise but thoughtful",
    ],
}

# Real conversation examples that succeeded
SUCCESSFUL_PATTERNS = [
    {
        "recipient": "Heera",
        "why_it_worked": "Initial pitch was too generic, but Faheem listened, understood her setup, then pivoted to automation angle with empathy. She saw he understood her world.",
        "key_moment": "Acknowledged her PowerBI setup was solid, then explained a *different* value prop (automation vs reporting)",
    },
    {
        "recipient": "Ayodeji",
        "why_it_worked": "Specific reference to Mirrorly framing, shared concrete demo, casual/friendly tone, clear ask for call",
        "key_moment": "Got response within minutes, scheduled call, conversation felt natural not transactional",
    },
    {
        "recipient": "Athy",
        "why_it_worked": "Asked hard questions about what makes systems useful, listened to feedback about building in context",
        "key_moment": "Showed willingness to learn and adjust thinking based on feedback",
    },
]

# Industries/roles Faheem successfully reached
TARGET_PATTERNS = {
    "best_fit": [
        "Product Managers", "Growth/Analytics roles", "Founders", "ML/Data specialists",
        "Operations/Systems thinking roles"
    ],
    "hook_angles": {
        "Product_Manager": "How do you think about identifying what actually drives traction?",
        "Analytics": "What makes your signals strong enough to act on?",
        "Founder": "How do you turn raw business data into growth decisions?",
        "Growth": "How do you surface patterns before they become obvious?",
        "Operations": "What's causing friction in your workflows that's hard to see?",
    },
}
