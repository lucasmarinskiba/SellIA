# Beta Testing Email Templates - v1.0.0

Copy-paste ready email templates for beta user invitations + onboarding.

---

## Email 1: Initial Invitation (Send Aug 11)

**Subject**: You're invited to test Sellia v1.0.0 early! 🚀

---

Hi [NAME],

We're excited to invite you to **Sellia Beta** — early access to v1.0.0 launching August 12th.

**What's new:**
- Real-time team collaboration (comments, @mentions, approvals)
- Native mobile app (iOS + Android, works offline)
- AI-powered deal intelligence (win probability, forecasting)
- Voice calling with transcription (Twilio integration)
- Workflow automation (8 actions, conditional logic)
- Advanced analytics & reporting (custom dashboards, CSV/Excel exports)

**Your beta access:**
- Start date: August 12, 2026
- Duration: 2 weeks
- Access: https://app.production.com?beta=true
- Cohort: [Sales | Operations | Mobile | Voice]

**Getting started:**
1. Confirm access (reply to this email)
2. Attend optional 30-min onboarding (link coming)
3. Check Slack for #beta-testing channel
4. Start testing + sharing feedback

**Why your feedback matters:**
Your input shapes the final product. Every bug report, feature request, and success story helps us ship v1.0.0 with confidence.

**What we need from you:**
- 50+ hours of active testing (over 2 weeks)
- Daily standup posts in #beta-testing (5 min)
- Weekly feedback survey (Friday)
- Attendance at Thursday feedback call (optional)

**Rewards:**
- ✨ Exclusive early access (Phase 34 features before launch)
- 🎁 Swag shipped after beta
- 💬 Direct line to product team
- 📣 Recognition in release notes (with permission)

**Questions before we start?**
Reply to this email or post in #beta-testing Slack.

Excited to have you! Let's build something great.

---
Lucas
Product Lead, Sellia

P.S. Mobile app TestFlight/Play beta links coming tomorrow.

---

## Email 2: Onboarding Session Details (Send Aug 11)

**Subject**: Your Sellia Beta Onboarding Session - Aug 12, 2pm UTC

---

Hi [NAME],

Thanks for confirming! Here's your onboarding session details:

**Session Details:**
- Date: August 12, 2026
- Time: 2:00 PM - 2:30 PM UTC
- Duration: 30 minutes
- Format: Zoom video call
- Link: [ZOOM_LINK]
- Organizer: Lucas (Product), [Engineer], [Designer]

**What we'll cover:**
1. Product tour (5 min)
   - Dashboard walkthrough
   - New features overview
   - Your cohort's focus area

2. Feature deep-dive (15 min)
   - Live demo of key features
   - How to report issues
   - Q&A on your use cases

3. Test scenario walkthrough (10 min)
   - Specific tasks for your cohort
   - Success criteria
   - Expected timeline

**What to bring:**
- Your laptop (browser login ready)
- Mobile device (optional, for mobile cohort)
- Notepad for taking notes

**Before the call:**
- [ ] Login to https://app.production.com (test access)
- [ ] Join #beta-testing Slack channel
- [ ] Download mobile app (TestFlight/Play) if in Cohort C
- [ ] Have your Salesforce/HubSpot credentials (if in Cohort B)

**Can't attend?**
No problem! We'll record the session and share a link after the call.

See you August 12th!

---
Lucas
Product Lead

Calendar invite: [ICS_FILE_ATTACHED]

---

## Email 3: Access Confirmed (Send Aug 12)

**Subject**: Your Sellia v1.0.0 Beta Access is Live! ✅

---

Hi [NAME],

Your beta access is now active. Log in anytime:

**Access Details:**
- URL: https://app.production.com?beta=true
- Username: [EMAIL]
- Password: Use your existing password (or reset if needed)
- 2FA: Enabled (approve from email)

**Test Account Setup:**
We've pre-created 5 sample deals for you to work with:
- Acme Corp - $500k (Prospecting)
- TechFlow - $250k (Negotiating)
- DataStream - $150k (Proposal)
- CloudSync - $300k (Closed Won)
- ApiHub - $200k (Closed Lost)

**Your first task:**
1. Login to app
2. View sample deals
3. Add comment on "Acme Corp" deal
4. Screenshot + post in #beta-testing: "I'm in! 🎉"

**Slack channel:**
All beta communication happens in #beta-testing:
- 💬 Daily standups (5-min posts)
- 🐛 Issue reports (structured format)
- ❓ Quick questions
- 📞 Support responses (< 2 hours)

**Mobile app** (Cohort C only):
- iOS: [TESTFLIGHT_LINK] (download via TestFlight app)
- Android: [GOOGLE_PLAY_BETA_LINK]
- Same credentials as web app

