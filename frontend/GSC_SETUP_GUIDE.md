# Google Search Console - Setup & Sitemap Submission Guide
**Date:** 2026-08-08  
**URL:** https://sellia-brain.vercel.app  
**Sitemap:** https://sellia-brain.vercel.app/sitemap.xml  
**Robots.txt:** https://sellia-brain.vercel.app/robots.txt (dynamic)

---

## 📋 STEP 1: Access Google Search Console

### Option A: Direct Link
```
https://search.google.com/search-console
```

### Option B: Google Account
1. Go to Google Search Console
2. Sign in with your Google account
3. If no account yet, create one (use company email recommended)

---

## ✅ STEP 2: Add/Verify Property

### 2.1 Click "Add Property" or Use URL Prefix

**Recommended: URL Prefix Method**
```
Property type: URL prefix
Enter: https://sellia-brain.vercel.app
Click: Continue
```

### 2.2 Verify Ownership (Choose One Method)

#### Method A: DNS Record (Recommended for Vercel)
```
1. Click: "DNS record" verification method
2. Copy TXT record: v=google-site-verification=xxx...
3. Go to your domain registrar (GoDaddy, Namecheap, Route 53, etc)
4. Add DNS TXT record with value from GSC
5. Return to GSC, click "Verify"
6. Wait 5-60 minutes for DNS propagation
```

#### Method B: HTML File
```
1. Click: "HTML file" verification method
2. Download verification file: google[hash].html
3. Upload to: frontend/public/google[hash].html
4. Deploy to Vercel
5. GSC will check: https://sellia-brain.vercel.app/google[hash].html
6. Click "Verify" in GSC
```

#### Method C: HTML Tag (Fast)
```
1. Click: "HTML tag" verification method
2. Copy meta tag from GSC
3. Add to: src/app/layout.tsx
   <meta name="google-site-verification" content="xxx" />
4. Redeploy frontend
5. Return to GSC, click "Verify"
```

**→ Choose Method A or C (fastest)**

---

## 📝 STEP 3: Submit Sitemap

### 3.1 Navigate to Sitemaps Section
```
GSC Dashboard → Left sidebar
Click: "Sitemaps" (under "Index" section)
```

### 3.2 Enter Sitemap URL
```
Input field: "Add a new sitemap"
Enter: https://sellia-brain.vercel.app/sitemap.xml
Click: "Submit"
```

### 3.3 Monitor Submission
```
Status should show:
✓ Submitted (pending)
→ Sitemaps index (auto-refreshes)

Refresh page to see status update
Expected: "Success" after 1-5 minutes
```

### 3.4 Verify Sitemap Content
```
GSC → Sitemaps → Click sitemap URL
Should show:
- Status: "Success"
- Submitted URLs: 6
- Indexed URLs: 0-6 (building over time)
- Errors: 0 (no errors)
```

---

## 🔗 STEP 4: Monitor URL Indexation

### 4.1 Go to Coverage Report
```
GSC Dashboard → "Coverage" (under "Index")
```

### 4.2 Check Indexation Status
```
Expected breakdown:
- Valid (indexed): 0-6 URLs
- Excluded: 0 URLs
- Error: 0 URLs
- Valid with warnings: 0 URLs
```

### 4.3 Check Individual URLs
```
GSC → Coverage
Click: "Indexed" tab
Should see:
✓ https://sellia-brain.vercel.app
✓ https://sellia-brain.vercel.app/sellia-brain
✓ https://sellia-brain.vercel.app/privacy
(others as indexed over time)
```

### 4.4 Request Indexation (Speed Up)
```
For each URL:
1. Click URL in Coverage
2. Click: "Request indexing"
3. GSC will crawl immediately
4. Status: "Queued for crawl" → "Indexed" (1-48h)
```

---

## 🔍 STEP 5: Validate Robots.txt & Sitemaps

### 5.1 Test Robots.txt
```
GSC → "Settings" (gear icon, top right)
Click: "Test robots.txt"

Select paths to test:
- /
- /sellia-brain
- /api/v1/auth
- /admin

Expected:
✓ / → Allowed
✓ /sellia-brain → Allowed
✓ /api/v1/auth → Blocked
✓ /admin → Blocked
```

