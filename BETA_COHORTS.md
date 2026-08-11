# Beta Testing Cohorts - v1.0.0

**Program Start**: 2026-08-12  
**Program End**: 2026-08-25 (2 weeks)  
**Total Users**: 50-100 across 4 cohorts  
**Feedback Channel**: #beta-testing Slack  

---

## Cohort A: Enterprise Sales (20 users)

**Focus**: Deal collaboration, forecasting, mobile pipeline  
**Exit Criteria**: Close 50+ deals without critical issues  
**Onboarding**: Aug 12-13 (2 days)

### User Profile
- Sales executives + managers
- 5-20 years sales experience
- High deal velocity (10+ deals/month)
- Mobile power users
- Salesforce users

### Test Scenarios
```
[COLLAB-001] Team Comments
  1. Create deal "Acme Corp - $500k"
  2. Add comment "Need legal review"
  3. @mention teammate_name
  4. Verify: Comment real-time + @mention notification

[COLLAB-002] Approval Workflow
  1. Create discount request ($50k deal)
  2. Submit for approval
  3. Approver reviews + approves
  4. Verify: Decision visible to team + audit logged

[FORECAST-001] Deal Scoring
  1. View deal details
  2. Check win probability (should match stage + activity)
  3. Verify: Score updates when stage changes
  4. Compare: Manual estimate vs. AI score

[MOBILE-001] Pipeline on Phone
  1. Open mobile app
  2. View deals in pipeline
  3. Swipe to move deal (stage change)
  4. Verify: Updates sync to desktop in real-time

[MOBILE-002] Offline Mode
  1. Turn off WiFi
  2. Approve pending action (offline)
  3. Turn on WiFi
  4. Verify: Action queued + syncs when online
```

### Tasks (Pick 5)
- [ ] Create 5 deals (various stages)
- [ ] Add 10+ comments across deals
- [ ] Test 3 approval workflows
- [ ] Use mobile app for 50% of work
- [ ] Close 5 deals using app
- [ ] Test @mentions (3+ tags)
- [ ] Export deals as CSV
- [ ] View forecasting dashboard

### Daily Standup Format
```
[STATUS] ✅ Progressing | ⚠️ Minor issues | ❌ Blocked

[DEALS TODAY]
- Created: 3 deals
- Closed: 2 deals ($450k)
- Activities: 8 comments, 2 approvals

[WINS]
- Real-time collaboration working great
- Mobile app smooth + fast
- Win probability accurate (within 10%)

[ISSUES]
- [None] | [Issue title + steps]

[NEXT]
- Test voice calling (optional)
- Try workflow automation
```

---

## Cohort B: Sales Operations (15 users)

**Focus**: Workflows, reporting, data exports, integrations  
**Exit Criteria**: Run 20+ workflows, export 100k+ rows without errors  
**Onboarding**: Aug 12-13 (2 days)

### User Profile
- Operations managers
- Revenue operations analysts
- Data analysts
- Salesforce admins
- 3-10 years experience

### Test Scenarios
```
[WORKFLOW-001] Auto Email on Deal Created
  1. Create workflow: "If deal created → send email"
  2. Create new deal
  3. Verify: Email sent within 30 seconds
  4. Check: Email in Salesforce activity trail

[WORKFLOW-002] Update CRM on Stage Change
  1. Create workflow: "If stage = Closed Won → update Salesforce"
  2. Move deal to Closed Won
  3. Verify: Salesforce stage updated
  4. Check: Timestamp + actor logged

[INTEGRATION-001] Salesforce Sync
  1. Connect Salesforce (OAuth)
  2. Sync 50 contacts
  3. Create deal from synced contact
  4. Verify: Contacts appear in 5 min

[INTEGRATION-002] HubSpot Sync
  1. Connect HubSpot (API key)
  2. Verify contacts synced
  3. Map custom fields
  4. Verify: 2-way sync working

[EXPORT-001] Data Export CSV
  1. Filter deals: "Closed Won, Last 30 days"
  2. Export as CSV
  3. Verify: All columns present + data correct
  4. Check: File size matches row count

[EXPORT-002] Large Export
  1. Export all deals (100k+ rows)
  2. Monitor: Progress + time taken
  3. Verify: No timeout/errors
  4. Download + open in Excel
```

