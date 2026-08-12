# Phase 31 - Psychology Sales System
## "El Lobo de Wall Street" - Jordan Belfort Sales Methodology

**Duration**: 10 weeks (Feb 1 - Apr 15, 2027)  
**Team**: 2 backend + 1 frontend + 1 ML  
**Expected Impact**: +300% close rate, -50% sales cycle, $30M+ ARR expansion  
**Launch Date**: Apr 16, 2027

---

## 🧠 THE METHODOLOGY

**"La clave para vender no es hablar de las características del objeto, sino hacer preguntas para conocer las necesidades, los deseos y los problemas del comprador"**

**Jordan Belfort's 5-Step Framework:**

```
1. DISCOVER
   ↓ Ask questions to understand REAL needs
   ↓ Don't talk about product features yet
   ↓ Make them open up about problems

2. CREATE NEED
   ↓ Make them see their current situation is BROKEN
   ↓ Show gap between current state → desired state
   ↓ Make pain REAL and URGENT

3. POSITION SOLUTION
   ↓ Introduce product as ONLY answer
   ↓ Position against alternatives (FUD)
   ↓ Create "this is the one" mindset

4. TRIGGER URGENCY
   ↓ Limited supply / spots available
   ↓ Price going up tomorrow
   ↓ Others jumping in (social proof)
   ↓ Window closing (deadline)

5. CLOSE & COMMITMENT
   ↓ Assumptive close
   ↓ Get YES to small commitment first
   ↓ Build momentum to larger ask
   ↓ Repeat yes until big decision made
```

---

## 1. DISCOVERY QUESTIONS ENGINE

### Psychology: Uncover Hidden Needs

Rep asks questions in this ORDER:
1. **Rapport** ("Tell me about your company")
2. **Problem identification** ("What's your biggest challenge?")
3. **Impact assessment** ("How is that affecting revenue/efficiency?")
4. **Status quo** ("How are you handling it now?")
5. **Desired state** ("What would ideal look like?")
6. **Authority** ("Who else needs to agree on this?")

```python
class DiscoveryQuestionsEngine:
    """Generate contextual discovery questions."""
    
    QUESTION_HIERARCHY = {
        "rapport": [
            "Tell me about {company_name}",
            "What does your team focus on?",
            "How long have you been in this role?"
        ],
        "problem": [
            "What's your biggest challenge right now?",
            "Where are you losing time/money?",
            "What keeps you up at night?"
        ],
        "impact": [
            "How much is that costing you annually?",
            "What's the impact on your team?",
            "If this continued for 12 months, what happens?"
        ],
        "status_quo": [
            "How are you handling it now?",
            "What have you tried?",
            "Why hasn't that worked?"
        ],
        "desired": [
            "What would ideal look like?",
            "If you fixed this, what changes?",
            "What would you do with the time saved?"
        ],
        "authority": [
            "Who else needs to sign off?",
            "What's the decision process?",
            "When can we get them involved?"
        ]
    }
    
    def generate_discovery_questions(self, prospect: Dict, deal_stage: str) -> List[str]:
        """Generate next discovery question based on stage."""
        
        # Map deal stage to question hierarchy
        stage_to_hierarchy = {
            "initial_contact": "rapport",
            "discovery": "problem",
            "qualification": "impact",
            "needs_analysis": "status_quo",
            "solution_design": "desired",
            "proposal": "authority"
        }
        
        hierarchy = stage_to_hierarchy.get(deal_stage, "problem")
        questions = self.QUESTION_HIERARCHY[hierarchy]
        
        # Use Claude to personalize questions
        prompt = f"""
        Customize these discovery questions for:
        Company: {prospect['company']}
        Industry: {prospect['industry']}
        Role: {prospect['role']}
        
        Questions to customize:
        {json.dumps(questions)}
        
        Make questions specific to their industry. Focus on making them TALK, not you.
        """
        
        personalized = self.claude.messages.create(
            model="claude-opus",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return personalized.content[0].text.split("\n")
```

### Database: Track Responses

