# Phase 10: Humanization Module (3,500 Lines)

Complete system for making AI-generated sales messages sound genuinely human across all channels, markets, and industries.

## Overview

The Humanization module ensures >90% of messages are rated "sounds human" by users through:

- **10 Communication Tones** — Matched to market, industry, and buyer state
- **Emotion Detection** — Responds empathetically to buyer feelings
- **Deep Personalization** — Uses names, history, preferences, and context
- **Intelligent Response Building** — Combines tone + empathy + personalization
- **Continuous A/B Testing** — Optimizes humanness through experimentation

## Components

### 1. Tone Engine (600L)
**File:** `tone_engine.py`

Manages 10 distinct communication tones across markets and industries:

```python
from backend.app.core.humanization import ToneEngine, ToneType, Market, Industry

engine = ToneEngine()

# Get tone profile for a specific context
profile = engine.get_tone_profile(
    ToneType.FRIENDLY,
    Market.LATIN_AMERICA,
    Industry.ECOMMERCE,
)

# Suggest appropriate tone based on buyer state
tone = engine.suggest_tone(
    buyer_sentiment="negative",  # "positive", "neutral", "negative"
    buyer_urgency="high",        # "low", "medium", "high"
    market=Market.USA,
    industry=Industry.SAAS,
)

# Apply tone to message
result = engine.apply_tone("Hey! This is cool!", profile)
print(result["toned_message"])  # Adjusted for tone

# Measure how well text matches a tone
score = engine.measure_tone_match("Very casual message!", profile)
```

**10 Tones:**
1. **FORMAL** — Professional, structured, serious
2. **CASUAL** — Relaxed, conversational, approachable
3. **FRIENDLY** — Warm, personable, emotionally engaging
4. **PROFESSIONAL** — Business-focused, credible, expert
5. **CHEEKY** — Playful, witty, bold
6. **EDUCATIONAL** — Informative, teaching-focused
7. **URGENT** — Time-sensitive, action-oriented
8. **LUXE** — Premium, exclusive, aspirational
9. **DISCOUNT** — Value-focused, deal-oriented
10. **EMPATHETIC** — Understanding, supportive, listening

**Supported Markets:** Latin America (es_MX), Spain (es_ES), Argentina (es_AR), USA (en_US), UK (en_UK)

**Supported Industries:** Real Estate, SaaS, E-commerce, Services

### 2. Empathy Layer (400L)
**File:** `empathy_layer.py`

Detects buyer emotions and responds with appropriate empathy:

```python
from backend.app.core.humanization import EmpathyLayer, EmotionalState

layer = EmpathyLayer()

# Detect buyer emotional state
signal = layer.detect_emotion("I'm not sure about this...", language="en")
print(signal.emotional_state)  # EmotionalState.HESITANT
print(signal.confidence)        # 0.8
print(signal.urgency_level)     # 6/10

# Generate empathetic response
response = layer.generate_empathetic_response(
    signal,
    language="en",
    buyer_context={"objection": "price"},
)
print(response["response"])     # "I totally understand that concern..."
print(response["response_type"]) # "validate"
print(response["next_action"])   # "Ask clarifying questions"

# Handle specific objections
result = layer.handle_objection("It's too expensive", language="en")
print(result["response"])        # Templated objection response
print(result["objection_type"])  # "price"

# Build urgency empathetically (not pushy)
urgency = layer.build_urgency_empathetically(
    reason="limited_spots",
    language="en",
)
```

**Detected Emotional States:**
- CONFIDENT — Ready to buy
- CURIOUS — Exploring options
- HESITANT — Unsure about decision
- FRUSTRATED — Pain point triggered
- SKEPTICAL — Doubts about offer
- OBJECTING — Active resistance
- URGENT — Time pressure
- OVERWHELMED — Too many options

### 3. Personalization Engine (400L)
**File:** `personalization.py`

Personalizes messages with buyer context:

```python
from backend.app.core.humanization import (
    PersonalizationEngine,
    BuyerProfile,
    PersonalizationContext,
    PersonalizationLevel,
)

engine = PersonalizationEngine()

# Create buyer profile
profile = engine.create_buyer_profile(
    buyer_id="buyer_123",
    name="John Doe",
    company="Acme Corp",
    industry="saas",
    role="CTO",
    timezone="America/New_York",
)

# Add purchase history
profile.past_purchases = [
    {"product": "Premium Plan", "date": "2024-01-15"},
]

# Personalize message
context = PersonalizationContext(
    buyer_profile=profile,
    message_type="follow_up",
    personalization_level=PersonalizationLevel.DEEP,
)

result = engine.personalize_message(
    "Check out our new features",
    profile,
    context,
    language="en",
)

print(result["personalized_message"])
# "John, I know you're in SaaS. Check out our new features..."

print(result["personalization_elements"])
# ["name_greeting:John", "industry_keyword:scalable", ...]

# Detect urgency from profile
urgency = engine.detect_urgency_from_profile(profile)
print(urgency)  # 1-10 scale

# Extract preferences
prefs = engine.extract_buyer_preferences(profile)
print(prefs["tone"])           # "professional"
print(prefs["content_type"])   # "short"
print(prefs["max_length"])     # 50 words
```

