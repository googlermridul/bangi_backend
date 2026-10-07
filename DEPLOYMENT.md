# Deployment Roadmap

Frontend (Next.js static export) -> **Hostinger shared hosting**
Backend (FastAPI)                -> **Render** (free web service)
Database (PostgreSQL)            -> **Neon** (free plan)

Replace `yourdomain.com` everywhere below with your real domain.

```
Browser -> https://yourdomain.com      (Hostinger: static files)
        -> https://api.yourdomain.com  (Render: FastAPI)  -> Neon (PostgreSQL)
```

> Free-tier limits and menus change. If a screen looks different, follow the platform's current docs.

---

## Phase 0: Before you start (30 min)

- [ ] Accounts: GitHub, Neon (neon.com), Render (render.com)
- [ ] Your domain is on Hostinger and its DNS is managed by Hostinger (hPanel -> Domains -> DNS / Nameservers)
- [ ] Backend works locally (you already did this)
- [ ] **Do not launch publicly with the demo data.** It contains FAKE products and links to example.com.
      Use it for testing only; replace it with real data before real users arrive.

---

## Phase 1: Database on Neon

1. Neon dashboard -> **Create project** (any name, pick the region closest to your Render region).
2. Open **Connection details** and copy the connection string. It looks like:
   `postgresql://user:password@ep-xxxx.region.aws.neon.tech/neondb?sslmode=require`
   Keep it secret.
3. On your PC, in `backend/.env`, set:
   `DATABASE_URL=<the Neon connection string>`
4. Create the tables on Neon (from the `backend` folder):
   ```
   python -m scripts.init_db
   ```
   Expected: `Connected to database 'neondb'.` then `Created tables: ...`
5. (Testing only) load demo data: `python -m scripts.seed`
6. Run the API locally (`python -m uvicorn app.main:app --reload`) and test `/search`.
   If it works against Neon, the database part is done.

Note: Neon's free database sleeps when idle, so the first request after a quiet period is a little slower.

---

## Phase 2: Put the backend on GitHub

1. Make sure `.gitignore` exists (it is included) so `.env` and `venv` are never uploaded.
2. Create a GitHub repository (private is fine) and push the project.
   Recommended: one repo with this structure:
   ```
   repo/
     backend/    (this project's backend folder)
     frontend/   (your Next.js app)
   ```
3. Double-check on github.com that **no `.env` file** was uploaded.

---

## Phase 3: Backend on Render

1. Render dashboard -> **New +** -> **Web Service** -> connect your GitHub repo.
2. Settings:
   | Field | Value |
   |---|---|
   | Language / Runtime | Python 3 |
   | Root Directory | `backend` |
   | Build Command | `pip install -r requirements.txt` |
   | Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
   | Instance type | Free |
3. **Environment variables** (Environment tab):
   | Key | Value |
   |---|---|
   | `DATABASE_URL` | your Neon connection string |
   | `ALLOWED_ORIGINS` | `https://yourdomain.com,https://www.yourdomain.com` |
   | `DEFAULT_CURRENCY` | `BDT` |
   | `PYTHON_VERSION` | a full version like `3.12.8` (only if the build fails on the default version) |
   | `ANTHROPIC_API_KEY` | optional, only when you want the AI parser |
4. Deploy. When it finishes, open `https://<your-service>.onrender.com/docs` and test `POST /search`.
   Also try `/ping` (no database) and `/health` (checks the database).
5. Free instances sleep after ~15 minutes without traffic; the first request afterwards can take 30-60 seconds. This is normal.

---

## Phase 4: API subdomain (api.yourdomain.com)

1. Render -> your service -> **Settings -> Custom Domains -> Add** `api.yourdomain.com`.
   Render shows you the DNS record to create (usually a CNAME to `<your-service>.onrender.com`).
2. Hostinger hPanel -> **Domains -> DNS / Nameservers -> DNS records** -> add:
   - Type: `CNAME`, Name: `api`, Target: the value Render gave you
