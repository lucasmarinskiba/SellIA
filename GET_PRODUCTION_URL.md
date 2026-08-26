# Get Production URL from Railway

## Method 1: Railway Dashboard (Easiest)

1. Go to https://railway.app/
2. Log in with your account
3. Look for project: **"impartial-hope"** or **"shimmering-light"**
   (One should contain SellIA/Sellbot)
4. Click on the project
5. Go to **Deployments** tab
6. Find the **backend** service
7. Copy the URL (should look like `https://[xyz].railway.app/`)
8. Run tests:
   ```bash
   cd "C:\Users\Usuario\Pictures\Somos paithon labs\Agente IA - Vendedor Automático"
   ./run_e2e_tests.sh https://[your-url]
   ```

## Method 2: Railway CLI (Local)

If you prefer command line:

```bash
cd "C:\Users\Usuario\Pictures\Somos paithon labs\Agente IA - Vendedor Automático"

# Login (if not already)
railway login

# Link project (choose impartial-hope or shimmering-light)
railway link impartial-hope
# or
railway link shimmering-light

# Get deployment info
railway deployment

# Get service URL
railway domain --service backend

# Or open dashboard directly
railway open
```

## What to Look For

Production URL should:
- Start with `https://`
- End with `.railway.app` (or custom domain)
- Example: `https://sellbot-prod.railway.app`
- Health check endpoint: `https://[url]/api/health`

## Test It

Once you have the URL:

```bash
# Quick health check
curl https://[your-url]/api/health

# Run full e2e suite
./run_e2e_tests.sh https://[your-url]
```

## Success Indicators

✅ `/api/health` returns 200 OK
✅ All 16 e2e tests pass
✅ Debug endpoints accessible (with tags=["debug"])

## If Issues

Check Railway logs:
```bash
railway logs --deployment [deployment-id]
```

Or email/message support at Railway if deployment is stuck.

---

**Note:** Two projects found in Railway account:
- impartial-hope
- shimmering-light

One should be the SellIA backend. Check which one has recent deployments.
