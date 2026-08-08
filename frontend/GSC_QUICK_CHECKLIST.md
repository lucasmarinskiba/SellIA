# Google Search Console - Quick Setup Checklist
**Status:** Ready to Submit  
**Estimated Time:** 15-30 minutes  
**Date:** 2026-08-08

---

## ✅ PRE-SUBMISSION VERIFICATION

```
[✓] Sitemap live: https://sellia-brain.vercel.app/sitemap.xml
[✓] Robots.txt updated: https://sellia-brain.vercel.app/robots.txt
[✓] Metadata deployed: Title, OG, canonical all live
[✓] JSON-LD schema: SoftwareApplication deployed
[✓] All URLs accessible (no 404s expected)
```

---

## 📋 STEP-BY-STEP ACTIONS (Copiar/Pegar)

### 1️⃣ OPEN GOOGLE SEARCH CONSOLE
```
URL: https://search.google.com/search-console
Action: Sign in with Google Account
```

### 2️⃣ ADD PROPERTY
```
Click: "+ ADD PROPERTY" button (top left)
Select: "URL prefix" option
Enter: https://sellia-brain.vercel.app
Click: "Continue"
```

### 3️⃣ VERIFY OWNERSHIP (Choose ONE)

#### Option A: HTML Tag (FASTEST - 2 min)
```
GSC shows meta tag:
<meta name="google-site-verification" content="xxx..." />

1. Copy the entire tag
2. Open: frontend/src/app/layout.tsx
3. Paste in <head> section (after charset)
4. Git add + commit + push
5. Wait for Vercel deploy (2-5 min)
6. Return to GSC, click "VERIFY"
7. Status: Should show "Verified" ✓
```

#### Option B: DNS TXT Record (RECOMMENDED - 5-10 min)
```
GSC shows: v=google-site-verification=xxx...

1. Copy verification string
2. Go to your domain registrar (GoDaddy, Namecheap, Route 53, etc)
3. Add DNS TXT record:
   - Name: @ (or root)
   - Value: v=google-site-verification=xxx...
4. Save DNS record (takes 5-60 min to propagate)
5. Return to GSC, click "VERIFY"
6. Status: Should show "Verified" after propagation
```

**→ Use Option A for instant verification**

---

## 🗺️ SUBMIT SITEMAP

### After Verification ✓
```
1. GSC Dashboard (after verification complete)
2. Click: "Sitemaps" in left sidebar
   (Under "Index" section)
3. Field: "Add a new sitemap"
4. Enter: https://sellia-brain.vercel.app/sitemap.xml
5. Click: "SUBMIT"

Expected:
- Status: "Submitted"
- Submitted URLs: 6
- Indexed URLs: 0-6 (will grow over 1-4 weeks)
```

---

## 🔍 VALIDATE EVERYTHING

### Test Robots.txt (Verify Allow Rules)
```
1. GSC → Settings (gear icon, top right)
2. Click: "Test robots.txt"
3. Test these paths:
   - Path: / → Expected: Allowed ✓
   - Path: /sellia-brain → Expected: Allowed ✓
   - Path: /api/ → Expected: Blocked ✓
   - Path: /admin/ → Expected: Blocked ✓
4. All should show correct status
```

### Validate Structured Data
```
1. GSC → Enhancements → "Structured data"
   OR "Rich results" (depending on GSC version)
2. Should see:
   ✓ SoftwareApplication type
   ✓ Name: SellIA Brain
   ✓ Features: 6 listed
   ✓ 0 errors, 0 warnings

If errors appear:
- Use: https://validator.schema.org/
- Copy JSON-LD from page source
- Fix issues
- Redeploy
```

### Check Coverage (Indexation Status)
```
1. GSC → Coverage (under "Index")
2. Should show:
   - Valid (indexed): 0-1 immediately
   - Excluded: 0
   - Error: 0
3. Over 1-4 weeks:
   - Indexed should grow to 6 URLs
4. Click "Request indexing" button on important URLs
   to speed up indexation
```

---

## ⏱️ TIMELINE EXPECTATIONS