### 5.2 Validate Structured Data
```
GSC → Left sidebar → "Enhancement"
Click: "Rich results" or "Structured data"

Should show:
✓ SoftwareApplication (if parsing correct)
- Name: SellIA Brain
- Type: BusinessApplication
- Features: 6 listed

If errors appear:
1. Check JSON-LD in page source
2. Use: https://validator.schema.org/
3. Fix issues in src/app/sellia-brain/layout.tsx
4. Redeploy
```

---

## 📊 STEP 6: Monitor Core Web Vitals

### 6.1 Access Web Vitals Report
```
GSC Dashboard → "Core Web Vitals" (under "Enhancements")
```

### 6.2 Review Metrics
```
Expected Good Metrics:
- LCP (Largest Contentful Paint): < 2.5s
- FID (First Input Delay): < 100ms
- CLS (Cumulative Layout Shift): < 0.1

If issues:
1. Click metric to see affected pages
2. Use PageSpeed Insights for details
3. Optimize per recommendations
4. Resubmit after fixes
```

### 6.3 Benchmark Against Industry
```
GSC shows:
- "Good" (green): meets Core Web Vitals thresholds
- "Needs improvement" (yellow): borderline
- "Poor" (red): fails thresholds

Target: 100% Good
```

---

## 🚨 STEP 7: Check for Crawl Errors

### 7.1 View Crawl Stats
```
GSC → Settings → "Crawl statistics"

Monitor:
- Requests per day: Should increase as indexation grows
- Crawl budget: Vercel limits crawl to reasonable rate
- Errors: Should be 0
```

### 7.2 Check for Issues
```
GSC → Left sidebar → "Indexing"
Click: "Pages" or "Enhancements"

If issues appear:
- 404s: Investigate URL existence
- Server errors (5xx): Check Vercel logs
- Redirects: Ensure redirects work
- Coverage issues: Update robots.txt/metadata
```

---

## 📅 STEP 8: Set Up Manual Sitemap Refresh

### 8.1 Automatic Refresh
```
GSC monitors sitemap.xml automatically
No action needed on your side
Updates detected: Every 24-48 hours
```

### 8.2 Force Refresh (Optional)
```
When you update content:
1. GSC → Sitemaps
2. Click sitemap URL
3. Click: "Request re-crawl" (if available)
4. OR navigate to page and use URL inspection tool
```

---

## 🔐 STEP 9: Configure Verification & Security

### 9.1 Manage Team Access
```
GSC → Settings (gear) → "Users and permissions"
Add team members:
- Admin: Full access
- Editor: Can view data, submit URLs
- Analyst: Read-only access
```

### 9.2 Link Analytics
```
GSC → Settings → "Google Analytics"
Connect your GA4 property:
1. Select property from dropdown
2. Confirm association
3. Enables: GSC data in GA4, GA4 insights in GSC
```

### 9.3 Link to Google Business Profile
```
GSC → Settings → "Google Business Profile"
If you have local business presence:
1. Select profile
2. Confirm association
```

---

## 📈 STEP 10: Monitor Rankings & Traffic

### 10.1 Performance Report
```
GSC Dashboard → "Performance" (top tab)
Shows:
- Clicks (traffic from search)
- Impressions (shown in search results)
- CTR (click-through rate)
- Average position (ranking)

Filter by:
- Date range: Last 90 days (default)
- Country: Search traffic geography
- Device: Mobile vs Desktop vs Tablet
- Search type: Web, News, Image, Video
```

### 10.2 Track Target Keywords
```
Performance → Position column
Sort by "Position" ascending

Top ranking keywords:
- Position 1-10: High value
- Position 11-30: Improvement potential
- Position 31-100: Long-tail opportunities

Growth strategy:
1. Content update for position 11-30 → Move to top 10
2. Backlink building for position 31-100 → Move to top 20
```

### 10.3 Monitor CTR
```
If impressions high but clicks low (low CTR):
- Title may be unattractive
- Meta description needs improvement
- Position may be too low (8-10)

Actions:
- Refresh title/description
- Optimize for better position
- Add structure markup for featured snippets
```

---

## ⚠️ COMMON ISSUES & SOLUTIONS

### Issue 1: Sitemap Shows "Error"
```
Cause: Invalid XML, wrong URL
Solution:
1. Check: https://sellia-brain.vercel.app/sitemap.xml
2. Should display valid XML (not 404)
3. Verify sitemap.ts route handler is deployed
4. Check: curl https://sellia-brain.vercel.app/sitemap.xml
```