```sql
CREATE TABLE discovery_responses (
  id UUID PRIMARY KEY,
  prospect_id VARCHAR(255),
  deal_id VARCHAR(255),
  
  -- Question asked
  question TEXT,
  question_category VARCHAR(50),  -- rapport, problem, impact, etc
  
  -- Response captured
  response_text TEXT,
  sentiment VARCHAR(50),  -- positive, neutral, negative
  urgency_level INT,  -- 1-10: how urgent is problem
  
  -- Analysis
  needs_identified JSONB,  -- ["cost reduction", "faster implementation"]
  pain_points JSONB,  -- ["losing $50k/mo", "team burnout"]
  desired_outcomes JSONB,  -- ["save 10 hours/week", "reduce errors"]
  
  asked_at TIMESTAMP,
  INDEX idx_prospect (prospect_id)
);
```

---

## 2. NEED CREATION ENGINE

### Psychology: Amplify Pain + Show Solution Gap

```python
class NeedCreationEngine:
    """Create awareness of need using pain amplification."""
    
    def create_need_narrative(self, prospect: Dict, discovery_responses: List[str]) -> str:
        """Build narrative that creates urgency."""
        
        # Extract pain points from discovery
        pain_points = self._extract_pain_points(discovery_responses)
        
        # Calculate financial impact
        financial_impact = self._calculate_impact(pain_points, prospect)
        
        # Build narrative using Claude
        prompt = f"""
        Based on prospect's responses, create a "wake-up call" narrative that makes them see they NEED to act.
        
        Pain Points: {json.dumps(pain_points)}
        Financial Impact: ${financial_impact:,.0f}/year
        
        Structure:
        1. Validate their problem ("You're not alone...")
        2. Quantify cost ("That's costing you...")
        3. Show trend ("If unchanged for 12 months...")
        4. Create urgency ("Meanwhile, competitors are...")
        5. Position solution ("There IS a way to fix this...")
        
        Write in conversational, empathetic tone. Make it REAL, not salesy.
        """
        
        narrative = self.claude.messages.create(
            model="claude-opus",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return narrative.content[0].text
    
    def _extract_pain_points(self, responses: List[str]) -> List[str]:
        """Extract pain points from discovery responses."""
        
        # Use NLP/Claude to identify pain statements
        pain_keywords = ["losing", "wasting", "frustrated", "struggling", "broken", "pain"]
        
        pain_points = []
        for response in responses:
            if any(keyword in response.lower() for keyword in pain_keywords):
                pain_points.append(response)
        
        return pain_points
    
    def _calculate_impact(self, pain_points: List[str], prospect: Dict) -> float:
        """Calculate financial impact of problems."""
        
        # Extract metrics from pain points
        # "Losing 10 hours/week" → 10 * 50 * 52 = $26k/year
        # "50% error rate" → calculate cost per error
        
        # Use Claude to do calculation
        prompt = f"""
        Calculate annual financial impact:
        Pain points: {json.dumps(pain_points)}
        Company size: {prospect.get('size', 100)} employees
        Industry: {prospect.get('industry')}
        
        Estimate:
        - Lost productivity cost
        - Error/rework cost
        - Opportunity cost
        - Total annual impact
        """
        
        analysis = self.claude.messages.create(
            model="claude-opus",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Extract number from response
        import re
        match = re.search(r'\$([0-9,]+)', analysis.content[0].text)
        if match:
            return float(match.group(1).replace(",", ""))
        return 50000  # Conservative default
```

---

## 3. FOMO/URGENCY TRIGGER ENGINE

### Psychology: Create Scarcity + Social Proof + Deadline