### Tasks (Pick 5)
- [ ] Create 5 workflows (different triggers)
- [ ] Connect Salesforce + HubSpot
- [ ] Run 10+ workflow executions
- [ ] Export deals (small + large datasets)
- [ ] Create custom dashboard (5 widgets)
- [ ] Test data filtering (10+ filters)
- [ ] Schedule 3 reports (daily/weekly/monthly)
- [ ] Test approval chains (3 levels deep)

### Daily Standup Format
```
[STATUS] ✅ Progressing | ⚠️ Performance issue | ❌ Integration failed

[WORKFLOWS RUN]
- Total executed: 12
- Success rate: 100%
- Avg duration: 2.5 seconds

[INTEGRATIONS]
- Salesforce: ✅ 50 contacts synced
- HubSpot: ✅ Connected
- Stripe: ⏳ Testing payment workflow

[ISSUES]
- [None] | [Issue: Large export takes 8 min]

[NEXT]
- Test Stripe integration
- Schedule reports
- Create BI connection
```

---

## Cohort C: Mobile Power Users (15 users)

**Focus**: iOS/Android app, offline mode, push notifications  
**Exit Criteria**: 50+ hrs app usage, offline mode tested, no crashes  
**Onboarding**: Aug 13-14 (delayed 1 day for app stabilization)

### User Profile
- Mobile-first sales reps
- High velocity (20+ activities/day)
- Remote workers
- iOS + Android users
- Push notification enabled

### Test Scenarios
```
[MOBILE-001] App Installation
  1. Download from TestFlight (iOS) or Google Play beta (Android)
  2. Install + launch
  3. Verify: Splash screen → login
  4. Check: App version matches v1.0.0

[MOBILE-002] Login & Auth
  1. Enter credentials
  2. Verify: 2FA (if enabled)
  3. Check: JWT token stored locally
  4. Verify: Token refresh works after 24hr

[MOBILE-003] Dashboard
  1. View KPI cards (deals, revenue, calls)
  2. Verify: Real-time updates (refresh every 30s)
  3. Check: Numbers match web dashboard
  4. Tap card → drill-down works

[MOBILE-004] Pipeline View
  1. Swipe between stages (Prospecting → Negotiating)
  2. View deals in each stage
  3. Tap deal → details load
  4. Verify: Smooth 60fps scrolling

[MOBILE-005] Offline Mode
  1. Enable WiFi, load deals
  2. Disable WiFi
  3. Scroll deals + view details (works offline)
  4. Approve pending action (queued)
  5. Enable WiFi
  6. Verify: Action syncs + appears on web

[MOBILE-006] Push Notifications
  1. Enable notifications
  2. Receive notification on web (create comment)
  3. Verify: Notification appears on phone within 3 sec
  4. Tap notification → app opens + shows deal
  5. Test: 5+ notifications

[MOBILE-007] Performance
  1. Measure app startup time (should be <3 sec)
  2. Measure screen load times (should be <1 sec)
  3. Check: Memory usage stable
  4. Monitor: No crashes during 50+ activities
```

### Tasks (Pick 5)
- [ ] Install on iOS + Android (both phones)
- [ ] Use app for 50+ hours total
- [ ] Test offline mode (10+ times)
- [ ] Receive 20+ push notifications
- [ ] Report 3+ crashes (if any)
- [ ] Test all 5 main screens
- [ ] Approve actions via mobile
- [ ] Test WiFi reconnection (toggle on/off 5x)

### Daily Standup Format
```
[STATUS] ✅ Rock solid | ⚠️ Minor UI issue | ❌ Crash on startup

[USAGE]
- Session time: 4 hours
- Activities: 25 (10 approvals, 15 views)
- Crashes: 0

[PLATFORMS]
- iOS (iPhone 14): ✅ 2 hours, smooth
- Android (Pixel 7): ✅ 2 hours, responsive

[FEATURES TESTED]
- ✅ Dashboard KPIs
- ✅ Pipeline swipe
- ✅ Offline mode (WiFi off 10x)
- ⚠️ Push notifications (3 sec delay)

[ISSUES]
- [None] | [Issue: Crash when offline + online simultaneously]

[NEXT]
- Test more offline scenarios
- Try deep linking
- Monitor battery drain
```

