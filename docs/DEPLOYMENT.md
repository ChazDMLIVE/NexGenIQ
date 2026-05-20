# Deploying NexGenIQ

This guide walks you through putting NexGenIQ online as a live website.

NexGenIQ has three parts that get deployed:

1. **Backend** — the FastAPI service (the two engines run inside it).
2. **Database** — a managed PostgreSQL database.
3. **Frontend** — the React web application (a set of static files).

The recommended host is **Railway**, because it runs all three together
with minimal configuration and, unlike a serverless platform, supports the
long-running herd simulation without timeouts.

Everything below assumes the project is already on GitHub (it is) — Railway
deploys straight from the repository.

---

## Before you start

You need:

- The NexGenIQ GitHub repository (done).
- A **Railway** account — sign up free at railway.app, using "Login with
  GitHub" so Railway can see your repository.

---

## Step 1 — Create the Railway project and database

1. In Railway, click **New Project**.
2. Choose **Deploy from GitHub repo**, and pick the **NexGenIQ**
   repository. Railway may ask permission to access it — allow it.
3. Railway will start trying to build something. That's fine — you will
   point it at the backend in Step 2.
4. In the project, click **New** → **Database** → **Add PostgreSQL**.
   Railway provisions a Postgres database and, importantly, exposes its
   connection string as a variable called `DATABASE_URL` within the
   project.

---

## Step 2 — Configure the backend service

The backend lives in the `backend/` subdirectory of the repo, so Railway
must be told to build from there.

1. Click the service Railway created from your repo (the one that is *not*
   the database). Open its **Settings**.
2. Under **Source** / **Root Directory**, set the root directory to
   `backend`.
3. Railway auto-detects Python and uses the `backend/railway.json` and
   `backend/requirements.txt` already in the repo — these install the web
   stack and both NexGenIQ engines, and start the API with uvicorn. No
   build or start command needs to be typed by hand.

### Backend environment variables

Open the backend service's **Variables** tab and add these:

| Variable | Value |
|----------|-------|
| `NEXGENIQ_DATABASE_URL` | `${{Postgres.DATABASE_URL}}` — this references the Postgres service Railway created. (Type it exactly, including the `${{ }}`.) |
| `NEXGENIQ_JWT_SECRET` | A long random string. Generate one by running `python -c "import secrets; print(secrets.token_hex(32))"` and paste the result. **Do not skip this** — a known secret lets anyone forge logins. |
| `NEXGENIQ_DEBUG` | `false` |
| `NEXGENIQ_CORS_ORIGINS` | Leave blank for now — you will set it in Step 4 once the frontend has a URL. |

Railway will redeploy the backend. When it finishes, the service has a
public URL like `https://nexgeniq-backend-production.up.railway.app`.
**Copy that URL** — you need it for the frontend. Confirm it works by
visiting `<that-url>/health` in a browser; you should see a small JSON
response with `"status": "ok"`.

---

## Step 3 — Deploy the frontend

The frontend is a separate service in the same Railway project.

1. In the project, click **New** → **GitHub Repo**, and pick the
   **NexGenIQ** repository again.
2. Open the new service's **Settings**, set the **Root Directory** to
   `frontend`.
3. Railway auto-detects Node and uses the `frontend/railway.json` already
   in the repo — it runs `npm run build` and serves the built site with
   `npm run start`. No commands need to be typed by hand.
4. In the frontend service's **Variables**, add:

   | Variable | Value |
   |----------|-------|
   | `VITE_API_BASE_URL` | The backend URL you copied in Step 2 (e.g. `https://nexgeniq-backend-production.up.railway.app`). |

   This variable is read **at build time**, so the frontend must be
   rebuilt after setting it — Railway does this automatically.

When the frontend finishes deploying it gets its own public URL — that is
the address people visit to use NexGenIQ.

### Frontend as a static site (alternative, often simpler)

The frontend is purely static files after `npm run build`. If you prefer,
host it on **Vercel** instead — Vercel is excellent at static sites:

1. On Vercel, **Add New Project** → import the NexGenIQ repo.
2. Set the **Root Directory** to `frontend`.
3. Vercel auto-detects Vite. Set the **Build Command** to
   `npm run build` and the **Output Directory** to `dist`.
4. Under **Environment Variables**, add `VITE_API_BASE_URL` = the backend
   URL.
5. Deploy. Vercel gives you the public frontend URL.

The backend and database still live on Railway; only the static frontend
moves to Vercel. Both arrangements work.

---

## Step 4 — Connect frontend and backend

The backend must allow the frontend's browser origin to call it.

1. Copy the frontend's public URL (from Step 3).
2. Go back to the **backend** service's **Variables** on Railway.
3. Set `NEXGENIQ_CORS_ORIGINS` to that frontend URL, e.g.
   `https://nexgeniq.vercel.app` (no trailing slash; comma-separate if
   there is more than one).
4. The backend redeploys. The two halves are now connected.

---

## Step 5 — Verify

Open the frontend URL in a browser and check the full path works:

1. Create an account and sign in.
2. Build an index — define a goal, add a couple of animals, see them ranked.
3. Run a herd simulation — describe a herd, derive economic values.
4. Carry the derived values into the Index Builder.

If every step works, NexGenIQ is live.

---

## A note on the database

On its first start the backend creates its database tables automatically.
For a production system that will evolve over time, the proper next step
is to adopt a migration tool (Alembic) so schema changes are versioned —
this is noted in the Phase 3 specification as a post-MVP hardening item.
For an initial deployment, the automatic table creation is sufficient.

## A note on cost

Railway and Vercel both have free tiers adequate for a research preview or
a small user base. A herd simulation is CPU-intensive for ~15 seconds; if
usage grows, the backend service is the part to scale up first.

## Troubleshooting

- **Backend build fails on the engines** — confirm the backend Root
  Directory is `backend`; the `requirements.txt` installs the engines via
  the relative paths `../engine` and `../sim`, which only resolve when the
  whole repo is present (Railway clones the whole repo, so this works).
- **Frontend loads but every action fails** — almost always CORS or the
  API URL. Check `VITE_API_BASE_URL` is the exact backend URL and
  `NEXGENIQ_CORS_ORIGINS` is the exact frontend URL, neither with a
  trailing slash.
- **"Could not validate credentials" right after deploy** — if you
  changed `NEXGENIQ_JWT_SECRET` after creating accounts, existing tokens
  are invalidated; just sign in again.