**Important links:**
- Runbook: https://github.com/lucasmarinskiba/SellIA/blob/main/BETA_TESTING.md
- Onboarding: https://github.com/lucasmarinskiba/SellIA/blob/main/BETA_USER_ONBOARDING.md
- Issue template: Post in #beta-testing with [ISSUE] format

**Next steps:**
- [ ] Login + test access
- [ ] Attend onboarding call (if registered)
- [ ] Read test scenarios for your cohort
- [ ] Start testing + posting daily updates

**Support:**
- Technical issues: #beta-testing Slack
- Account access: Reply to this email
- Urgent bugs: Page @on-call

Welcome to the beta! Let's ship v1.0.0 together 🚀

---
Lucas & Team
Sellia

---

## Email 4: Onboarding Complete (Send Aug 13)

**Subject**: Welcome to Sellia Beta! Your testing guide inside 📋

---

Hi [NAME],

Great job attending onboarding! Here's everything you need to crush your beta testing.

**Your cohort: [A | B | C | D]**
- Focus areas: [Collaboration | Workflows | Mobile | Voice]
- Exit criteria: [50 deals | 20 workflows | 50 hrs | 100 calls]
- Expected time: 50-100 hours over 2 weeks

**Your test scenarios:**
→ See attached: BETA_COHORTS.md (your cohort's section)

Pick 5 test scenarios to focus on this week. They're designed to:
- Cover critical features
- Find edge cases
- Validate performance
- Test integrations

**Daily routine (15 min/day):**
```
09:00 AM → Test feature (30-60 min)
05:00 PM → Post standup in #beta-testing (5 min)
Format:
  [STATUS] ✅ Progressing
  [DONE] Feature A, Feature B
  [ISSUES] None | [Issue title]
  [TODAY] Feature C focus
```

**Weekly rhythm:**
- Thursday 2pm UTC: Feedback call (optional but recommended)
- Friday: 5-min satisfaction survey
- Every day: Monitor #beta-testing for updates

**Issue reporting (when you find a bug):**

Post in #beta-testing with this format:
```
[ISSUE] Brief title (1 line)
[SEVERITY] P0 | P1 | P2 | P3
[COMPONENT] Collaboration | Mobile | Voice | Integrations | Analytics
[STEPS]
  1. Do this
  2. Then this
  3. See error

[EXPECTED] Should do X
[ACTUAL] Actually does Y
[SCREENSHOT] Attach if visual bug
```

**Known limitations (don't report these):**
- WebSocket reconnect takes up to 30s on poor WiFi
- Voice recording uploads async (1-2 min delay)
- Large exports (100k+ rows) take 5+ minutes
- Mobile app limited to 100 concurrent users
- Twilio calls limited to 50 simultaneous

**Success looks like:**
- ✅ Completing 5 test scenarios
- ✅ Finding 2-5 bugs (minor + major mix)
- ✅ Posting daily standups (10/14 days)
- ✅ Attending 1-2 feedback calls
- ✅ Survey submission (2/2 weeks)

**Timeline:**
```
Aug 12-13: Onboarding
Aug 14-19: Week 1 testing (daily standups)
Aug 20-25: Week 2 testing (daily standups)
Aug 25: Final survey
Aug 26: Go/no-go decision + thank you
```

**Questions?**
1. Post in #beta-testing (fastest)
2. Reply to this email (1-day response)
3. Schedule call with Lucas (email lucas@sellia.app)

Ready to test? Let's go! 🚀

---
Lucas
Product Lead

P.S. First person to find a P0 bug gets bonus swag 😉

---

## Email 5: Weekly Check-in (Send Every Friday)

**Subject**: Sellia Beta Week [X] - Survey + Next Week Preview

---

Hi [NAME],

Great work this week! Here's the weekly update + survey.

**This week's highlights:**
- 247 hours total testing logged
- 47 bugs reported (28 fixed, 19 in progress)
- Mobile app: 0 crashes (rock solid!)
- Voice calling: 489 calls made, 98.5% success rate
- Integrations: 100% sync success (Salesforce + HubSpot)
- User satisfaction: 8.2/10 average

**Your contribution:**
- Hours logged: [X] hours
- Tasks completed: [Y] tasks
- Issues found: [Z] issues
- Satisfaction score: ? (submit survey to update)

**Quick survey** (3 minutes):
→ [SURVEY_LINK]

Questions:
1. Overall satisfaction (1-10)
2. Feature readiness (% per feature)
3. Top 3 pain points
4. Top 3 wins
5. Recommend to others? (1-10)

**Next week focus:**
- Cohort A: Test approval chains + mobile updates
- Cohort B: Workflow performance + large exports
- Cohort C: Offline sync edge cases
- Cohort D: Call transfer + sentiment accuracy

**Metrics update:**
- Uptime: 99.8% ✅
- Error rate: 0.2% ✅
- Response time: 180ms (p95) ✅
- Cache hit rate: 94% ✅

**On track for Aug 26 launch?**
YES! No show-stoppers. All P0/P1 issues being addressed.

Keep up the great work! 🎉

---
Lucas & Team

---

## Email 6: Final Week Reminder (Send Aug 21)

**Subject**: Sellia Beta Week 2 - Last Push + Final Survey

---

Hi [NAME],

Final week of beta! Thanks for everything so far.

**Week 2 focus:**
- Polish edge cases found in Week 1
- Test any remaining scenarios
- Verify fixes for reported issues
- Wrap-up testing + final survey

**Final survey (Friday, Aug 25):**
This is our last feedback collection. Please be thorough:
- What worked great?
- What needs improvement?
- Would you use this in production?
- Any final bugs to report?

Survey link: [LINK] (takes 5 min)

**Final call (Thursday, Aug 22, 2pm UTC):**
Join Lucas + team for final feedback session:
- Review all feedback collected
- Discuss go/no-go decision
- Share Phase 34 preview
- Thank you + next steps

Zoom: [LINK] | Optional but encouraged

**After beta (Aug 26+):**
- ✨ Early access to Phase 34 (next month)
- 🎁 Swag arrives in September
- 💬 Direct Slack channel to product team
- 📣 Recognition in v1.0.0 release notes

**Count down:**
- 4 days of testing left
- 2 feedback sessions remaining
- 1 final survey

You're in the home stretch! 🏁

---
Lucas

---

## Email 7: Go/No-Go Decision (Send Aug 26)

**Subject**: Sellia v1.0.0 - GO FOR PRODUCTION LAUNCH! 🎉

---

Hi [NAME],

**The decision is in: GO FOR PRODUCTION LAUNCH!**

Your feedback + testing made v1.0.0 production-ready. Thank you! 🙌

**Final numbers:**
- 50-100 beta users
- 1,000+ hours of testing
- 156 bugs found + 154 fixed (99%)
- Avg satisfaction: 8.4/10
- Uptime: 99.8% (only 3 min downtime)
- Error rate: 0.15% (way below 1% target)
- Zero P0 issues at launch

**What launches Aug 26:**
- v1.0.0 to all production users
- Real-time collaboration
- Mobile app (App Store + Play Store)
- Voice calling (Twilio)
- Workflow automation
- Advanced analytics

**What's next for you:**
- ✨ Early access to Phase 34 (September)
- 🎁 Your swag is shipping this week
- 💬 Join exclusive #beta-success channel
- 📣 Check release notes — you're credited!

**Thank you email with swag link coming tomorrow.**

One more time: **THANK YOU** for making v1.0.0 amazing. Your real-world testing uncovered edge cases we never would have found in QA.

Let's celebrate! 🚀

---
Lucas & Team
Sellia

P.S. Keep an eye on #beta-success for Phase 34 sneak peeks starting next week.

---

## Email 8: Thank You + Swag (Send Aug 27)

**Subject**: Your Sellia Beta Swag is Coming! 🎁

---

Hi [NAME],

v1.0.0 is now live in production! Here's your thank-you.

**Your contribution:**
- Cohort: [A | B | C | D]
- Hours tested: [X]
- Bugs found: [Y]
- Feedback quality: ⭐⭐⭐⭐⭐

**Swag tracking:**
We're sending you: [Sellia T-Shirt + Mug + Sticker Pack]
Tracking: [FEDEX_LINK]
Delivery: 3-5 business days

**After beta perks:**
- ✨ Phase 34 early access (features release Aug 2026)
- 💬 #beta-success Slack channel (exclusive updates)
- 📞 Direct line to product team
- 🎤 Potential customer testimonial (optional)

**How are you already using Sellia?**
We'd love to feature your story. Reply with:
- Your role
- 1-2 wins from v1.0.0
- Quote (1-2 sentences)
- Photo (optional)

**What's coming next:**
- Phase 34 (September): GraphQL API + advanced ML
- Phase 35 (October): Multi-language support
- Phase 36 (Q4): Video calling via WebRTC

You'll get early previews! 🚀

**Stay connected:**
- Slack: #beta-success (exclusive channel)
- Twitter: Follow @selliacrm for updates
- Email: Subscribe to [NEWSLETTER_LINK]

**Questions?**
Reply to this email or post in #beta-success.

Thanks again for making v1.0.0 great. Can't wait to show you what's next!

---
Lucas & Team
Sellia

---

**All templates ready to use. Customize [BRACKETS] with actual values before sending.**