---

## Cohort D: Voice/Integration Team (10 users)

**Focus**: Twilio calling, voice transcription, CRM sync  
**Exit Criteria**: 100+ calls made, 50+ contact syncs, transcription accurate  
**Onboarding**: Aug 12-13 (2 days)

### User Profile
- Sales development reps (SDRs)
- High call volume (30-50 calls/day)
- CRM power users
- Salesforce admins
- Want voice analytics

### Test Scenarios
```
[VOICE-001] Make Outbound Call
  1. Open deal detail
  2. Click "Call" button
  3. Agent persona answers
  4. Have conversation (3+ min)
  5. Verify: Call logged with duration
  6. Check: Audio quality good

[VOICE-002] Call Recording
  1. Make 5 calls (record all)
  2. Verify: Recording appears in call history
  3. Click play → recording plays
  4. Download: Recording saves locally
  5. Check: File size matches duration

[VOICE-003] Transcription
  1. Complete call (recording enabled)
  2. Wait 2-3 min for transcription
  3. View transcript in call details
  4. Verify: Text matches audio (90%+ accuracy)
  5. Check: Timestamps match

[VOICE-004] Sentiment Analysis
  1. Review calls with sentiment scores
  2. Verify: Scores match conversation tone
  3. Filter by sentiment (positive/neutral/negative)
  4. Check: Correlation with deal outcome

[VOICE-005] CRM Logging
  1. Make call (recording + transcript)
  2. Verify: Activity logged in Salesforce
  3. Check: Duration, transcript, sentiment in activity
  4. Verify: Linked to correct contact

[VOICE-006] Call History
  1. Make 20+ calls
  2. View call history (list view)
  3. Sort by date/duration/sentiment
  4. Search by phone number
  5. Filter by status (completed/missed/transferred)

[VOICE-007] Performance
  1. Measure call connect time (should be <5 sec)
  2. Measure transcription time (should be <3 min)
  3. Make 50+ calls in 1 day
  4. Verify: No timeouts or errors
```

### Tasks (Pick 5)
- [ ] Make 100+ calls total
- [ ] Record 50+ calls
- [ ] Review transcriptions (check accuracy)
- [ ] Log calls to Salesforce (verify mapping)
- [ ] Test sentiment analysis (review 20+ scores)
- [ ] Sync 50+ contacts from Salesforce
- [ ] Create workflow: Call made → CRM update
- [ ] Test call transfer (if applicable)

### Daily Standup Format
```
[STATUS] ✅ Running smoothly | ⚠️ Transcription slow | ❌ Calls not recording

[CALLING]
- Calls made: 45
- Success rate: 98% (1 failed connect)
- Avg duration: 4:30
- Recordings: 45/45 (100%)

[TRANSCRIPTION]
- Transcribed: 35
- Avg time: 2.5 min
- Accuracy check: 92% match audio
- Issues: 3 bad audio files (unclear speech)

[CRM INTEGRATION]
- Contacts synced: 25
- Calls logged to Salesforce: 40
- Sentiment logged: 35/35
- Sync errors: 1 (bad email format)

[ISSUES]
- [None] | [Issue: Transcription takes 5+ min for long calls]

[NEXT]
- Make 50+ more calls
- Test call transfer
- Review sentiment accuracy
```

---

## Cohort Tracking

