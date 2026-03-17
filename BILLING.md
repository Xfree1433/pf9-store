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
| FLOWTRACK | $299/mo | price_1TBvd2FAgoUfnM8VCpCOar6a |
| QUALIFI | $199/mo | price_1TBvd3FAgoUfnM8VN72kmCLN |
| SHIFTLOG | $99/mo | price_1TBvd3FAgoUfnM8VF49rWAgh |
| REPORTR | $149/mo | price_1TBvd4FAgoUfnM8VJ8S2w6KA |
| INSPECTR | $149/mo | price_1TBvd4FAgoUfnM8Ve7yTxqNU |

**Stripe Keys:**
- Publishable: `pk_test_51TBvRfFAgoUfnM8VLxN2Fyz...` (in store frontend)
- Secret: `sk_test_51TBvRf...` (in server .env)
- Webhook Secret: `whsec_JmvHZE6lLaPmfiswnwOsNFsaRCjKqw8e`
- Webhook Endpoint ID: `we_1TBwHSFAgoUfnM8Vn63MjcJh`

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