### Immediate (Today)
```
[✓] robots.txt updated with /sellia-brain allowed
[✓] Sitemap submitted to GSC
[✓] Verification in progress
```

### 1-2 Hours
```
[+] HTML tag verification complete (if using meta tag method)
[+] GSC property verified
[+] Sitemap "Submitted" status shows
```

### 1-3 Days
```
[+] First URLs appear in Coverage as "Indexed"
[+] GSC detects JSON-LD schema
[+] robots.txt validated
[+] Core Web Vitals data starts appearing
```

### 1-2 Weeks
```
[+] All 6 URLs indexed in GSC
[+] Organic impressions appear in Performance report
[+] First clicks from Google search
[+] Rankings for target keywords visible (position 20-100)
```

### 1-3 Months
```
[+] Significant organic traffic (10-100+ clicks/week)
[+] Rankings improve (position 10-30 for main keywords)
[+] Pattern trends visible in Performance data
[+] Content optimization opportunities identified
```

---

## 📲 QUICK REFERENCE URLS

| Purpose | URL |
|---------|-----|
| Google Search Console | https://search.google.com/search-console |
| Sitemap | https://sellia-brain.vercel.app/sitemap.xml |
| Robots.txt | https://sellia-brain.vercel.app/robots.txt |
| Schema Validator | https://validator.schema.org/ |
| PageSpeed Insights | https://pagespeed.web.dev/ |
| Google Business | https://www.google.com/business/ |

---

## ⚠️ COMMON MISTAKES TO AVOID

```
❌ DON'T: Submit sitemap before verifying property
   ✓ Verify first, submit second

❌ DON'T: Modify domain/redirect structure after submitting
   ✓ Keep URLs stable for 1+ months minimum

❌ DON'T: Block /robots.txt in your actual robots.txt
   ✓ Should always be crawlable

❌ DON'T: Change titles/descriptions during ranking period
   ✓ Let URLs stabilize before A/B testing

❌ DON'T: Expect results in 1 week
   ✓ Realistic timeline: 1-3 months for organic traffic
```

---

## 🎯 SUCCESS INDICATORS

### Week 1
```
✓ Property verified in GSC
✓ Sitemap submitted and showing status
✓ robots.txt test passing
✓ 0-2 URLs indexed
```

### Week 2-3
```
✓ 2-4 URLs indexed
✓ 10-50 impressions in GSC Performance
✓ 0-5 clicks from organic search
✓ Rankings appearing for long-tail keywords
```

### Week 4+
```
✓ 4-6 URLs indexed
✓ 50-200+ impressions
✓ 5-20 clicks per week
✓ Rankings improving for target keywords
✓ Traffic patterns visible in analytics
```

---

## 📞 NEED HELP?

### If Property Won't Verify
- Try different verification method
- Wait 24 hours (DNS propagation)
- Clear browser cache
- Try incognito mode
- Contact: https://support.google.com/webmasters/

### If Sitemap Shows Error
- Verify: https://sellia-brain.vercel.app/sitemap.xml returns 200
- Check: Valid XML format (paste in validator)
- Wait 5 min and resubmit
- Contact Vercel support if 404

### If URLs Not Indexing After 4 Weeks
- Use "URL Inspection" tool in GSC
- Click "Request indexing"
- Check for crawl errors in Coverage
- Verify robots.txt allows path
- Check for noindex meta tag

---

## 📝 NEXT ACTIONS (COPY TO YOUR TODO)

- [ ] Step 1: Open GSC
- [ ] Step 2: Add property (https://sellia-brain.vercel.app)
- [ ] Step 3: Verify ownership (HTML tag or DNS)
- [ ] Step 4: Submit sitemap.xml
- [ ] Step 5: Test robots.txt
- [ ] Step 6: Monitor Coverage (bookmark page)
- [ ] Step 7: Check back in 1 week
- [ ] Step 8: Monitor Performance tab for traffic

---

**Estimated Completion Time:** 15-30 minutes  
**Next Checkpoint:** 1 week (check Coverage report)  
**Created:** 2026-08-08  
**Status:** ✅ READY TO EXECUTE