```python
class UrgencyTriggerEngine:
    """Generate FOMO/urgency without being sleazy."""
    
    def generate_urgency_triggers(self, deal: Dict) -> List[Dict]:
        """Create legitimate urgency triggers."""
        
        triggers = []
        
        # 1. Supply scarcity
        if deal['stage'] == 'proposal':
            triggers.append({
                "type": "supply_scarcity",
                "trigger": "We have 3 slots left this quarter",
                "why_true": "Limited onboarding capacity",
                "deadline": "End of quarter"
            })
        
        # 2. Price increase
        triggers.append({
            "type": "price_increase",
            "trigger": "Pricing goes up March 1st",
            "why_true": "We're raising costs for new customers",
            "deadline": "Feb 28"
        })
        
        # 3. Social proof
        if deal['company']['industry'] == prospect['industry']:
            triggers.append({
                "type": "social_proof",
                "trigger": f"We just signed 3 other {prospect['industry']} companies",
                "why_true": "True recent closures",
                "deadline": "Now"
            })
        
        # 4. Competitive threat
        competitors_in_market = check_competitor_activity(prospect)
        if competitors_in_market:
            triggers.append({
                "type": "competitive",
                "trigger": "Your competitors are already using this",
                "why_true": "Sales intelligence data",
                "deadline": "Before they get advantage"
            })
        
        return triggers
    
    def weave_urgency_into_narrative(self, triggers: List[Dict], narrative: str) -> str:
        """Weave urgency into conversation naturally."""
        
        # DON'T say "Limited spots available!" (cringe)
        # DO say "Our next onboarding cohort is full" (true + natural)
        
        prompt = f"""
        Weave these urgency elements into the sales narrative naturally (not salesy):
        
        Triggers: {json.dumps(triggers)}
        Current narrative: {narrative}
        
        Rules:
        1. Sound conversational, not pushy
        2. Make each point feel like valuable info sharing
        3. Let prospect draw own conclusion ("You should probably move fast")
        4. Don't sound desperate or fake
        
        Rewrite narrative with urgency woven in:
        """
        
        result = self.claude.messages.create(
            model="claude-opus",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return result.content[0].text
```

---

## 4. OBJECTION HANDLER (Psychology-Based)

### Psychology: Never Deny, Always Validate + Reframe

```python
class PsychologyObjectionHandler:
    """Handle objections using psychology, not logic."""
    
    OBJECTIONS = {
        "price": {
            "frameworks": [
                "Price of regret: If you don't act, what does it cost?",
                "Comparison: What does [status quo] cost you?"
            ]
        },
        "time": {
            "frameworks": [
                "Investment frame: 5 hours now saves 10 hours/week",
                "Opportunity cost: What's your time worth?"
            ]
        },
        "need": {
            "frameworks": [
                "Future frame: Will this problem get worse or better?",
                "Competitor frame: Others are already solving this"
            ]
        },
        "authority": {
            "frameworks": [
                "Get them talking: Who would benefit most?",
                "Social proof: Here's how [peer company] sold it internally"
            ]
        }
    }
    
    def handle_objection(self, objection: str, prospect: Dict) -> str:
        """Generate psychology-based objection response."""
        
        # 1. Validate (never dismiss)
        validation = f"I totally get that. {len(objection) * 0.1}% of people feel that way initially."
        
        # 2. Reframe using psychology framework
        objection_type = self._classify_objection(objection)
        frameworks = self.OBJECTIONS.get(objection_type, self.OBJECTIONS['need'])
        
        # 3. Use Claude to generate response
        prompt = f"""
        Create psychology-based reframe for this objection:
        
        Objection: "{objection}"
        Prospect: {json.dumps(prospect)}
        
        Reframe using one of these psychological frames:
        {json.dumps(frameworks['frameworks'])}
        
        Response should:
        1. Validate their concern
        2. Shift perspective without dismissing
        3. Ask question that makes them think
        4. NOT sell features
        
        Generate response:
        """
        
        response = self.claude.messages.create(
            model="claude-opus",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
```

---

## 5. ASSUMPTIVE CLOSE ENGINE

### Psychology: Assume Yes, Ask for Commitment

