# Beta User Onboarding - v1.0.0

**Welcome to Sellia Beta!** 🎉

We're launching v1.0.0 with you. This 2-week beta tests critical features before full production launch. Your feedback directly shapes the product.

---

## Day 1: Access Setup

### Email Template
Subject: Access Your Sellia Beta Account - v1.0.0

---

Welcome to Sellia Beta! 🚀

We're excited to have you test drive v1.0.0 with us. This early access gives you first-look at major new features:

✨ **What's New in v1.0.0:**
- Real-time team collaboration (comments, @mentions, approvals)
- Native mobile app (iOS + Android, works offline)
- Deal intelligence (win probability, forecasting, risk dashboard)
- AI voice agent (outbound calling, transcription)
- Workflow automation (8 actions, conditional logic)
- Advanced analytics & reporting (custom dashboards, data exports)

📋 **Your Beta Details:**
- Beta ID: `[USER_ID]`
- Cohort: `[Sales | Operations | Mobile | Voice]`
- Access URL: `https://app.production.com?beta=true`
- Duration: August 12-25, 2026
- Slack channel: `#beta-testing`

🔑 **Getting Started:**
1. Use your existing login (username + password)
2. Check Slack for #beta-testing channel invite
3. Attend optional 30-min onboarding session (details below)
4. Report issues + feedback in Slack

❓ **Questions?**
- Onboarding: Reply to this email
- Technical issues: #beta-testing on Slack
- Feature requests: Reply in thread

We appreciate your early adoption. Let's make v1.0.0 great together!

---Lucas
Product Lead, Sellia

---

### Access Checklist
- [ ] Email sent to user
- [ ] Account activated in production
- [ ] Slack #beta-testing invite sent
- [ ] API key generated (if integrations needed)
- [ ] Onboarding session scheduled (optional)

---

## Day 2: Onboarding Session (30 min)

### Agenda

**Intro (5 min)**
- Welcome + what we're testing
- How feedback is used
- What happens after beta

**Product Tour (15 min)**

1. **Dashboard** (KPIs + real-time metrics)
   - Walk through analytics dashboard
   - Show pipeline summary
   - Explain metrics (calls, deals, revenue)

2. **Collaboration** (comments + approvals)
   - Show deal comments in action
   - Demo @mentions
   - Walk through approval workflow
   - Show activity feed

3. **Mobile App** (if iOS/Android beta)
   - Show app installation (TestFlight/Play)
   - Walk through main screens
   - Explain offline mode
   - Test push notifications

4. **Integrations** (Salesforce/HubSpot)
   - Show sync setup
   - Verify contact import
   - Explain 2-way sync

5. **Voice** (if Cohort D)
   - Show call interface
   - Make test call demo
   - Explain transcription
   - Review call history

**Test Scenarios (10 min)**
- Assign specific test tasks (see below)
- Answer questions
- Review reporting process

---

## Day 3: Go Live

### Kickoff Checklist
- [ ] User attended onboarding (or watched recording)
- [ ] Test account setup (5 sample deals created)
- [ ] First task assigned
- [ ] Slack notifications enabled
- [ ] Daily check-in scheduled

### Test Tasks (Pick 3-5 for your cohort)

**Collaboration Tests**
- [ ] Create deal + add 3 comments
- [ ] @mention teammate (verify notification)
- [ ] Create approval (request sign-off)
- [ ] Move deal to next stage + verify activity feed
- [ ] Share deal with 2 teammates

**Mobile Tests** (Cohort C)
- [ ] Download from TestFlight/Google Play
- [ ] Login with beta credentials
- [ ] View dashboard on phone
- [ ] Check 5+ deals in pipeline
- [ ] Test offline mode (turn off WiFi, use app, turn on WiFi)
- [ ] Approve action via push notification
- [ ] Search for deal

**Voice Tests** (Cohort D)
- [ ] Make 3 outbound calls
- [ ] Record call + verify recording plays
- [ ] Check call transcript
- [ ] Review sentiment analysis
- [ ] Verify call shows in call history

**Integration Tests** (Cohort B)
- [ ] Connect Salesforce account
- [ ] Sync 20+ contacts
- [ ] Create deal from synced contact
- [ ] Run workflow (deal created → send email)
- [ ] Export deals as CSV
- [ ] Create custom dashboard widget

**Forecasting Tests** (All)
- [ ] View deal win probability
- [ ] Check 30/60/90-day revenue forecast
- [ ] Identify at-risk deals
- [ ] Review forecast accuracy

---

## Daily Standup (5 min async)

Post in `#beta-testing` Slack channel:

```
[STATUS] ✅ Progressing | ⚠️ Blocked | ❌ Issue found

[COHORT] Sales | Operations | Mobile | Voice

[DONE TODAY]
- Task 1 ✅
- Task 2 ✅

[BLOCKED BY]
- None

[ISSUE] (if any)
[SEVERITY] Critical | High | Medium | Low
[DESCRIPTION] What happened?
[STEPS] How to reproduce?
```

**Response SLA**: Team replies within 2 hours (business hours)

---

## Weekly Feedback Survey (Friday)