**Personalization Levels:**
- **MINIMAL** — No personalization
- **LIGHT** — Name only
- **MODERATE** — Name + one reference (default)
- **DEEP** — Name + history + preferences + timing

### 4. Response Builder (400L)
**File:** `response_builder.py`

Combines tone + empathy + personalization + CTA into coherent responses:

```python
from backend.app.core.humanization import ResponseBuilder, CTAType

builder = ResponseBuilder()

# Build complete response
result = builder.build_response(
    base_message="Our platform can help you close more deals",
    tone_type="friendly",
    emotional_state="curious",
    buyer_name="Alice",
    cta_type=CTAType.SOFT,
    social_proof_data={
        "count": "500",
        "percent": "85",
        "audience": "SaaS companies",
        "timeframe": "30 days",
    },
    language="en",
)

print(result["response"])          # Full ready-to-send message
print(result["humanness_score"])   # 0.0-1.0, target >0.85
print(result["cta_strength"])      # 0.0-1.0 (how pushy)
print(result["components"])        # {"intro": ..., "body": ..., "cta": ..., "closing": ...}

# Validate response before sending
validation = builder.validate_response(
    response="Hey! Check this out...",
    tone="casual",
    language="en",
)

if validation["is_valid"]:
    print("Ready to send!")
else:
    print("Issues:", validation["issues"])
    print("Warnings:", validation["warnings"])

# Optimize for specific platform
optimized = builder.optimize_for_platform(
    response=result["response"],
    platform="whatsapp",  # email, sms, instagram
    language="en",
)
print(optimized["optimized_response"])
```

**CTA Types:**
- SOFT — "What do you think?" (0.2 pushiness)
- DIRECT — "Click here" (0.6 pushiness)
- SCARCITY — "Only X left" (0.8 pushiness)
- BENEFIT — "Save 10 hours/week" (0.5 pushiness)
- FEAR_OF_MISSING — "Don't miss out" (0.75 pushiness)
- CURIOSITY — "See what others found" (0.5 pushiness)

### 5. A/B Testing Engine (300L)
**File:** `a_b_testing.py`

Tests tone variations to optimize humanness:

```python
from backend.app.core.humanization import ABTestingEngine, ExperimentType

engine = ABTestingEngine()

# Create A/B test
test = engine.create_test(
    test_name="Tone Test",
    test_type=ExperimentType.TONE,
    control_message="Hey, check out our new feature",
    treatment_messages=[
        {
            "name": "Formal Tone",
            "message": "We'd like to present our new feature",
            "tone": "professional",
        },
        {
            "name": "Casual Tone",
            "message": "Just launched something awesome you might love",
            "tone": "casual",
        },
    ],
    hypothesis="Casual tone converts better than formal",
    duration_days=7,
)

# Select variant for each message (splits traffic)
variant = engine.select_variant(test.test_id)
print(f"Using variant: {variant.name}")

# Send message using this variant
# ... send message ...

# Record events as they happen
engine.record_event(test.test_id, variant.variant_id, "sent")
# Later...
engine.record_event(test.test_id, variant.variant_id, "opened")
engine.record_event(test.test_id, variant.variant_id, "clicked")
engine.record_event(test.test_id, variant.variant_id, "converted")

# Record humanness feedback from users
engine.record_humanness_feedback(
    test.test_id,
    variant.variant_id,
    score=0.92,  # 0-1 scale
)

# Analyze test results
analysis = engine.analyze_test(test.test_id)
print(f"Status: {analysis['status']}")  # "active", "inconclusive", "winner_found"
print(f"Recommendation: {analysis['recommendation']}")
print(f"Confidence: {analysis['confidence_level']}")

for variant_stat in analysis["variants"]:
    print(f"{variant_stat['name']}: {variant_stat['conversion_rate']:.1%}")

# Create test from preset
preset_test = engine.create_preset_test(
    preset_name="formal_vs_casual",
    control_message="Your message here",
)

# Or preset CTA test
cta_test = engine.create_preset_test(
    preset_name="soft_vs_direct_cta",
    control_message="Your message here",
)
```

**Experiment Types:** TONE, CTA, PERSONALIZATION, EMOJI, LENGTH, TIMING, HUMANNESS

## Integration Example

```python
from backend.app.core.humanization import (
    HumanizationOrchestrator,
    Market,
    Industry,
)

# Initialize orchestrator (combines all systems)
humanizer = HumanizationOrchestrator()

# Build human message
response = humanizer.build_human_message(
    base_message="Our product can help you grow",
    buyer_profile=buyer,  # BuyerProfile instance
    market=Market.USA,
    industry=Industry.SAAS,
    language="en",
)

print(f"Message: {response['response']}")
print(f"Humanness: {response['humanness_score']:.1%}")
print(f"Ready to send: {response['is_ready_to_send']}")

# Measure humanness of any text
score = humanizer.measure_humanness(
    text="Hey! This is super cool.",
    tone="casual",
    language="en",
)
print(f"Humanness score: {score:.1%}")
```