### Issue 2: "Not Found" in Coverage
```
Cause: Page exists but not indexed
Solution:
1. Use "URL Inspection" tool (GSC)
2. Enter: https://sellia-brain.vercel.app/sellia-brain
3. Click: "Request indexing" if available
4. Wait 24-48 hours
5. Monitor Coverage report
```

### Issue 3: Robots.txt Blocking /sellia-brain
```
Cause: Old static robots.txt cached
Solution:
1. Vercel deployed new dynamic robots.ts
2. Verify with: curl https://sellia-brain.vercel.app/robots.txt
3. Should show: Allow: /sellia-brain
4. GSC will re-crawl after verification
5. Check robots.txt test in GSC → Settings
```

### Issue 4: Structured Data Not Recognized
```
Cause: JSON-LD malformed
Solution:
1. Use: https://validator.schema.org/
2. Paste page source
3. Fix reported errors
4. Redeploy
5. GSC will re-process (24-48h)
```

### Issue 5: Low CTR Despite High Position
```
Cause: Title/description unattractive
Solution:
1. Review in GSC → Performance
2. Click query to see current title/description
3. Update metadata in src/app/sellia-brain/layout.tsx
4. Make more compelling + include keyword
5. Redeploy
6. Wait 2-4 weeks for ranking recovery
```

---

## 📞 MONITORING SCHEDULE

### Weekly (Every Monday)
```markdown
- [ ] Check Coverage report (new indexed URLs)
- [ ] Review Performance top queries
- [ ] Monitor Core Web Vitals status
- [ ] Check for new crawl errors
```

### Monthly (1st of month)
```markdown
- [ ] Analyze Performance trends (last 30 days)
- [ ] Review keyword rankings movement
- [ ] Check backlink growth (via GSC "Links")
- [ ] Plan content updates based on data
```

### Quarterly (Every 3 months)
```markdown
- [ ] Full SEO audit (Lighthouse + GSC)
- [ ] Backlink strategy review
- [ ] Competitor analysis
- [ ] Update roadmap based on data
```

---

## 🎯 SUCCESS METRICS

### Indexation Success
```
Target timeline: 2-4 weeks
- Week 1: 1-2 URLs indexed
- Week 2: 3-4 URLs indexed
- Week 3-4: All 6 URLs indexed ✓
```

### Traffic Success
```
Target timeline: 1-3 months
- Month 1: 10-50 clicks from organic search
- Month 2: 50-200 clicks
- Month 3: 200-500 clicks

Depends on: Competition, keyword difficulty, backlinks
```

### Ranking Success
```
Target timeline: 1-6 months
- Month 1: Position 30-50 (long-tail keywords)
- Month 2: Position 20-40 (medium keywords)
- Month 3-6: Position 10-20 (competitive keywords)

Note: Timelines vary by keyword difficulty
```

---

## 🔗 USEFUL GSC TOOLS

| Tool | Purpose | Location |
|------|---------|----------|
| URL Inspection | Debug single page | Magnifying glass, top |
| Test robots.txt | Verify allow/block | Settings → Test robots.txt |
| Test robots rules | Check specific path | Settings → Test robots rules |
| Fetch as Google | See page as crawler | (Legacy, use URL inspection) |
| Removals | Temporarily hide URL | Coverage → Manage removals |
| Security Issues | Check malware/hacking | (If applicable) |
| Core Web Vitals | Performance metrics | Enhancements → CWV |
| Rich Results | Structured data | Enhancements → Rich results |

---

## 📞 SUPPORT

### If Verification Fails
```
1. Try different verification method
2. Wait 24 hours (DNS propagation)
3. Contact Google Support:
   https://support.google.com/webmasters/
```

### If Sitemap Error
```
1. Verify sitemap.xml returns 200:
   curl https://sellia-brain.vercel.app/sitemap.xml
   
2. Check structure with:
   https://www.xml-sitemaps.com/validate-xml-sitemap.html
   
3. Submit again
```

### Resources
```
Google Search Central: https://developers.google.com/search
Search Console Help: https://support.google.com/webmasters/
SEO Starter Guide: https://support.google.com/webmasters/answer/7340
```

---

**Document Version:** 1.0  
**Last Updated:** 2026-08-08  
**Status:** Ready for implementation