**5-minute survey** (Slack):

```
1. Overall satisfaction: 1-10 (1=frustrated, 10=thrilled)

2. Feature readiness (%):
   - Collaboration: _%
   - Mobile: _%
   - Voice: _%
   - Integrations: _%
   - Analytics: _%

3. Top 3 pain points:
   - Issue 1
   - Issue 2
   - Issue 3

4. Top 3 wins (what's working great?):
   - Win 1
   - Win 2
   - Win 3

5. Likelihood to recommend (1-10):
   - Score: _
   - Why: Brief explanation
```

---

## Weekly Feedback Call (Thursday 2pm UTC)

**30-minute call** with product + engineering + 3-4 beta users

**Agenda:**
- Top issues this week (live discussion)
- Workarounds deployed (if any)
- Roadmap adjustments based on feedback
- Q&A

**Link**: [Calendar invite sent separately]

---

## Issue Reporting Guide

### Format: Structured Issue Report

**Template** (post in #beta-testing):

```
[ISSUE] Brief title
[SEVERITY] P0 (Critical) | P1 (High) | P2 (Medium) | P3 (Low)
[COMPONENT] Collaboration | Mobile | Voice | Integrations | Analytics
[AFFECTED FEATURE] Feature name

[DESCRIPTION]
What happened? (2-3 sentences)

[STEPS]
1. Do this
2. Then this
3. See error

[EXPECTED]
What should happen?

[ACTUAL]
What actually happens?

[SCREENSHOT]
(Attach screenshot if visual bug)

[ENVIRONMENT]
- Device/OS: (if mobile)
- Browser: (if web)
- User role: Sales | Operations | Admin
- Time: When did it happen?
```

### Severity Levels

**P0 - Critical** (Fix within 4 hours)
- System unavailable
- Data loss or corruption
- Security breach
- Core feature broken (login, deals, calls)

**P1 - High** (Fix within 24 hours)
- Feature not working as expected
- Performance degraded significantly
- Workflow blocked
- Incorrect data

**P2 - Medium** (Fix within 1 week)
- UX friction (confusing flow)
- Minor bug (visual, typo)
- Performance issue (noticeable but not blocking)
- Missing documentation

**P3 - Low** (Backlog)
- Nice-to-have feature
- Polish/cosmetic issue
- Documentation gap
- Feature request

---

## Known Issues & Workarounds

### WebSocket Reconnection
**Issue**: Comments may show delayed (up to 30s) on poor connection
**Workaround**: Refresh page or wait for auto-reconnect
**Status**: Auto-reconnect every 5s, investigating performance improvement

### Voice Recording Upload
**Issue**: Recording file takes 1-2 min to appear
**Workaround**: None (async processing, check back in 2 min)
**Status**: Expected behavior, working as designed

### Large Data Exports
**Issue**: Exporting 100k+ rows may take 5+ minutes
**Workaround**: Use filters to reduce data, export in batches
**Status**: Investigating async processing improvements

### Mobile App Push Notifications
**Issue**: May miss notification on poor WiFi
**Workaround**: Check app manually for updates
**Status**: Known Firebase limitation, investigating alternative

### Workflow Execution Rate Limit
**Issue**: Only 10 workflows can run concurrently
**Workaround**: Schedule workflows at different times
**Status**: Investigating queue system for handling more

---

## Success Criteria

**Your beta is successful if:**
- ✅ You complete 3-5 test scenarios without blockers
- ✅ You find at least 1 bug or UX issue
- ✅ You attend 2/2 weekly feedback calls
- ✅ You fill out 2/2 weekly surveys
- ✅ You provide actionable feedback

---

## Incentives

**Thank you for beta testing!**

- ✨ **Exclusive access** to Phase 34 features before launch
- 🎁 **Swag** (shipped after beta)
- 💰 **Beta discount** (contact sales team)
- 📣 **Public recognition** (with your permission)
- 🔔 **Notification** when your feedback ships

---

## Timeline

| Date | Event |
|------|-------|
| Aug 12 | Access goes live, onboarding kicks off |
| Aug 13-18 | Week 1 testing, daily standups, Thu feedback call |
| Aug 20-25 | Week 2 testing, daily standups, Thu feedback call |
| Aug 25 (Fri) | Final survey + decision |
| Aug 26 (Mon) | Go/no-go decision + thank you |
| Aug 26 (Wed) | Full production launch to all users |

---

## Support

**Questions?**
- Slack: #beta-testing (response within 2 hours)
- Email: support+beta@sellia.app
- Call: Available for urgent issues (contact via Slack)

**Feedback ideas?**
- Post in #beta-testing
- Mention in weekly call
- Include in survey comments

---

## What Happens After Beta

**Week 3 (Aug 26):**
1. We analyze all feedback
2. Fix critical issues
3. Launch v1.0.0 to all users
4. Send thank-you + swag

**Ongoing:**
- Beta cohort gets early access to Phase 34
- Bi-weekly product updates
- Direct line to product team for feature requests

---

**You're helping shape the future of sales. Thank you!** 🙌

Questions before we start? Reply to this email or post in #beta-testing.

Let's go! 🚀
