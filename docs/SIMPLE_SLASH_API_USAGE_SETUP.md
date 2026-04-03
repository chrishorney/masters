# Slash API usage counter — simple setup

**Good news:** The app code is already built (admin banner, counting, API). Nothing else needs to be “programmed.”

**What still needs a human:** Your **database** must get one new table, and your **hosting** must run the **new** backend + frontend. I (or any AI) **cannot** log into your Supabase, Render, Railway, etc. — only you can, with your password.

---

## Option A — Easiest if you use **Supabase** (no terminal)

1. Open **Supabase** → your project → **SQL Editor**.
2. Open the file in this repo: **`docs/sql/apply_slash_api_usage_monthly.sql`**
3. Copy **all** of it, paste into SQL Editor, click **Run**.

That creates the table. It also updates Alembic’s version row **only if** your DB was already at the previous revision (`f1a2b3c4d5e6`). If you’re not sure, run the first block (CREATE TABLE) only; if it says the table already exists, you’re done.

4. In Supabase (or wherever you set API env vars), optionally add:  
   `SLASH_API_MONTHLY_LIMIT=70000`  
   so the admin page shows a progress bar vs your RapidAPI cap.

5. **Deploy** your site the same way you usually do (push to GitHub, or your host’s “Deploy” button). The new code has to go live **after** the table exists (or at the same time).

---

## Option B — Someone runs **one** command for you

If a friend or IT person has your project on their machine with `backend/.env` pointing at your real database:

```bash
cd backend
source venv/bin/activate   # if they use a venv
alembic upgrade head
```

That’s the whole migration.

---

## How you’ll know it worked

- Log into **Admin** in your app.
- You should see **“Slash Golf API usage”** with numbers (may be `0` until the next sync/API call).

---

## If you get stuck

Send whoever helps you this file and say: *“We need this migration applied to prod and the latest code deployed.”* They’ll know what that means.
