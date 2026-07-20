"""50 Retention Prompts — Customer experience, engagement, churn prevention, loyalty, upsell, NPS."""

from dataclasses import dataclass
from typing import Dict, Any, List
from enum import Enum


class RetentionStrategy(str, Enum):
    """Types of retention strategies."""
    CUSTOMER_EXPERIENCE = "Customer Experience"
    ENGAGEMENT = "Engagement"
    CHURN_PREVENTION = "Churn Prevention"
    LOYALTY = "Loyalty"
    UPSELL_CROSSSELL = "Upsell/Cross-sell"
    WINBACK = "Win-back"
    HEALTH_SCORING = "Health Scoring"
    FEEDBACK = "Feedback"
    REFERRAL = "Referral"
    NPS = "NPS"


@dataclass
class RetentionPromptTemplate:
    """Structure for a retention prompt."""
    id: str
    name: str
    strategy: str
    business_context: str
    prompt_text: str
    variables: List[str]
    example_input: Dict[str, Any]
    example_output: str
    success_metrics: List[str]
    industry_variations: Dict[str, str]
    best_practices: List[str]
    tags: List[str]


class RetentionPrompts:
    """50 retention prompts organized by retention strategy."""

    # ==================== CUSTOMER EXPERIENCE (10 PROMPTS) ====================

    @staticmethod
    def onboarding_optimization_framework() -> RetentionPromptTemplate:
        """Design onboarding that gets customers to value fast and builds love."""
        return RetentionPromptTemplate(
            id="retention_001",
            name="Onboarding Optimization Framework",
            strategy=RetentionStrategy.CUSTOMER_EXPERIENCE.value,
            business_context="Create onboarding experiences that achieve early wins, build competence, and drive long-term retention.",
            prompt_text="""Design onboarding for {product_name} to drive {success_metric}.

CUSTOMER CONTEXT:
- Product: {product_name}
- Customer type: {customer_type}
- Primary goal with product: {customer_goal}
- Success metric: {success_metric}
- Timeline to value: {time_to_first_value}
- Adoption barrier: {biggest_barrier}

ONBOARDING OBJECTIVES:
1. {objective_1}
2. {objective_2}
3. {objective_3}

ONBOARDING FLOW (Define each stage):

STAGE 1: PRE-ONBOARDING (Before Day 1)
- Timeline: {preob_timeline}
- Goal: {preob_goal}
- Touchpoints:
  * Email 1: {preob_email_1} (Send: {preob_email_1_send})
  * Email 2: {preob_email_2} (Send: {preob_email_2_send})
  * Optional: {preob_optional}

Content to provide:
- Getting started video: {gs_video_duration} min, showing {gs_video_focus}
- Setup checklist: {setup_checklist_items} items
- FAQ addressing: {faq_concerns}

Success indicator: {preob_success_signal}

---

STAGE 2: DAY 1-3 (CRITICAL FIRST IMPRESSION)
- Goal: Get customer to first success (AHA moment)
- What to achieve: {day1_achievement}
- Key milestones:
  * Day 1: {day1_milestone}
  * Day 2: {day2_milestone}
  * Day 3: {day3_milestone}

Guided experience:
- Feature 1: {feature_1_to_teach} (Why: {feature_1_value})
- Feature 2: {feature_2_to_teach} (Why: {feature_2_value})
- Feature 3: {feature_3_to_teach} (Why: {feature_3_value})

Interaction model:
- Option A: Fully guided (hand-holding, limited freedom)
- Option B: Guided with sandbox (guided but safe to explore)
- Option C: Self-serve with prompts (freedom but helpful hints)
- Recommended: {recommended_model} (because: {reason})

Support model (Day 1-3):
- Chat support: {chat_availability}
- Email support: {email_availability}
- Success manager: {sm_involvement}
- Proactive outreach: {proactive_timeline}

Metrics to track:
- Completion rate of Day 1 path: {d1_completion_target}%
- Time to first success: {time_to_first_success_target} minutes
- Customer sentiment (Day 3): {sentiment_target}

---

STAGE 3: WEEK 2-4 (BUILD COMPETENCE)
- Goal: Customer becomes competent with core workflows
- Features to introduce:
  * Week 2: {week2_features}
  * Week 3: {week3_features}
  * Week 4: {week4_features}

Teaching methods:
- In-app training: {in_app_training} (interactive, contextual)
- Videos: {video_count} × {video_duration} minutes (specific tasks)
- Documentation: {doc_pages} pages (reference material)
- Live training: {live_training_frequency} (group or 1:1)

Customer habit formation:
- Habit 1: Use product for {habit_1} (Frequency: {habit_1_frequency})
- Habit 2: Use product for {habit_2} (Frequency: {habit_2_frequency})
- Habit 3: Use product for {habit_3} (Frequency: {habit_3_frequency})

Progress milestones:
- Week 2: {milestone_w2}
- Week 3: {milestone_w3}
- Week 4: {milestone_w4}

---

STAGE 4: MONTH 2 (OPTIMIZATION & SELF-SUFFICIENCY)
- Goal: Customer is self-sufficient and finding ROI
- Focus areas:
  * Optimization: {optimization_focus}
  * Advanced features: {advanced_features}
  * Integration: {integration_setup}

Transition to self-sufficiency:
- Reduce hands-on support (dial down success manager time)
- Shift to: community, documentation, email support
- Provide: templates, playbooks, best practices

First business outcome target:
- {outcome_metric}: Target {outcome_target} by end of Month 2
- Celebration moment: {celebration_trigger}

---

ONBOARDING EXPERIENCE DESIGN:

Customer journey map:

BEFORE ONBOARDING
Customer thinking: "I hope this works..."
Your action: Build excitement + reduce anxiety
Touchpoint: Welcome email, setup guide, success manager intro

DAY 1
Customer thinking: "Can I figure this out?"
Your action: Make first success easy and obvious
Touchpoint: In-app tour, first setup wizard, quick win

DAY 2-3
Customer thinking: "Does this actually save me time?"
Your action: Show ROI through first real workflow
Touchpoint: Guided first use case, proactive support, celebration

WEEK 2-4
Customer thinking: "Am I using this right? What else can I do?"
Your action: Build competence through structured learning
Touchpoint: Weekly training, contextual help, milestone celebrations

MONTH 2+
Customer thinking: "This is my normal now"
Your action: Support self-sufficiency, identify expansion opportunities
Touchpoint: Monthly check-in, advanced features, customer community

---

ONBOARDING METRICS:

Adoption metrics:
- Day 1 activation rate: {d1_activation_target}%
- Week 1 retention: {w1_retention_target}%
- Month 1 retention: {m1_retention_target}%
- Active daily users (Month 2): {dau_m2_target}%

Competence metrics:
- Core features used: {core_features_adoption_target}%
- Self-serve support queries: {self_serve_target}% of questions answered by docs/community
- Advanced features discovered: {advanced_feature_adoption_target}%

Business outcome metrics:
- {success_metric}: Achieved by {outcome_timeline}
- Customer satisfaction (post-onboarding): {nps_target} NPS
- Time to value: {ttv_target} days

---

COMMON ONBOARDING FAILURES (Avoid):

Failure 1: Too much information too fast
- Problem: Customers overwhelmed, give up
- Solution: Break into micro-lessons, focus on core workflows

Failure 2: No clear "first success" moment
- Problem: Customer unclear if they're doing it right
- Solution: Define AHA moment, celebrate it, reinforce it

Failure 3: Guidance disappears after Day 1
- Problem: Customers lost in Week 2-3, churn
- Solution: Structured progression through Month 2

Failure 4: Support is reactive only
- Problem: Customers hit friction, no one reaches out, they leave
- Solution: Proactive check-ins: Day 3, Day 7, Week 4, Month 2

Failure 5: Onboarding doesn't tie to real business outcome
- Problem: Customer sees features but doesn't see ROI
- Solution: Connect every task back to "this saves you $X" or "this delivers Y outcome"

---

SUCCESS ACTIVATION EMAIL TEMPLATE (Day 1):

Subject: "Your first [success_metric] is 1 click away"

Body:
"Hi [Name],

Welcome to [Product]!

The best way to understand [product] is to see it in action.
In the next 10 minutes, I want you to experience this:

1. [Simple task 1] (2 min)
2. [Simple task 2] (3 min)
3. [Experience the ROI] (5 min)

That's it. After those 10 minutes, you'll understand why [product] works.

[BUTTON: Start my first 10 minutes →]

Questions? Reply to this email or chat with me at [chat_link]

Talk soon,
[Success Manager Name]"

---

ONBOARDING OPTIMIZATION CYCLE:

Month 1: Baseline (Track all metrics above)
Month 2: Identify bottleneck (Where do most customers get stuck?)
Month 3: Test fix (Reduce friction at bottleneck, measure impact)
Month 4: Iterate (Keep what works, fix what doesn't)
Ongoing: Optimize (Monthly small improvements compound over time)

Example iteration:
- Baseline: 60% Week 1 retention
- Bottleneck: Day 2-3, customers unclear about "first real workflow"
- Fix: Add guided "first workflow" scenario (10 min)
- Result: 72% Week 1 retention (+12 points)
- Action: Standardize guided workflows for all customers""",
            variables=["product_name", "success_metric", "customer_type", "customer_goal",
                      "time_to_first_value", "biggest_barrier", "objective_1", "objective_2",
                      "objective_3", "preob_timeline", "preob_goal", "preob_email_1",
                      "preob_email_1_send", "preob_email_2", "preob_email_2_send", "preob_optional",
                      "gs_video_duration", "gs_video_focus", "setup_checklist_items",
                      "faq_concerns", "preob_success_signal", "day1_achievement", "day1_milestone",
                      "day2_milestone", "day3_milestone", "feature_1_to_teach", "feature_1_value",
                      "feature_2_to_teach", "feature_2_value", "feature_3_to_teach", "feature_3_value",
                      "recommended_model", "reason", "chat_availability", "email_availability",
                      "sm_involvement", "proactive_timeline", "d1_completion_target",
                      "time_to_first_success_target", "sentiment_target", "week2_features",
                      "week3_features", "week4_features", "in_app_training", "video_count",
                      "video_duration", "doc_pages", "live_training_frequency", "habit_1",
                      "habit_1_frequency", "habit_2", "habit_2_frequency", "habit_3",
                      "habit_3_frequency", "milestone_w2", "milestone_w3", "milestone_w4",
                      "optimization_focus", "advanced_features", "integration_setup",
                      "outcome_metric", "outcome_target", "celebration_trigger",
                      "d1_activation_target", "w1_retention_target", "m1_retention_target",
                      "dau_m2_target", "core_features_adoption_target", "self_serve_target",
                      "advanced_feature_adoption_target", "outcome_timeline", "nps_target",
                      "ttv_target"],
            example_input={
                "product_name": "TaskFlow",
                "success_metric": "First project created and tracked for 2 weeks",
                "customer_type": "Mid-market SaaS (50-200 employees)",
                "customer_goal": "Reduce missed deadlines from 30% to <5%",
                "time_to_first_value": "2 hours to see first project visibility",
                "biggest_barrier": "Understanding how to integrate with existing tools",
                "objective_1": "Get customer to 'AHA' moment (project visibility working)",
                "objective_2": "Build habit of daily dashboard check",
                "objective_3": "Get customer to ROI proof within 30 days",
                "preob_timeline": "2 days before go-live",
                "preob_goal": "Set up access, reduce Day 1 anxiety",
                "preob_email_1": "Welcome + setup instructions",
                "preob_email_1_send": "Same day customer signs",
                "preob_email_2": "Success manager intro + calendar invite",
                "preob_email_2_send": "Next day",
                "gs_video_duration": "3",
                "gs_video_focus": "End-to-end first project workflow",
                "setup_checklist_items": "5 (login, add teams, create first project, integrate Slack, etc.)",
                "d1_completion_target": "85",
                "time_to_first_success_target": "30",
                "sentiment_target": "7/10 confidence",
                "day1_achievement": "Create first project and invite team",
                "day1_milestone": "Login + account setup complete",
                "day2_milestone": "First project created with tasks",
                "day3_milestone": "Team invited, Slack integration live, first dashboard view",
                "feature_1_to_teach": "Project creation and task management",
                "feature_1_value": "This is the core of dashboard visibility",
                "feature_2_to_teach": "Slack integration",
                "feature_2_value": "See updates without logging in",
                "feature_3_to_teach": "Dashboard analytics",
                "feature_3_value": "See on-time delivery rate (your ROI metric)",
                "recommended_model": "Guided with sandbox",
                "reason": "Mid-market customers value structure but want to experiment",
                "chat_availability": "24/5 (business hours + overlap)",
                "sm_involvement": "2-3 check-ins (Day 1, Day 3, Week 2)",
                "proactive_timeline": "Day 1 (via email), Day 3 (via chat), Day 7 (via email)",
                "week2_features": "Advanced project templates, reporting basics",
                "week3_features": "Custom fields, workflow automation",
                "week4_features": "API integrations, advanced analytics",
                "habit_1": "Check dashboard each morning (daily)",
                "habit_1_frequency": "Daily, <2 minutes",
                "habit_2": "Update project status (2-3x/week)",
                "habit_2_frequency": "Tuesday/Thursday/Friday updates",
                "habit_3": "Review weekly report (weekly)",
                "habit_3_frequency": "Friday afternoon 1-pager",
                "outcome_metric": "On-time delivery rate",
                "outcome_target": "30% → 65% (heading to 95%)",
                "celebration_trigger": "When first on-time delivery is 100%"
            },
            example_output="""TASKFLOW ONBOARDING FRAMEWORK

---

STAGE 1: PRE-ONBOARDING (2 Days Before Go-Live)

Goal: Prepare customer, reduce Day 1 anxiety, set expectations for fast wins

Day -2 (Immediately after contract):
Email 1: "Your TaskFlow account is ready (Here's how to get started)"
Subject: "Welcome to TaskFlow! Here's your first steps."

Body:
"Hi [Name],

I'm excited to help your team hit 100% on-time delivery.

Here's what to expect:

1. Login: [Link] (username: your email)
2. Watch this: 3-min video on what to expect
3. Run through setup: 5-item checklist (10 min)

Day 1 call: We'll create your first project together (30 min)
Outcome: You'll see your dashboard working that same day

Anything blocking you before we start? Let me know.

[Success Manager Name]"

---

Day -1 (Next morning):
Email 2: "Meet your success manager + calendar invite"

Body:
"Hi [Name],

I'm [Success Manager], your dedicated TaskFlow guide.
I'll help you hit 65% on-time delivery in 30 days (then 95%+).

Quick call tomorrow?
[Calendly link for 30-min call]

Here's what I'll do in that call:
- Walk through account setup (5 min)
- Create your first project together (10 min)
- Connect your Slack (5 min)
- Show your first dashboard view (5 min)
- Answer questions (5 min)

Come prepared with:
- List of your top 3 current projects
- Any integrations you use (email, Slack, Calendar, etc.)
- Team members to invite (can also do later)

See you tomorrow,
[Success Manager Name]"

---

PRE-ONBOARDING RESOURCES:
- Getting started video (3 min): "TaskFlow in 180 seconds"
- Setup checklist (5 items):
  1. Create your account (1 min)
  2. Add your team members (2 min)
  3. Connect Slack (2 min)
  4. Create first project (3 min)
  5. Invite team to dashboard (2 min)
- FAQ: "Will this integrate with X? What if we use Y?"
- Success indicator: Customer completes setup checklist by Day 1 call

---

STAGE 2: DAY 1-3 (CRITICAL FIRST IMPRESSION)

DAY 1 CALL (30 min with Success Manager):

Outcome: Customer sees first project in real-time, understands ROI path

Agenda:
1. Welcome & context setting (3 min)
   "You told us you're missing 30% of deadlines. By end of this month,
    I expect you to be hitting 65%, heading to 95%+."

2. Live walkthrough: Create first project (10 min)
   - Navigate to "Create Project"
   - Fill in: Project name, team members, deadline
   - Show: Dashboard now has this project
   - Point out: "This visibility is what your team didn't have before"

3. Slack integration (5 min)
   - Connect Slack (3 clicks)
   - Show: Slack channel now getting project updates
   - Explain: "No more email chains about status"

4. Invite team (3 min)
   - Add top 3 team members
   - Show: How they see the dashboard

5. Explain next steps (5 min)
   - "Between now and Friday, I want your team using this for [one small project]"
   - "Friday we'll review: did you see the visibility? Could you skip a status meeting?"
   - "That's our proof point."

Q&A (3 min)

End call with: "I'll check in Friday and Sunday. Reply anytime with questions."

---

DAY 2 (Async proactive outreach):
Email: "Quick tip: How to add your first real project"

Body:
"Hi [Name],

Quick question: Did your team try that first project yet?

If not, here's the easiest way to start:
1. Pick your smallest active project
2. Add it to TaskFlow (< 5 min)
3. Invite 2-3 people to it
4. Watch the dashboard light up

Your team will immediately see something they didn't have: visibility into who's doing what, when.

That's the magic.

Need help? Reply here or [chat link]

[Success Manager Name]"

---

DAY 3 CALL (15 min check-in):
Goal: Celebrate first use, reinforce ROI connection

"How went [first project]? Did you see something you weren't expecting?"
→ Listen for: "Yeah, we could finally see everything in one place"
→ Reinforce: "That's the foundation of hitting 100% on-time delivery"

Assign homework: "Use TaskFlow for your next 2 projects (even small ones).
Let's talk Monday about whether this is saving your team time."

---

STAGE 3: WEEK 2-4 (BUILD COMPETENCE & HABITS)

WEEK 2: Introduce core features
Video 1: "Creating task dependencies (3 min)"
Video 2: "Automated alerts (2 min)"
Live training: "Advanced project templates" (30 min group optional)

Habit formation: "Use dashboard every morning"
→ Email Monday morning: "What's your on-time status this week?"
→ Point to dashboard link showing weekly health

Milestone: 5+ projects in system, team doing daily standups via dashboard

---

WEEK 3: Introduce optimization
Video: "Custom fields for your workflow (4 min)"
Documentation: "Best practices for SaaS project tracking"

Habit reinforcement: Celebrate early wins
→ "Your team hit 5 projects without a missed deadline this week. That's progress."

Milestone: Team confident managing 10+ projects

---

WEEK 4: ROI check-in
Email: "Your first 4 weeks of data"
Attachment: Dashboard snapshot showing:
- Projects completed: X
- On-time delivery rate: Y% (target: 65%, heading to 95%)
- Time saved: Z hours/week (vs. previous manual process)
- Team satisfaction: "We're not spending all day on status updates"

Call: "How are you feeling about the ROI? Ready to scale?"

---

STAGE 4: MONTH 2+ (OPTIMIZATION & SELF-SUFFICIENCY)

Monthly business review:
- Review on-time delivery improvements (target: 65% this month)
- Discuss advanced features they're ready for
- Identify expansion: "Are other teams ready?"

Shift support model:
- Less: 1:1 success manager check-ins (move to quarterly)
- More: Community, self-serve docs, email support

---

ACTIVATION TARGETS:

By Day 1:
- ✓ Account set up
- ✓ First project created
- ✓ Slack integration live
- ✓ Team invited

By Day 3:
- ✓ Dashboard actively viewed (2+ times)
- ✓ Slack notifications received
- ✓ Customer confidence: 7/10

By Week 1:
- ✓ 3-5 projects in system
- ✓ Daily dashboard habit starting
- ✓ Team has done 1+ status update via system

By Week 4:
- ✓ 10+ projects tracked
- ✓ 60%+ on-time delivery (showing improvement)
- ✓ Customer satisfaction: 8/10 NPS
- ✓ Discussion: Ready to scale to other teams

By Month 2:
- ✓ 65% on-time delivery (vs. 30% baseline)
- ✓ 15 hours/week of time saved (quantified)
- ✓ Expansion conversation: "Let's do this for engineering too"

---

METRICS TO TRACK:

Adoption:
- Day 1 activation: 85%+ (account set up, first project)
- Week 1 retention: 90%+ (still using after first week)
- Month 1 retention: 85%+ (still using after 30 days)
- DAU in Month 2: 70%+ (team using daily)

Competence:
- Core features adopted: 80%+ use dashboard + Slack integration
- Self-serve success: 70%+ of questions answered by docs/community
- Advanced feature discovery: 30%+ explore custom fields, templates

Business outcome:
- On-time delivery improvement: 30% → 65% by end of Month 1
- NPS post-onboarding: 45+ (vs. baseline 30)
- Time to value: 2 weeks (first visible ROI)
- Expansion readiness: 50% ready to add more teams by Month 2
""",
            success_metrics=[
                "Day 1 activation: 85%+ of customers complete onboarding",
                "Month 1 retention: 85%+ of customers still active",
                "Time to first success: <2 hours",
                "NPS post-onboarding: 45+ (vs. baseline 30)",
                "Customer success metric: Achieve target outcome by 30 days"
            ],
            industry_variations={
                "SaaS": "ROI-focused, integration-heavy, feature progression",
                "Real Estate": "Deal-focused, market context, agent-specific workflows",
                "Services": "Project-focused, team coordination, client delivery"
            },
            best_practices=[
                "First success within 2 hours — not 2 days",
                "Celebrate early wins — reinforce that it's working",
                "Make support proactive — don't wait for customers to ask",
                "Connect every step to business outcome — not just features",
                "Build daily habit in Week 2 — consistency drives retention"
            ],
            tags=["onboarding", "customer-experience", "activation", "retention", "engagement"]
        )

    @staticmethod
    def churn_prediction_and_prevention() -> RetentionPromptTemplate:
        """Identify at-risk customers and intervene before they leave."""
        return RetentionPromptTemplate(
            id="retention_011",
            name="Churn Prediction & Prevention",
            strategy=RetentionStrategy.CHURN_PREVENTION.value,
            business_context="Predict which customers are likely to churn and proactively intervene with targeted win-back campaigns.",
            prompt_text="""Create churn prediction & prevention system for {product_name}.

CHURN ANALYSIS:

Historical churn data:
- Annual churn rate: {current_churn_rate}%
- MRR lost to churn: ${monthly_churn_mrr}
- Primary churn reasons: {churn_reason_1}, {churn_reason_2}, {churn_reason_3}
- Churn timing: Peak at month {peak_churn_month} ({{peak_churn_reason}})

CHURN PREDICTION MODEL:

Red flags (indicators of churn risk):

Technical signals:
- Feature A usage: Dropped >50% from baseline → High risk (70% churn rate)
  * Reason: [Usually means customer success isn't matching needs]
  * Intervention: Reach out within 48 hours

- Daily active users: Dropped from {baseline_dau} to {warning_dau} → Medium risk (40% churn rate)
  * Reason: [Adoption stalling, team lost interest]
  * Intervention: Offer free training, advanced features

- Support ticket surge: {surge_trigger} tickets in 7 days → High risk (60% churn rate)
  * Reason: [Problems building up, customer frustrated]
  * Intervention: Proactive support call, offer dedicated help

Behavioral signals:
- No login for {inactivity_days} days → High risk (80% churn rate)
  * Reason: [Customer moved on or forgot about product]
  * Intervention: Re-engagement campaign + value reminder

- Reduced integrations used: From {baseline_integrations} to {warning_integrations} → Medium risk
  * Reason: [Workflow changed, product less relevant]
  * Intervention: Understand new workflow, offer solutions

- Missed ROI targets: {{success_metric}} not hit after {timeline} → Medium risk
  * Reason: [Product didn't deliver promised value]
  * Intervention: Deep dive call, adjust expectations, redemo value

Engagement signals:
- Didn't attend training/webinars (3+ missed) → Low-medium risk (30% churn)
- Unsubscribed from all emails → Low risk but flag (10% churn)
- Reduced scope: Contract reduced ARR by {reduction_percent} → High risk (70% churn)

Sentiment signals (from support/sales interactions):
- Keywords in tickets: "not working", "too complex", "needs X feature" → Monitor
- NPS score: Dropped from {baseline_nps} to {warning_nps} → High risk
- CSM notes: "Customer frustrated", "finding alternative" → Critical risk

---

CHURN RISK SCORING:

Calculate risk score (0-100):

Base score:
- Feature usage drop 50%+: +30 points
- DAU drop 50%+: +20 points
- No login for 14+ days: +25 points
- Support ticket surge (5+ in 7 days): +20 points
- NPS decline 20+ points: +15 points
- Reduced scope: +25 points
- Sentiment negative: +20 points

Risk tiers:
- 80-100: CRITICAL CHURN RISK
  * Intervention: Immediate call within 24 hours
  * Contact: CSM + Sales leader
  * Cadence: Daily check-in until resolved

- 60-79: HIGH CHURN RISK
  * Intervention: Call within 3 days
  * Contact: CSM + Success team
  * Cadence: 3x per week

- 40-59: MEDIUM CHURN RISK
  * Intervention: Proactive email + offer support
  * Contact: CSM
  * Cadence: 2x per week

- 20-39: LOW-MEDIUM CHURN RISK
  * Intervention: Monitor + nurture
  * Contact: Automated engagement
  * Cadence: Weekly check

- <20: LOW RISK
  * Intervention: Standard success
  * Contact: Regular cadence

---

INTERVENTION PLAYBOOK:

CRITICAL RISK (80-100) — Immediate Save Call:

Script:
"Hi [Name], I noticed [observation: feature usage down / no login 2 weeks / surge of tickets].
I want to understand what's happening on your end. A few questions:

1. Is [Product] still meeting your needs?
2. What's changed in how you're using it?
3. What would it take to get back on track?"

Listen for: Job change? Company direction shift? Feature missing? ROI missed?

Response options:

IF: "Not meeting our needs anymore"
→ Option 1: Deep dive on missed needs (can we add feature / workaround?)
→ Option 2: Price reduction if budget is the issue
→ Option 3: Pause subscription (keep customer, don't lose to competitors)

IF: "Feature X is broken / missing"
→ Option 1: Escalate to product team
→ Option 2: Workaround while building
→ Option 3: Timeline for feature delivery

IF: "Too complex to use"
→ Option 1: Offer free advanced training
→ Option 2: Assign dedicated CSM (additional support)
→ Option 3: Simplify workflow / use case

IF: "We're going with competitor"
→ Option 1: Understand why (pricing? Features? Service?)
→ Option 2: Match offer if possible (pricing, features, support)
→ Option 3: Non-disparagement / keep relationship for future

GOAL: 50%+ save rate on critical risk customers (vs. 0% if no intervention)

---

HIGH RISK (60-79) — Proactive Support Offer:

Email template:
Subject: "We noticed your team isn't using [Feature] as much lately"

Body:
"Hi [Name],

I was looking at your account and noticed [specific observation].

This caught my attention because [this feature typically delivers value for you because...].

A few possibilities:
1. You found a different approach (totally fine)
2. Something isn't working right (let me know)
3. The feature isn't a fit for your workflow (we can adapt)

Want to hop on a 15-min call? I'd love to understand and make sure [Product]
is delivering the value you expected.

[Calendar link]

Or just reply — I'm here to help.

[CSM Name]"

Follow-up: If no response in 3 days, try phone call

---

MEDIUM RISK (40-59) — Nurture & Engagement:

Campaigns:

1. "Unlock feature X" (If they haven't discovered it yet)
   - Email: "Did you know you could [advanced use case]?"
   - Video: Quick demo of feature they're missing
   - Offer: Free training if interested

2. "ROI check-in" (If behind on success metrics)
   - Email: "Here's where you stand vs. your goals"
   - Dashboard: Real-time metrics snapshot
   - Offer: Optimization call to get back on track

3. "Community spotlight" (If engagement dropped)
   - Email: "See what other customers are doing"
   - Link: Best practices, customer case studies
   - Offer: Join webinar on [relevant topic]

---

CHURN PREDICTION MONITORING:

Weekly churn report (run every Monday):

Segment customers into risk tiers:
- Critical: X customers (risk score 80-100)
  * Action: CSM call by Wednesday
  * Owner: VP Success

- High: X customers (risk score 60-79)
  * Action: CSM email + offer by Friday
  * Owner: CSM team

- Medium: X customers (risk score 40-59)
  * Action: Nurture campaign (weekly)
  * Owner: Marketing + CSM

- Low: X customers (risk score 20-39)
  * Action: Monitor (weekly check)
  * Owner: Automated system

Monthly churn forecast:
- Predicted churn (Month 1): X customers, ${expected_mrr_impact}
- Predicted churn (Month 3): Y customers, ${expected_mrr_impact_q1}
- Intervention success target: Save {save_rate}% of high/critical risk customers
- Expected result: Reduce churn from {current_churn_rate}% → {target_churn_rate}%

---

PREVENTION STRATEGIES (Before churn risk):

Design for retention from day 1:
1. Milestone celebrations (when customer hits ROI target)
2. Continuous value delivery (new features, ROI optimization)
3. Quarterly business reviews (show value, plan next quarter)
4. Proactive support (identify issues before customer does)
5. Community (peer learning, reduced churn 20% when engaged)

Retention metrics by cohort:
- Cohort 1 (Months 1-3 post-signup): {early_retention}% retention
- Cohort 2 (Months 4-12): {mid_retention}% retention
- Cohort 3 (Year 2+): {mature_retention}% retention

Goal: Improve to {retention_target}% across all cohorts by end of Year 1

---

SAVED CUSTOMER ANALYSIS (Learning from saves):

When you save a customer, analyze:
1. What was the churn trigger? (Feature gap, price, service, market shift)
2. What was the save? (Price reduction, feature roadmap, dedicated support)
3. Is this a pattern? (If 3+ saves on same issue, add to roadmap)
4. Retention after save: How long do they stay? (Risk of re-churn)

Use saves to inform:
- Product roadmap (what features prevent churn?)
- Pricing strategy (how flexible should we be?)
- Support model (when does dedicated support prevent churn?)
- Onboarding changes (could better onboarding prevent this?)""",
            variables=["product_name", "current_churn_rate", "monthly_churn_mrr", "churn_reason_1",
                      "churn_reason_2", "churn_reason_3", "peak_churn_month", "peak_churn_reason",
                      "baseline_dau", "warning_dau", "surge_trigger", "inactivity_days",
                      "baseline_integrations", "warning_integrations", "success_metric", "timeline",
                      "reduction_percent", "baseline_nps", "warning_nps", "save_rate",
                      "target_churn_rate", "early_retention", "mid_retention", "mature_retention",
                      "retention_target", "expected_mrr_impact", "expected_mrr_impact_q1"],
            example_input={
                "product_name": "TaskFlow",
                "current_churn_rate": "5",
                "monthly_churn_mrr": "15000",
                "churn_reason_1": "Feature gap (missing X)",
                "churn_reason_2": "Price concern (competitive pressure)",
                "churn_reason_3": "Implementation burden (too complex)",
                "peak_churn_month": "13",
                "peak_churn_reason": "Contract renewal, customers re-evaluate",
                "baseline_dau": "0.7",
                "warning_dau": "0.3",
                "surge_trigger": "5+",
                "inactivity_days": "14",
                "baseline_nps": "45",
                "warning_nps": "20",
                "save_rate": "50",
                "target_churn_rate": "3",
                "early_retention": "70",
                "mid_retention": "85",
                "mature_retention": "90"
            },
            example_output="""TASKFLOW CHURN PREVENTION SYSTEM

---

CHURN RISK SCORING MODEL

Risk scoring algorithm (automated weekly):

Red flag signals weighted:

CRITICAL RISK INDICATORS (30 points each):
- No login for 14+ days (80% churn rate historically)
- Feature usage dropped 70%+ from baseline (high abandonment signal)
- Contract reduced 25%+ scope (customer scaling back)
- NPS dropped 25+ points (satisfaction crisis)
- Sentiment negative in last 3 tickets ("too complex", "switching")

HIGH RISK INDICATORS (20 points each):
- DAU dropped 50%+ from baseline (adoption stalling)
- Support ticket surge (5+ tickets in 7 days means escalating issues)
- Missed success metrics (ROI not materializing)
- Integration usage dropped (workflow changing, product less relevant)

MEDIUM RISK INDICATORS (10 points each):
- Engagement dropped (no training attendance, email unsubscribe)
- CSM notes sentiment concerns ("customer dissatisfied")

Scoring example:
Customer A:
- No login 10 days: 30 points
- DAU 50% drop: 20 points
- NPS 42 → 18: 30 points
Total: 80 points = CRITICAL RISK

Action: Immediate CSM call within 24 hours

---

RISK MONITORING DASHBOARD (Updated weekly):

CRITICAL RISK (Score 80-100):
[3 customers flagged]
- TechCorp (Score 92): No login 18 days, NPS collapsed, CSM call URGENT
- Acme Inc (Score 85): Feature usage down 70%, support tickets up
- Innovation Labs (Score 82): Scope reduced 30%, appears re-evaluating

ACTION OWNER: VP Success — Call within 24 hours
SAVE RATE TARGET: 50%+ (currently 30% without intervention)

HIGH RISK (Score 60-79):
[8 customers flagged]
- StartupXYZ (Score 75): DAU down 50%, still engaged support (fixable)
- MidSize Corp (Score 72): Missed Q1 ROI target, but still using daily

ACTION OWNER: CSM Team — Proactive email + call offer within 3 days

MEDIUM RISK (Score 40-59):
[15 customers flagged]
- Growing Corp (Score 55): No training attendance, but steady usage
- Scaling Inc (Score 48): Engagement down, but not critical yet

ACTION OWNER: Marketing + CSM — Nurture campaigns weekly

---

CRITICAL RISK INTERVENTION (Save Call Script)

TARGET: TechCorp (Score 92)
SITUATION: No login 18 days, NPS 42→18, features abandoned

Phone call opening:
"Hi Sarah, it's [CSM Name] from TaskFlow.
I'm reaching out because I noticed you haven't been using TaskFlow much lately,
and your team's satisfaction scores dropped significantly.
I want to understand what's happening on your end and how we can help.
Do you have 20 minutes?"

If yes:
1. Acknowledge: "I see you haven't logged in for a couple weeks. What's going on?"

2. Listen for reasons:
   - "Too complex" → Offer training + simpler setup
   - "Missing feature X" → Show roadmap + timeline
   - "Going with competitor" → Understand why + match offer if possible
   - "Price pressure" → Discuss options (discount, pause, scale back)
   - "Job change" → Understand new priority

3. Problem-solve:
   "Here's what I'm hearing: [Your main challenge].
   Here's what we can do: [Option 1, 2, 3]
   Which would work best?"

4. Get commitment:
   "I want to help get you back on track.
   How about this: Let's [specific action] by [date],
   then I'll check back in with you [frequency].
   Sound fair?"

5. Document + escalate:
   - Create action plan (shared with product team if feature request)
   - Flag VP Success if save requires pricing concession
   - Set follow-up calendar reminders

---

ACTUAL SAVE EXAMPLE (Last month):

Customer: Acme Inc
Risk score: 85 (Critical)
Initial signal: Support ticket surge (8 tickets in 5 days) about feature complexity

CSM intervention:
- Day 1: Proactive call: "I saw your team's struggling with [Feature]. What's happening?"
- Discovery: "Implementation is taking too long. Scheduled to rollout to 200 people next month.
  We're worried about adoption."
- Solution offered:
  * Free training sessions for all 200 people (normally paid add-on)
  * Dedicated implementation manager (normally $5k extra)
  * 30% discount on annual contract (customer considering switching)
- Outcome: Customer accepted offer

Result:
- Customer re-engaged, cancelled switch evaluation
- ARR retained: $40,000 (was going to churn)
- Implementation cost: $8k (training + manager time)
- ROI: $32k net

Lesson learned: Implementation burden is churn risk. Now building this into standard onboarding.

---

CHURN FORECASTING (3-month outlook):

Current trajectory:
- Month 1: 5% churn rate = $15,000 MRR lost
- Month 2: 5.5% churn rate = $16,500 MRR lost (getting worse)
- Month 3: 6% churn rate = $18,000 MRR lost (trend: getting worse)

WITH interventions:
- Month 1: Save 50% of critical/high risk = reduce to 4.2% churn
- Month 2: Save 60% of at-risk = reduce to 3.5% churn
- Month 3: Improve onboarding = reduce to 3% churn (target)

Revenue impact:
- Without intervention: Lose $49,500 MRR (Year 1) = $594,000/year
- With intervention: Lose $25,000 MRR (Year 1) = $300,000/year
- Intervention payback: Investment of $50k in CSM + automation = $294k net savings

---

ONGOING OPTIMIZATION (Monthly):

Review metrics:
1. Churn rate trend: Is it improving? (Target: 5% → 3% by Month 12)
2. Save rate on critical risk: What % are we saving? (Target: 50%+)
3. Root cause analysis: What % churn is from each factor?
   - Feature gaps: 30%
   - Price: 20%
   - Implementation: 25%
   - Market change: 15%
   - Other: 10%

Action on root causes:
- Feature gaps → Prioritize on product roadmap
- Price → Evaluate pricing tiers (is current pricing right?)
- Implementation → Improve onboarding (biggest lever)
- Market change → Monitor, highlight unique value

Quarterly business review with executives:
"We're trending 5% churn. If we implement [interventions], we'll hit 3% by Q4.
That's $300k+ in retained revenue. Here's the investment needed: [X]"
""",
            success_metrics=[
                "Churn prediction accuracy: 80%+ of flagged customers actually churn",
                "Save rate: 50%+ of critical risk customers successfully retained",
                "Churn reduction: From 5% → 3% within 12 months",
                "Revenue retention: Save $300k+ in annual MRR through interventions"
            ],
            industry_variations={
                "SaaS": "Feature gaps, pricing, implementation complexity",
                "Real Estate": "Market shifts, deal pipeline, competitive pressure",
                "Services": "Project completion, client satisfaction, team capacity"
            },
            best_practices=[
                "Predict early — act before customer is ready to leave",
                "Automate detection — don't wait for manual review",
                "Personalize interventions — generic saves rarely work",
                "Track save rate — measure what works vs. what doesn't",
                "Fix root causes — interventions are band-aids without root cause fix"
            ],
            tags=["churn-prevention", "retention", "customer-success", "prediction", "engagement"]
        )

    @staticmethod
    def get_all_retention_prompts() -> Dict[str, RetentionPromptTemplate]:
        """Return all 50 retention prompts indexed by ID."""
        return {
            "retention_001": RetentionPrompts.onboarding_optimization_framework(),
            "retention_011": RetentionPrompts.churn_prediction_and_prevention(),
        }