3. Back in Render click **Verify**. Wait (minutes, sometimes longer) until it shows verified and HTTPS is issued.
4. Test: `https://api.yourdomain.com/ping`

---

## Phase 5: Frontend on Hostinger

### 5a. Make the Next.js app exportable
In `frontend/next.config.js` (or `.ts` / `.mjs`) set:
```js
const nextConfig = {
  output: 'export',
  images: { unoptimized: true }, // needed if you use next/image
};
module.exports = nextConfig; // keep the file's existing export style
```
Static export means: no API routes, no server actions, no server-only features. A search page that calls
your FastAPI from the browser is fine. If `npm run build` shows an error, send it to me.

### 5b. Build with the production API URL
`NEXT_PUBLIC_API_URL` is baked into the files at build time, and **`.env.local` overrides `.env.production`**,
so set it in the terminal for the build (PowerShell):
```
cd frontend
$env:NEXT_PUBLIC_API_URL="https://api.yourdomain.com"
npm run build
```
This creates an `out` folder. Quick check: open any `.js` file inside `out/_next` and search for your API URL
(it should be `https://api...`, NOT `localhost`).

### 5c. Upload to Hostinger
1. hPanel -> **Websites -> your site -> File Manager** -> open `public_html`.
2. Delete the default placeholder files.
3. Upload the **contents** of `out` (not the folder itself). Tip: zip the contents, upload the zip, extract it.
4. In hPanel make sure **SSL** is active for the domain and "Force HTTPS" is on.
   If not, add this to `public_html/.htaccess`:
   ```
   RewriteEngine On
   RewriteCond %{HTTPS} off
   RewriteRule ^(.*)$ https://%{HTTP_HOST}/$1 [R=301,L]
   ```
5. Open `https://yourdomain.com` and run a search.

To redeploy after changes: rebuild (5b) and upload the new `out` contents again.

---

## Phase 6: Pre-launch checklist

- [ ] Search works on the live site (no CORS error in the browser console, F12)
- [ ] Buy button goes through `https://api.yourdomain.com/go/...` and lands on the seller
- [ ] Demo data removed and replaced with real products and real affiliate links
- [ ] Affiliate disclosure, Privacy, and Terms pages exist on the site
- [ ] `.env` never uploaded anywhere; API keys only in Render's Environment tab
- [ ] If you enable the AI parser: set a spending limit on your AI provider account, and add basic
      rate limiting to `/search` (anyone can call your API, and each call would cost you money)
- [ ] Analytics: check the `queries` and `clicks` tables regularly

---

## Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| Browser console: "blocked by CORS policy" | `ALLOWED_ORIGINS` on Render is missing your exact domain (with `https://`, no trailing slash, `www` and non-`www` both). Fix it and redeploy. |
| Site calls `localhost` | The build used the wrong `NEXT_PUBLIC_API_URL`. Rebuild with step 5b and re-upload. |
| "Mixed content" error | The site is https but the API URL is http. Use `https://api.yourdomain.com`. |
| First search takes ~1 minute | Render free instance was asleep. Normal on the free plan. |
| `password authentication failed` / `SSL` errors | Re-copy the full Neon string (it must include `?sslmode=require`). |
| Render build fails on a package | Add `PYTHON_VERSION` (e.g. `3.12.8`) in Render's environment variables and redeploy. |
| Custom domain stuck "pending" | The CNAME is wrong or DNS has not propagated yet; recheck the record and wait. |
| Blank page or 404 on Hostinger | You uploaded the `out` folder itself instead of its contents, or `index.html` is not directly inside `public_html`. |

## Optional: reduce the Render cold start
Some people ping the API every ~10 minutes with a free uptime monitor so it stays awake. If you do:
ping `/ping` (not `/health`), because `/health` touches the database and would keep Neon awake too,
using up its free compute hours. Check Render's current terms before relying on this.
