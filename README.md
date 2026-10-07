# Micro Might

Micro Might is a Bengaluru farm-fresh microgreens storefront. The customer site
supports product browsing, cart and guest checkout, optional customer accounts,
saved delivery details, order tracking, and an admin workspace for order,
inventory, payment, and admin-user management.

The application uses **FastAPI + MongoDB** behind a **Vite + React 19 +
TypeScript** frontend. Frontend requests use a typed fetch layer over `/api`.

## Layout

```
  /app/
  backend/   FastAPI + motor (async MongoDB) + Pydantic v2 — /root/.venv/bin/python
  frontend/  Vite + React 19 + Tailwind v4 + shadcn/ui (TypeScript strict)
  tests/     Playwright e2e workspace (pre-scaffolded)
```

## Running

Two separate processes, managed by supervisor in the pod (see "Pod conventions"
below); to run them by hand from two terminals instead:

```bash
cd backend && /root/.venv/bin/python -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload   # http://localhost:8001
cd frontend && yarn dev                                                # http://localhost:3000
```

## The `/api` proxy convention

Every backend route lives under `/api` (the backend mounts one
`APIRouter(prefix="/api")`), and the frontend dev server
(`frontend/vite.config.ts`) proxies `/api/*` to `http://localhost:8001`. So
frontend code always calls a **relative** path — `apiGet("/auth/session")` →
`/api/auth/session` — and never an absolute backend URL. The same code works in dev
(via the Vite proxy) and in production (once both are served behind a single
origin).

The live API root is `/api/`. Customer endpoints are under `/api/auth`, orders
under `/api/orders`, and administration under `/api/admin`. There is no
`/api/status` endpoint in this storefront.

## Store rules

- Customer accounts are optional. Signup and login create an httpOnly session
  cookie; customer profiles and saved addresses are stored in MongoDB. Guest
  checkout also stores contact and delivery information with the order.
- Checkout pricing is calculated by the backend from its product catalog.
  Delivery is free for the first 5 km and estimated at ₹9 per additional km;
  COD adds ₹30.
- COD is restricted server-side to Bengaluru postal codes beginning with
  `560`, so bypassing the frontend cannot select COD for an out-of-area order.
- Online card/UPI payment uses Razorpay Checkout. The backend creates orders
  from catalog-priced items, stores short-lived payment intents, and accepts an
  order only after signature and captured-payment verification. Configure
  `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET` in `backend/.env`; never expose the
  secret to the frontend. The public `/api/payments/razorpay/config` endpoint
  reports whether both keys are present. Without keys, Razorpay stays unavailable.
- Checkout opens Razorpay only when both backend keys are configured. If the
  payment script fails, the payment is dismissed, or verification fails, no
  order is shown as complete. COD is selectable only after a `560` Bengaluru
  pincode is entered; the API enforces the same rule.
- Customer payment instructions live at `/payment`; checkout uses the gateway
  readiness endpoint to keep unavailable Razorpay options disabled.
- Admin order history and filters distinguish Razorpay, COD, and historic
  PhonePe QR orders. New checkout API requests accept only verified Razorpay
  payments or COD; QR cannot create a new order, even by bypassing the frontend.
- For an internet deployment, serve the frontend and `/api` on the same HTTPS
  origin, set production MongoDB and admin credentials, configure Razorpay's
  live keys in its dashboard, and point the chosen `.co` domain's
  DNS at the hosting provider. Domain registration, hosting, and live gateway
  activation require accounts and credentials not stored in this repository.

## Backend

FastAPI, async throughout. Use the app venv interpreter at
`/root/.venv/bin/python`; the shell's bare `python` may not resolve to that
environment. Backend deps are installed from
`backend/requirements.txt`.

- **Entry point**: `backend/server.py` — creates `app = FastAPI()`, creates
  `api_router = APIRouter(prefix="/api")`, registers routes **on the router**,
  and calls `app.include_router(api_router)` at the bottom. CORS middleware is
  added from `CORS_ORIGINS`. Never hang a route directly off `app` — it would
  land outside `/api` and the Vite proxy would not reach it.
- **Route organization**: `backend/server.py` mounts routers from
  `backend/routers/`; Pydantic request/response models live in
  `backend/models/`. Customer auth, orders, inventory, payments, and admin
  routes are mounted beneath `/api`. Invalid request bodies receive FastAPI's
  `422` response with a `{"detail": [...]}` body.
- **MongoDB**: import the shared handle — `from lib.db import client, db`
  (`backend/lib/db.py` self-loads `.env` before reading env). Use it from
  `server.py`, every router, and standalone scripts like `seed.py`; never
  construct another `AsyncIOMotorClient`. Collections are attributes:
  `await db.users.insert_one(...)`, `await db.orders.find().to_list(1000)`.
  Motor connects lazily, so importing `server` never blocks on Mongo. `pymongo`
  is installed too if you need a sync client in a script.
- **Ids**: documents use a string `id` (`uuid4`) field, not Mongo's `ObjectId`
  — `ObjectId` is not JSON-serializable and leaks into response bodies.
- **Config**: `backend/.env` — `MONGO_URL` (connection string), `DB_NAME`
  (database name), `CORS_ORIGINS`. `server.py` loads it with `python-dotenv`
  above its local imports, and `lib/db.py` self-loads it so standalone scripts
  inherit it too. The pod runs `mongod` locally, so `MONGO_URL` points at
  `localhost`. Add new secrets/config here; read them with `os.environ`.