### Database Schema (If Tracked in System)
```sql
CREATE TABLE beta_cohorts (
  id UUID PRIMARY KEY,
  user_id VARCHAR(255),
  cohort_name VARCHAR(50),  -- A, B, C, D
  email VARCHAR(255),
  onboarding_date DATE,
  status VARCHAR(20),  -- active, completed, dropped
  hours_logged NUMERIC,
  tasks_completed INT,
  issues_found INT,
  satisfaction_score INT,  -- 1-10
  created_at TIMESTAMP
);

CREATE TABLE beta_feedback (
  id UUID PRIMARY KEY,
  cohort_id UUID,
  feedback_type VARCHAR(20),  -- daily, weekly, survey
  severity VARCHAR(20),  -- P0, P1, P2, P3
  title VARCHAR(255),
  description TEXT,
  steps_to_reproduce TEXT,
  created_at TIMESTAMP
);
```

### Slack Channel Setup

**#beta-testing**
- Daily standups (async posts)
- Issue reports (structured format)
- Quick questions + responses
- SLA: 2-hour response time

**#beta-cohort-a** (optional, for sales team)
- Cohort-specific discussions
- Shared wins + blockers

**#beta-cohort-b** (optional, for ops team)
- Workflow discussions
- Integration issues

**#beta-cohort-c** (optional, for mobile team)
- App performance discussions
- Device-specific issues

**#beta-cohort-d** (optional, for voice team)
- Call quality discussions
- Transcription feedback

---

## Daily Standup Checklist

**Each morning (async, 5-min post)**:
- [ ] What's your status? (Progressing | Minor issue | Blocked)
- [ ] What did you complete yesterday?
- [ ] What's your focus today?
- [ ] Any blockers or issues?
- [ ] Attach screenshot (if bug report)

**Format** (standardized for easy tracking):
```
[COHORT] A | B | C | D
[STATUS] ✅ | ⚠️ | ❌
[DONE] Task 1 ✅ Task 2 ✅
[ISSUES] None | [Brief description]
[TODAY] Task focus
```

---

## Weekly Feedback Call

**Thursday 14:00 UTC (30 min)**

**Attendees**:
- Product lead
- 2-3 engineers
- 3-4 beta users (1 from each cohort)

**Agenda**:
```
[00:00-05:00] Top issues this week
  - Review P0/P1 issues from Slack
  - Discuss workarounds deployed
  - Update status

[05:00-15:00] Feature discussions
  - What's working great?
  - What's confusing?
  - What's missing?

[15:00-20:00] Roadmap + next week
  - Share Phase 34 preview
  - Discuss feedback incorporation
  - Plan next week's focus

[20:00-30:00] Q&A + closing
  - Open questions
  - Confirm next week's tasks
```

---

## Weekly Survey (Friday)

**5-minute survey** (Slack poll + form):

```
1. Overall satisfaction: 1-10 scale
2. Likelihood to recommend: 1-10 scale
3. Top 3 pain points (free text)
4. Top 3 wins (free text)
5. Feature readiness:
   - Collaboration: % ready
   - Mobile: % ready
   - Voice: % ready
   - Integrations: % ready
   - Analytics: % ready
```

---

## Success Tracking Dashboard

**Metrics** (update daily):

| Cohort | Users | Hours | Tasks | Issues | Satisfaction | Status |
|--------|-------|-------|-------|--------|--------------|--------|
| A Sales | 20 | ? | ? | ? | ? | 🔴 SETUP |
| B Ops | 15 | ? | ? | ? | ? | 🔴 SETUP |
| C Mobile | 15 | ? | ? | ? | ? | 🔴 SETUP |
| D Voice | 10 | ? | ? | ? | ? | 🔴 SETUP |

---

## Go/No-Go Criteria (Aug 25)

**MUST HAVE (All required)**:
- [ ] Uptime > 99%
- [ ] Error rate < 1%
- [ ] All P0 issues fixed
- [ ] All P1 issues fixed or documented
- [ ] Mobile app functional (iOS + Android)
- [ ] Voice calling works end-to-end
- [ ] Integrations tested (Salesforce, HubSpot)
- [ ] User satisfaction > 7.5/10

**Decision Matrix**:
- ✅ All MUST HAVE → GO (full production launch)
- ⚠️ 1 MUST HAVE missed → EXTENDED BETA (+1 week)
- ❌ 2+ MUST HAVE missed → ROLLBACK (fix + retry)

---

**Beta program ready to launch. Onboarding begins 2026-08-12.**
