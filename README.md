# What Can I Cook

Photo of your fridge/pantry -> recipe suggestions. Accounts, saved recipes,
voice-guided cooking, AI swaps, nutrition estimates and a photo-rich home page.
Everything runs on free tiers.

## Project layout

```
what-can-i-cook/
├── public/            Frontend (plain HTML/CSS/JS) - served by Vercel's CDN
├── api/index.py       Vercel entry point (exposes the FastAPI app)
├── backend/           FastAPI app: main.py, auth.py, database.py, gemini.py, ...
├── vercel.json        Routes /api/* to the function
└── requirements.txt
```

## Run locally (no database setup needed)

```bash
python -m venv venv && source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp backend/.env.example backend/.env                  # then paste your GEMINI_API_KEY
cd backend && uvicorn main:app --reload
```

Open http://localhost:8000. With `DATABASE_URL` empty it stores data in
`backend/app.db` (SQLite). API docs: http://localhost:8000/api/docs

## Deploy free on Vercel (+ Neon Postgres)

Vercel functions have no persistent disk, so accounts/pantry/favorites live in a
free Postgres database (Neon).

**1. Database (Neon)**
1. Create a free project at https://neon.com.
2. Copy the **pooled** connection string (host contains `-pooler`).
   It looks like `postgresql://user:pass@ep-xxx-pooler.region.aws.neon.tech/neondb?sslmode=require`.
   Tables are created automatically on first use.

**2. Code on GitHub**
Push this folder to a GitHub repo. `.gitignore` already keeps `.env` and `app.db` out.

**3. Vercel**
1. https://vercel.com -> **Add New -> Project** -> import the repo.
2. Framework Preset: **Other**. Leave build/output settings empty.
3. **Environment Variables**:
   - `DATABASE_URL` = the Neon string
   - `GEMINI_API_KEY` = your Gemini key
4. **Deploy**.

**4. Check it**
Open `https://<your-app>.vercel.app/api/health`. You should see
`"database": "postgres"` and `"database_status": "ok"`.
If `database_status` shows an error, the `DATABASE_URL` is wrong or missing.
After changing environment variables, redeploy.

### Free-tier things to know
- **Neon** sleeps after ~5 min idle; the first request afterwards takes about a second longer.
- **Request size:** Vercel rejects bodies over ~4.5 MB, so the app shrinks photos in the browser before upload.
- **Function time:** AI calls stop retrying after ~40 s (`GEMINI_TIME_BUDGET`), inside the 60 s `maxDuration` set in `vercel.json`.
- **Gemini free key** has daily limits shared by everyone using your site.
- **Vercel Hobby** is meant for personal, non-commercial projects.
- Camera and voice need HTTPS, which Vercel provides.

## API overview

| Method | Path | What it does |
|---|---|---|
| POST | `/api/auth/register`, `/login`, `/logout` | Accounts (cookie session) |
| GET | `/api/health` | Status, AI + database check |
| GET/POST/PATCH/DELETE | `/api/pantry` | Per-user pantry |
| POST | `/api/detect-ingredients` | Photo -> ingredients (Gemini vision) |
| POST | `/api/recipes/match` | Match pantry to recipes |
| GET | `/api/recipes/{id}`, `/pdf`, `/nutrition`, `/image` | Recipe detail, PDF, AI nutrition, photo |
| GET | `/api/home/featured` | Hero + photo meals (TheMealDB) |
| GET | `/api/explore/categories`, `/by-category/{name}` | Browse TheMealDB |
| GET/POST/DELETE | `/api/favorites` | Saved recipes |
| POST | `/api/how-to-cook/ai`, `/api/ai/substitute`, `/api/ai/freestyle-recipe` | AI helpers |