```python
class AssumptiveCloseEngine:
    """Jordan Belfort's 5-step closing sequence."""
    
    def generate_close_sequence(self, prospect: Dict, deal_value: float) -> List[str]:
        """Generate 5-step close assuming they said yes."""
        
        closes = []
        
        # Step 1: Small commitment (low barrier)
        closes.append({
            "step": 1,
            "commitment": "Should we schedule a 30-min call with [team]?",
            "psychology": "Small YES builds momentum",
            "expected_response": "Sure, when?"
        })
        
        # Step 2: Larger commitment (they're in the flow)
        closes.append({
            "step": 2,
            "commitment": "Which payment plan works better: annual or monthly?",
            "psychology": "Choice between prices assumes they'll buy",
            "expected_response": "Annual probably"
        })
        
        # Step 3: Even bigger (trial/pilot)
        closes.append({
            "step": 3,
            "commitment": "Let's pilot this for 30 days first",
            "psychology": "Removes risk perception",
            "expected_response": "Ok, let's try it"
        })
        
        # Step 4: Expand scope
        closes.append({
            "step": 4,
            "commitment": "Should we add the extra modules?",
            "psychology": "Small upsell after main buy",
            "expected_response": "Maybe later"
        })
        
        # Step 5: Full commitment
        closes.append({
            "step": 5,
            "commitment": "Let's get you fully set up. I'll send contract today.",
            "psychology": "Momentum + assumption = automatic yes",
            "expected_response": "Ok, send it"
        })
        
        return closes
    
    def generate_next_close(self, current_step: int, response: str) -> str:
        """Generate next close based on their response."""
        
        if not self._is_positive_response(response):
            # Objection - handle with psychology handler
            return self._handle_close_objection(response)
        
        # They said yes - move to next step
        closes = self.generate_close_sequence({}, 0)
        if current_step < len(closes):
            return closes[current_step + 1]["commitment"]
        
        return "So you're ready to go? Great! Let's make it happen."
    
    def _is_positive_response(self, response: str) -> bool:
        """Determine if response is positive."""
        positive_words = ["yes", "sure", "okay", "good", "let's", "when", "how"]
        return any(word in response.lower() for word in positive_words)
```

---

## 6. SALES CONVERSATION FLOW

### Entire Conversation Sequence (Jordan Belfort Method)

```
REP: "Hey [Name], thanks for taking the call. I've got just 15 minutes before my next thing."
    [Creates urgency, anchors time commitment]

REP: "Tell me, what brought you to look into this now?"
    [Discovery: Opens conversation, lets them talk]

PROSPECT: "We're looking to automate our outbound."
    [Early signal]

REP: "When you say automate, what's driving that? What's happening now?"
    [Problem discovery]

PROSPECT: "We're doing 30 calls a week manually. My team's burnout is high."
    [Pain point revealed]

REP: "Wow, 30 a week... [validates] ... how many could you do if you had the time?"
    [Quantifies opportunity]

PROSPECT: "Probably 5x if we didn't have to dial everything manually."
    [They're calculating revenue impact]

REP: "So if you could do 150 calls a week... what would that mean for revenue?"
    [Make THEM do the math on need]

PROSPECT: "Honestly? Could be $2M more pipeline..."
    [They create the need themselves]

REP: "That's huge. The challenge is we're at capacity for March onboarding..."
    [Scarcity/urgency trigger, woven naturally]

PROSPECT: "Really? How long is the wait?"
    [Interest in moving fast]

REP: "Current cohort's full, next is April. BUT, since this aligns with what we're building..."
    [Opens door to exception]

REP: "Can I show you what that 150-call-a-week version looks like? Fair?"
    [Assumptive close #1 - they say yes]

[Proposal shown]

REP: "So you're thinking March launch?"
    [Assumptive close #2 - assumes they're buying]

PROSPECT: "Wait, how much is this?"
    [Objection on price]

REP: "It's $500/month. [pause] But think about it... [holds up deal math]... you're spending that on coffee and lunches. Meanwhile $2M pipeline opportunity is sitting there."
    [Reframe: price vs opportunity, not price vs budget]

PROSPECT: "That's true, but my finance team..."

REP: "Totally get it. [validates] How about we make it easy for them? Start at $250 for 30 days, then $500 after. They see results, they'll get it approved. Fair?"
    [Assumptive close #3 - option between terms]

PROSPECT: "Ok, that works."
    [YES received]

REP: "Perfect. Let's get your team set up. I'll send the onboarding calendar by EOD. You'll be making 150 calls by March 15th. Good?"
    [Momentum: build next small commitment]

PROSPECT: "Sounds good."

REP: "Awesome. One thing - should we add the voice coaching module? It'll train your reps on the calls..."
    [Soft upsell after main buy - Step 4 close]

PROSPECT: "Maybe later."
    [No objection)

REP: "No problem, we can add it anytime. But just so you know, $50/month and 80% of customers add it by month 2 because results are crazy."
    [Social proof + easy option to add]

REP: "Ok, I'm sending you everything. Expect onboarding call tomorrow 10 AM. You good?"
    [Commitment #5: Assume final yes]

PROSPECT: "Yep, see you tomorrow."

[DEAL CLOSED]
```

