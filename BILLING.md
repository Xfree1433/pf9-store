# PF9 Store — Billing & Subscription System

## Customer Flow

1. **Browse** → Customer visits store.plainspokenfoundrynine.com
2. **Try Demo** → Auto-logged into demo account to explore the app
3. **Subscribe** → Enters name/email/company → redirected to Stripe Checkout
4. **Pay** → Completes payment on Stripe → redirected back to store with success banner
5. **Account Provisioned** → Webhook fires → account auto-created in the app + welcome email with login credentials
6. **Login** → Customer logs in with emailed credentials
7. **Manage** → "Manage Subscription" on login page opens Stripe billing portal (upgrade/cancel)

## Stripe Configuration (Test Mode)

| App | Monthly Price | Stripe Price ID |
|-----|--------------|-----------------|
| FLOWTRACK | $99/mo | price_1TBxHMFAgoUfnM8VHdeCIvUs |
| QUALIFI | $79/mo | price_1TBxHNFAgoUfnM8VMG2ryCbN |
| SHIFTLOG | $49/mo | price_1TBxHOFAgoUfnM8VfBp0iAkX |
| REPORTR | $59/mo | price_1TBxHOFAgoUfnM8VbcogJ3ha |
| INSPECTR | $49/mo | price_1TBxHPFAgoUfnM8VC7A8RARB |
| OPSIQ (Starter) | $79/mo | (create in Stripe) |
| OPSIQ (Growth) | $199/mo | (create in Stripe) |
| OPSIQ (Operations) | $399/mo | (create in Stripe) |

**Bundle Pricing:**
- Starter: From $49/mo (single app)
- Professional: $149/mo (any 3 apps)
- Enterprise: $249/mo (all 5 apps)

> 🔴 **THIS REPO IS PUBLIC — never paste an unredacted secret into it. Found 2026-08-08.**
> The test-mode webhook signing secret was committed here in full (`ecefd65`) and was being served
> at `https://store.plainspokenfoundrynine.com/BILLING.md` (HTTP 200, verified). It has been redacted
> below, but **redaction does not undo the exposure**: the repo is public and the value remains in
> git history, which cannot be assumed private. **The test webhook secret must be rotated in the
> Stripe dashboard** — see the rotation note under "Webhooks" below.
>
> Rule going forward: this file records *which* variables exist and where they live, **never their
> values**. Real values belong only in the server-side `.env` (mode 600), which `pf9-deploy`
> deliberately does not ship.

**Stripe Keys (values redacted — read them from the server `.env`, never from this file):**
- Publishable: `pk_test_…` (in store frontend — publishable keys are safe to expose by design)
- Secret: `sk_test_…` (server `.env` only)
- Webhook Secret: `whsec_…` (server `.env` only) — **🔴 the previously committed test value is
  compromised and pending rotation**
- Webhook Endpoint ID: `we_1TBwHSFAgoUfnM8Vn63MjcJh` (an identifier, not a credential — safe)

**Test Card:** `4242 4242 4242 4242` / any future expiry / any CVC

## Architecture

```
Store Frontend (store.plainspokenfoundrynine.com)
    │
    │  POST /store-api/create-checkout-session
    ▼
Flask store_api.py (app.plainspokenfoundrynine.com)
    │
    │  stripe.checkout.Session.create() → redirect to Stripe
    ▼
Stripe Checkout (customer pays)
    │
    │  POST /store-api/stripe-webhook (checkout.session.completed)
    ▼
Flask store_api.py
    │  1. Save subscription to SQLite
    │  2. Generate temp password
    │  3. POST to app's /api/auth/register endpoint
    │  4. Send welcome email with credentials
    ▼
App account provisioned → customer logs in
```

## API Endpoints

### POST /store-api/create-checkout-session
Creates a Stripe Checkout session for subscription.

**Request:**
```json
{"product": "FLOWTRACK", "email": "user@company.com", "name": "John", "company": "Acme"}
```

**Response:**
```json
{"url": "https://checkout.stripe.com/c/pay/cs_test_..."}
```

### POST /store-api/stripe-webhook
Handles Stripe webhook events. Registered for:
- `checkout.session.completed` → provisions account + sends welcome email
- `customer.subscription.deleted` → marks subscription as cancelled
- `customer.subscription.updated` → future use

### POST /store-api/create-portal-session
Opens Stripe billing portal for subscription management.

**Request:**
```json
{"email": "user@company.com"}
```

**Response:**
```json
{"url": "https://billing.stripe.com/..."}
```

### POST /store-api/demo-request
Original demo request form handler (saves lead + sends notification email).

### GET /store-api/health
Returns `{"status": "ok", "service": "store-api"}`

## Account Provisioning

Each app's `/api/auth/register` endpoint is called after payment:

| App | Endpoint | Payload Fields |
|-----|----------|---------------|
| Flowtrack | /api/auth/register | email, name, password, organizationName |
| Reportr | /api/auth/register | email, name, password, organizationName |
| ShiftLog | /api/auth/register | email, name, password, organizationName |
| Inspectr | /api/auth/register | email, name, password, companyName |
| Qualifi | (none — client-side only, no backend) | — |
| OPSIQ | /api/auth/register | email, name, password, organizationName |

## Server Deployment

**Location:** 139.94.250.128 (store server)
- API code: `/opt/bridgr/src/store/routes.py`
- Database: `/opt/bridgr/store_leads.db` (demo_requests + subscriptions tables)
- Env vars: `/opt/bridgr/.env`
- Service: `bridgr.service` (gunicorn)
- Restart: `sudo systemctl restart bridgr`

**Required env vars:**
```
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_FLOWTRACK_PRICE_ID=price_...
STRIPE_QUALIFI_PRICE_ID=price_...
STRIPE_SHIFTLOG_PRICE_ID=price_...
STRIPE_REPORTR_PRICE_ID=price_...
STRIPE_INSPECTR_PRICE_ID=price_...
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=...
SMTP_PASSWORD=...
NOTIFY_EMAIL=...
```

## Going Live

To switch from test to production Stripe:
1. Activate your Stripe account (complete identity verification)
2. Create live products/prices in Stripe Dashboard
3. Update `.env` with live `sk_live_` key and new price IDs
4. Create a new webhook endpoint with the live URL
5. Update `STRIPE_WEBHOOK_SECRET` with the new signing secret
6. Update the publishable key in the store frontend if used