- **Dates**: `backend/lib/dates.py` — `today_iso(tz=None)`. The pod clock is
  UTC; anchor "today" server-side with this, never with client-side date math.
- **Interactive check**: `cd /app/backend && /root/.venv/bin/python -c 'import server'` catches
  syntax/import errors without waiting for the supervisor log.

## Frontend

- Vite + React 19 + TypeScript strict, dev server on port `3000`.
- Tailwind CSS v4 (via the `@tailwindcss/vite` plugin — no separate
  `tailwind.config.js` needed) + shadcn/ui, initialized with the `base-nova`
  style and `neutral` base color, `@` path alias (`@/*` → `src/*`) wired in both
  `tsconfig.app.json`/`tsconfig.json` and `vite.config.ts`.
- `react-router-dom` and `motion` are preinstalled — don't re-add them. `src/App.tsx`
  is the `<Routes>` table and nothing else; screens live in `src/pages/*.tsx` and are
  imported as `@/pages/<Name>`. Current routes include product browsing, cart,
  checkout, login/signup, customer account, payment information, and admin tools. Add
  a `<Route>` for every page you write, in the same edit that creates the page — a
  page with no route is unreachable, and any URL without a matching `<Route>` renders a
  **blank page** — `<Routes>` matches nothing and mounts nothing.
- Components installed under `src/components/ui/`: button, card, input, label,
  select, dialog, sheet, tabs, badge, calendar, sonner, textarea, table, popover,
  dropdown-menu, checkbox. Add more with `npx shadcn@latest add <component>`.
- `src/lib/api.ts` — the typed fetch layer: `apiGet<T>`, `apiPost<T>`,
  `apiPut<T>`, `apiPatch<T>`, `apiDelete<T>`, all relative to base `/api`,
  throwing `ApiError` (with `status` and the parsed body) on any non-2xx.
  **Nothing infers across the Python boundary** — you declare the response type
  yourself as a TS interface mirroring the endpoint's Pydantic model, and keeping
  the two in sync is a manual discipline. When you change a Pydantic model,
  change its TS interface in the same edit.
- Customer/account, inventory, orders, and payment readiness use TanStack Query.
  Keep the main page shell available when optional API data is unavailable; do not
  represent unavailable Razorpay configuration as an active payment option.

## TypeScript

`frontend/tsconfig.app.json` / `tsconfig.node.json` have `strict: true`. In the
pod:

```bash
cd frontend && yarn typecheck
```

— plain `tsc --noEmit` run from `frontend/` checks ZERO files (root tsconfig uses
project references with `"files": []`) and exits 0 even with type errors. Always
use `-b` for the frontend. Lint with `cd frontend && yarn lint` (oxlint).

## Testing

Two lanes.

**Backend (pytest)** — specs in `backend/tests/` as `test_*.py`, run with:

```bash
cd /app/backend && /root/.venv/bin/python -m pytest
```

`backend/pytest.ini` is canonical: `addopts = -n 2 --dist loadscope` (pytest-xdist,
already parallel — do not pass your own `-n`) and `asyncio_mode = auto` (so
`async def test_...` needs no marker). Serial is `-n 0`, **never**
`-p no:xdist` (that errors, because `addopts` still passes `-n`/`--dist`).
`backend/tests/conftest.py` is pre-scaffolded — a sync `client` fixture
(`httpx.Client` rooted at `/api`), an async `aclient`, and an `api_url()` helper,
all pointed at `BACKEND_URL` (default `http://localhost:8001`). Tests hit the
live uvicorn process, so the app under test is the one the browser sees. Add
app-specific fixtures below the marker; do not re-create the file.

**Frontend (Playwright)** — `/app/tests/` is pre-scaffolded:
`playwright.config.ts` (canonical — edit the marked lines only),
`fixtures/helpers.ts`, and a `package.json` that resolves
`@playwright/test@1.62.0` (node_modules baked into the image). Write specs into
`tests/e2e/`. Do NOT re-create the config/helpers or install/upgrade playwright —
matching Chromium browsers live at `/pw-browsers`.

Backend specs use pytest; browser journey coverage uses Playwright.

Run the browser suite from the pre-scaffolded Playwright workspace:

```bash
cd /app/tests && PLAYWRIGHT_BROWSERS_PATH=/pw-browsers yarn playwright test
```

The customer journey runs at desktop and mobile viewports and covers signup,
saved-address persistence, Bengaluru-only COD eligibility, and order placement.

## Pod conventions

This template runs under supervisord in the Emergent agent pod — supersedes any
local-run instructions above.

- Backend, frontend, and `mongod` are supervisor programs. Source changes
  hot-reload; restart after environment, dependency, or Vite configuration changes:

  ```bash
  sudo supervisorctl restart frontend backend
  until curl -sf -o /dev/null http://localhost:3000; do sleep 2; done
  ```

- Status, only after a restart you triggered:
  `sudo supervisorctl status frontend backend`. Logs:
  `/var/log/supervisor/backend.err.log`, `backend.out.log`,
  `frontend.err.log`.
- App in a browser: the pod's preview URL (frontend, port `3000`). Backend API
  directly at port `8001`.
- `mongod` runs locally in the pod (`--bind_ip_all`); `MONGO_URL` in
  `backend/.env` points at `localhost`, no separate Mongo container.
- Both dev servers hot-reload on file edits (uvicorn `--reload` for the backend,
  Vite HMR for the frontend); no rebuild step needed for normal iteration. A
  restart is still needed after changing `.env`, `requirements.txt`, or
  `vite.config.ts`.
