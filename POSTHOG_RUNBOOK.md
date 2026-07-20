# PostHog Go-Live Runbook

Run everything from the repo root unless noted:
```bash
cd /Users/markpierce/Documents/PlainSpokenFoundryNine
```

---

## 1. Confirm the PostHog region (do this first — blocking)

Log into PostHog. Look at the URL after you're in:
- `us.posthog.com` / `app.posthog.com` → **US** (no change needed; everything already points here).
- `eu.posthog.com` → **EU** → run the search-replace below.

**Only if EU**, rewrite the host everywhere (macOS `sed`, skips node_modules/venv):
```bash
grep -rl --exclude-dir=node_modules --exclude-dir=venv --exclude-dir=.git \
  'us.i.posthog.com' . \
| xargs sed -i '' 's#us\.i\.posthog\.com#eu.i.posthog.com#g'
```
Verify: `grep -rl 'eu.i.posthog.com' --include='*.env' .` should list the apps.

---

## 2. Install deps + build (per app)

### Node / TypeScript apps
```bash
for app in FLOWTRACK SHIFTLOG MAINTAINR REPORTR INSPECTR QUALIFI; do
  echo "=== $app ==="
  ( cd "$app" && npm install && npm run build ) || echo "!! $app failed — check output"
done
```
(INSPECTR and QUALIFI are Vite + a backend; the line above builds the frontend. QUALIFI's Python backend is handled in the next block.)

### Python / Flask apps (use python3.12 per CLAUDE.md)
These got server-side `posthog` added to requirements:
```bash
for app in LANDLORDR PERMITR EXTRACTR SUPPORTR TASKFLOW TENANTLINKR COMPLI; do
  echo "=== $app ==="
  ( cd "$app" && python3.12 -m venv venv && source venv/bin/activate \
    && pip install -r requirements.txt && deactivate ) || echo "!! $app failed"
done

# QUALIFI's Flask backend
( cd QUALIFI/backend && python3.12 -m venv venv && source venv/bin/activate \
  && pip install -r requirements.txt && deactivate )
```

**No install needed** for BRIDGR, PAPERCLIPR, WEALTHWATCH, BABYSTOCK — they got the client snippet only (pure template change). Just redeploy them.

---

## 3. Storefront conversion event (one edit in your billing code)

`subscription_started` fires when Stripe returns to the success page with the right query params. Find where you create the Checkout Session (the handler behind `POST /create-checkout-session`) and set:
```python
success_url = (
    "https://store.plainspokenfoundrynine.com/"
    "?checkout=success&product=" + product +
    "&email=" + email +
    "&session_id={CHECKOUT_SESSION_ID}"
)
```
(Stripe substitutes `{CHECKOUT_SESSION_ID}` itself.) Everything else on the storefront already works with no edit.

---

## 4. Deploy

- **Storefront**: static HTML — deploy `pf9-store` the way you normally do (no rebuild).
- **Apps**: deploy each rebuilt app via your usual path (the `deploy-*.sh` scripts / `pf9-infra` compose).
- Tahoe Gatekeeper note from CLAUDE.md: run shell scripts as `bash deploy-foo.sh`, not `./deploy-foo.sh`.
- `.env` files are gitignored and pre-filled — don't commit them, don't push.

Smoke test per app after deploy: load it, then watch **PostHog → Activity**. You should see `$pageview` immediately, and `app_login` / `core_action_performed` as you click through.

---

## 5. Build the funnel in PostHog

Once events are arriving:
1. PostHog → **Funnels** → New.
2. Steps, in order: `$pageview` → `checkout_started` → `subscription_started` → `app_signup` → `core_action_performed`.
3. **Breakdown by** event property `app` — this splits all 15 products onto one chart so you can compare conversion.
4. Save it to a dashboard. Add a **Retention** insight (returning `core_action_performed`) next to it for activation→retention.

Activation per app is the *first* `core_action_performed` — defined in `POSTHOG_TRACKING_PLAN.md` §5. Glance at that list before you trust the numbers.