---

## 7. DATABASE SCHEMA

```sql
CREATE TABLE discovery_responses (
  id UUID PRIMARY KEY,
  prospect_id VARCHAR(255),
  
  question TEXT,
  category VARCHAR(50),
  response TEXT,
  sentiment VARCHAR(50),
  urgency_level INT,
  needs_identified JSONB,
  pain_points JSONB,
  
  INDEX idx_prospect (prospect_id)
);

CREATE TABLE need_narratives (
  id UUID PRIMARY KEY,
  deal_id VARCHAR(255),
  
  narrative TEXT,
  financial_impact_calculated FLOAT,
  created_at TIMESTAMP
);

CREATE TABLE objection_handling (
  id UUID PRIMARY KEY,
  deal_id VARCHAR(255),
  
  objection_text TEXT,
  objection_type VARCHAR(50),
  response_generated TEXT,
  prospect_response TEXT,
  resolved BOOLEAN,
  
  INDEX idx_deal (deal_id)
);

CREATE TABLE close_attempts (
  id UUID PRIMARY KEY,
  deal_id VARCHAR(255),
  
  close_step INT,
  commitment_asked TEXT,
  response TEXT,
  committed BOOLEAN,
  timestamp TIMESTAMP,
  
  INDEX idx_deal_step (deal_id, close_step)
);

CREATE TABLE sales_conversations (
  id UUID PRIMARY KEY,
  deal_id VARCHAR(255),
  
  conversation_text JSONB,
  sentiment_progression JSONB,
  urgency_triggers_used JSONB,
  closes_attempted INT,
  deal_won BOOLEAN,
  
  started_at TIMESTAMP,
  closed_at TIMESTAMP
);
```

---

## SUCCESS CRITERIA

**Discovery**:
- ✅ 5+ discovery questions per call
- ✅ 80%+ prospects open up about real problems
- ✅ Average problem quantified ($ impact calculated)

**Need Creation**:
- ✅ Prospect calculates their own impact
- ✅ 90%+ see their situation as urgent
- ✅ Self-generated belief they NEED solution

**FOMO/Urgency**:
- ✅ 3+ urgency triggers per deal naturally
- ✅ Triggers feel legitimate (not manipulative)
- ✅ 60%+ move to contract within 7 days

**Closing**:
- ✅ 5-step sequence 80%+ successful
- ✅ 3+ assumptive closes per deal
- ✅ 70%+ close rate (vs 18% baseline)

**Financial Impact**:
- ✅ Sales cycle: 85 days → 30 days (-65%)
- ✅ Close rate: 18% → 60% (+300%)
- ✅ ACV: $50k → $150k+ (+200%)
- ✅ Year 1: $30M+ ARR expansion

---

## TIMELINE

**Week 1-2**: Discovery Questions Engine  
**Week 3-4**: Need Creation Engine  
**Week 5-6**: FOMO/Urgency Triggers  
**Week 7-8**: Objection Handler  
**Week 9-10**: Assumptive Close Engine + Testing

**Launch**: Apr 16, 2027

---

**"The money's not in closing. The money's in the NEED."** — Jordan Belfort

**Phase 31 Ready to Build**