## Humanness Scoring

The system calculates humanness (0-1) based on:

**Sentence Variety** (+0.15)
- Different sentence lengths create natural rhythm
- Avoids repetitive patterns

**Natural Language Markers** (+0.1)
- "I think", "You know", "Honestly", "Totally"
- Conversational filler words

**Contractions** (+0.1)
- "don't", "can't", "it's", "we're"
- Makes language feel natural

**Emoji Usage** (+0.05 for 1-2 emojis)
- Adds personality when used appropriately
- Penalizes overuse (3+)

**Robotic Language Removal** (-0.3)
- Eliminates "I am writing to inform you"
- Removes "pursuant to", "as per", "herewith"

## Usage Patterns

### Pattern 1: Direct Message Humanization
```python
# Format: base message → humanized message
message = "Buy our product now"
humanized = humanizer.build_human_message(
    base_message=message,
    buyer_profile=profile,
    market=Market.USA,
    industry=Industry.ECOMMERCE,
    language="en",
)
```

### Pattern 2: Objection Response
```python
# Detect emotion from objection
emotion = empathy_layer.detect_emotion(objection_text, "en")

# Generate empathetic response
response = empathy_layer.generate_empathetic_response(
    emotion,
    language="en",
)

# Build into full message
final = response_builder.build_response(
    base_message=response["response"],
    tone_type="professional",
    emotional_state=emotion.emotional_state.value,
    buyer_name=profile.first_name,
)
```

### Pattern 3: A/B Testing Workflow
```python
# 1. Create test
test = testing_engine.create_test(
    test_name="Tone Variation",
    test_type=ExperimentType.TONE,
    control_message=control,
    treatment_messages=treatments,
    hypothesis="Casual converts better",
)

# 2. Send messages with variants
for buyer in buyers:
    variant = testing_engine.select_variant(test.test_id)
    message = variant.message_template
    send_message(message, buyer, test.test_id, variant.variant_id)

# 3. Track events
track_open(test.test_id, variant.variant_id)
track_conversion(test.test_id, variant.variant_id)

# 4. Analyze results
results = testing_engine.analyze_test(test.test_id)
if results["status"] == "winner_found":
    deploy_winning_message(results)
```

## Best Practices

### Do's ✓
- Use DEEP personalization for high-value buyers
- Test tone variations for your audience
- Respect buyer emotional state (frustrated → empathetic)
- Keep messages under 200 words for casual settings
- Use 1-2 emojis max in casual tone
- Vary sentence length for readability

### Don'ts ✗
- Use formal language with casual audience (tone mismatch)
- Overuse buyer name (max 1-2 times per message)
- Add emojis to professional/formal messages
- Ignore emotional signals (hesitant → still pushing hard)
- Send pushy CTA when buyer is frustrated
- Use jargon with non-expert audience

## Testing

Run comprehensive test suite:

```bash
cd backend/app/core/humanization
python -m pytest test_humanization.py -v
```

Tests cover:
- Tone engine (10 tones, market/industry combinations)
- Empathy detection (8 emotional states)
- Personalization (name usage, preferences, urgency)
- Response building (CTA types, validation)
- A/B testing (variant selection, winner determination)
- End-to-end integration

## Metrics & Monitoring

Track these metrics to optimize humanness:

| Metric | Target | How to Measure |
|--------|--------|---|
| Humanness Score | >0.85 | User perception survey |
| Open Rate | >25% | Email opens |
| Reply Rate | >5% | Responses to messages |
| Conversion Rate | >2% | Buyers who convert |
| Tone Match | >0.8 | Consistency check |
| Personalization Score | >0.75 | Depth of personalization |

## Configuration

Default settings (customizable):

```python
# tone_engine.py
formality_level = 0.0-1.0  # How formal (default per tone)
emoji_density = 0.0-1.0    # Emoji usage (default per tone)
avg_sentence_length = 12   # Words per sentence

# personalization.py
NAME_USAGE_RULES = {
    "initial": 1,           # Use name 1x in opening
    "follow_up": 0,         # Don't overuse
    "objection_response": 0,
    "closing": 1,           # Use name in closing
}

# response_builder.py
MAX_MESSAGE_LENGTH = 2000  # Words
MIN_SENTENCE_LENGTH = 10   # For validation
CTA_PLACEMENT = "end"      # Where to put CTA
```

## Performance

- **Tone matching**: <50ms
- **Emotion detection**: <30ms
- **Personalization**: <100ms
- **Full message building**: <300ms

## Support

For issues or questions:
1. Check test suite for usage examples
2. Review component docstrings
3. Refer to integration example above
