"""
Plainspoken Foundry Nine - Store API
Handles:
- Demo request form submissions (saves to DB + sends email)
- Stripe subscription checkout + webhooks + account provisioning
- CORS enabled for store.plainspokenfoundrynine.com
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import sqlite3
import os
import string
import secrets
import html
import requests as http_requests

try:
    import stripe
    stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', '')
except ImportError:
    stripe = None
    print('[Store API] WARNING: stripe package not installed')

try:
    import resend
    resend.api_key = os.environ.get('RESEND_API_KEY', '')
except ImportError:
    resend = None
    print('[Store API] WARNING: resend package not installed')

store_bp = Blueprint('store', __name__, url_prefix='/store-api')

DB_PATH = os.environ.get('STORE_DB_PATH', '/opt/pf9-store/store_leads.db')
STORE_URL = 'https://store.plainspokenfoundrynine.com'

# ── Email config (Resend) ──
EMAIL_FROM_CUSTOMER = os.environ.get('EMAIL_FROM_CUSTOMER', 'PF9 <welcome@plainspokenfoundrynine.com>')
EMAIL_FROM_INTERNAL = os.environ.get('EMAIL_FROM_INTERNAL', 'PF9 Alerts <alerts@plainspokenfoundrynine.com>')
NOTIFY_EMAIL        = os.environ.get('NOTIFY_EMAIL', '')


# ── HubSpot CRM config ──
HUBSPOT_TOKEN              = os.environ.get('HUBSPOT_TOKEN', '')
HUBSPOT_API_BASE           = 'https://api.hubapi.com'
HUBSPOT_LIST_MANUFACTURING = int(os.environ.get('HUBSPOT_LIST_MANUFACTURING', '12'))
HUBSPOT_LIST_PROPERTY      = int(os.environ.get('HUBSPOT_LIST_PROPERTY', '13'))
HUBSPOT_LIST_SUBSCRIBERS   = int(os.environ.get('HUBSPOT_LIST_SUBSCRIBERS', '14'))

_MANUFACTURING_APPS = {'FLOWTRACK', 'QUALIFI', 'SHIFTLOG', 'REPORTR', 'INSPECTR', 'MAINTAINR'}
_PROPERTY_APPS      = {'LANDLORDR', 'TENANTLINK', 'TENANTLINKR', 'PROPERTY_BUNDLE', 'PERMITR', 'TASKFLOW'}


# ── Klaviyo lifecycle-email config ──
# Drives the trial/paid onboarding flows. Klaviyo owns the day-27 pre-charge
# notice, which is why _handle_trial_will_end no longer emails directly.
KLAVIYO_API_KEY    = os.environ.get('KLAVIYO_API_KEY', '')
KLAVIYO_API_BASE   = 'https://a.klaviyo.com/api'
KLAVIYO_REVISION   = os.environ.get('KLAVIYO_REVISION', '2024-10-15')
KLAVIYO_LIST_TRIAL = os.environ.get('KLAVIYO_LIST_TRIAL', 'RKeAnZ')
KLAVIYO_LIST_PAID  = os.environ.get('KLAVIYO_LIST_PAID', 'SfBnvH')


def _hubspot_list_for_product(product):
    """Map a product key (or calculator-lead tag) to a HubSpot list ID. None if ambiguous."""
    p = (product or '').upper()
    if 'MANUFACTURING' in p or any(app in p for app in _MANUFACTURING_APPS):
        return HUBSPOT_LIST_MANUFACTURING
    if 'PROPERTY' in p or any(app in p for app in _PROPERTY_APPS):
        return HUBSPOT_LIST_PROPERTY
    return None


def _hubspot_push_contact(email, name='', company='', list_id=None):
    """
    Upsert a contact in HubSpot and optionally add to a static list.
    Fail-soft: never raises. Logs errors and returns. Callers must
    not block on this — CRM availability is not a precondition for
    serving the request.
    """
    if not HUBSPOT_TOKEN or not email:
        return

    email_norm = email.lower().strip()
    headers = {
        'Authorization': f'Bearer {HUBSPOT_TOKEN}',
        'Content-Type': 'application/json',
    }

    parts = (name or '').strip().split(None, 1)
    properties = {'email': email_norm}
    if parts:
        properties['firstname'] = parts[0]
    if len(parts) > 1:
        properties['lastname'] = parts[1]
    if company:
        properties['company'] = company

    contact_id = None
    try:
        r = http_requests.post(
            f'{HUBSPOT_API_BASE}/crm/v3/objects/contacts',
            json={'properties': properties},
            headers=headers,
            timeout=10,
        )
        if r.status_code == 201:
            contact_id = r.json().get('id')
        elif r.status_code == 409:
            r2 = http_requests.patch(
                f'{HUBSPOT_API_BASE}/crm/v3/objects/contacts/{email_norm}?idProperty=email',
                json={'properties': properties},
                headers=headers,
                timeout=10,
            )
            if r2.status_code == 200:
                contact_id = r2.json().get('id')
            else:
                print(f'[Store API] HubSpot patch failed for {email_norm}: {r2.status_code} {r2.text[:200]}')
        else:
            print(f'[Store API] HubSpot create failed for {email_norm}: {r.status_code} {r.text[:200]}')
    except Exception as e:
        print(f'[Store API] HubSpot upsert error for {email_norm}: {e}')
        return

    if contact_id and list_id:
        try:
            r = http_requests.put(
                f'{HUBSPOT_API_BASE}/crm/v3/lists/{list_id}/memberships/add',
                json=[contact_id],
                headers=headers,
                timeout=10,
            )
            if r.status_code not in (200, 201, 204):
                print(f'[Store API] HubSpot list add failed for {email_norm} (list {list_id}): {r.status_code} {r.text[:200]}')
        except Exception as e:
            print(f'[Store API] HubSpot list add error for {email_norm}: {e}')


def _klaviyo_headers():
    return {
        'Authorization': f'Klaviyo-API-Key {KLAVIYO_API_KEY}',
        'revision': KLAVIYO_REVISION,
        'Content-Type': 'application/json',
        'accept': 'application/json',
    }


def _klaviyo_format_trial_end(trial_end_iso):
    """Render the billing date the way the day-27 email reads it: 'August 30, 2026'."""
    if not trial_end_iso:
        return None
    try:
        return datetime.fromisoformat(trial_end_iso).strftime('%B %-d, %Y')
    except Exception:
        return None


def _klaviyo_sync(email, name='', properties=None, add_list=None, remove_list=None):
    """
    Upsert a Klaviyo profile and move it between lifecycle lists.

    Fail-soft like _hubspot_push_contact: never raises, never blocks the webhook.
    Klaviyo drives the day-27 pre-charge notice, so a failure here is logged
    loudly — a trial that never lands on the list gets no billing warning.
    """
    if not KLAVIYO_API_KEY or not email:
        return

    email_norm = email.lower().strip()
    attributes = {'email': email_norm}
    parts = (name or '').strip().split(None, 1)
    if parts:
        attributes['first_name'] = parts[0]
    if len(parts) > 1:
        attributes['last_name'] = parts[1]
    if properties:
        attributes['properties'] = {k: v for k, v in properties.items() if v is not None}

    profile_id = None
    try:
        r = http_requests.post(
            f'{KLAVIYO_API_BASE}/profile-import/',
            json={'data': {'type': 'profile', 'attributes': attributes}},
            headers=_klaviyo_headers(),
            timeout=10,
        )
        if r.status_code in (200, 201):
            profile_id = ((r.json() or {}).get('data') or {}).get('id')
        else:
            print(f'[Store API] Klaviyo profile upsert failed for {email_norm}: {r.status_code} {r.text[:200]}')
            return
    except Exception as e:
        print(f'[Store API] Klaviyo profile upsert error for {email_norm}: {e}')
        return

    if not profile_id:
        print(f'[Store API] Klaviyo returned no profile id for {email_norm}')
        return

    payload = {'data': [{'type': 'profile', 'id': profile_id}]}
    for list_id, method in ((add_list, 'post'), (remove_list, 'delete')):
        if not list_id:
            continue
        try:
            r = getattr(http_requests, method)(
                f'{KLAVIYO_API_BASE}/lists/{list_id}/relationships/profiles/',
                json=payload,
                headers=_klaviyo_headers(),
                timeout=10,
            )
            if r.status_code not in (200, 202, 204):
                print(f'[Store API] Klaviyo list {method} failed for {email_norm} (list {list_id}): {r.status_code} {r.text[:200]}')
        except Exception as e:
            print(f'[Store API] Klaviyo list {method} error for {email_norm} (list {list_id}): {e}')


def _send_email(from_addr, to_addr, subject, body):
    """Send an email via Resend. No-op if resend/key not configured."""
    if not resend or not os.environ.get('RESEND_API_KEY'):
        print(f'[Store API] Resend not configured, skipping email to {to_addr}')
        return False
    try:
        resend.Emails.send({
            "from": from_addr,
            "to": [to_addr] if isinstance(to_addr, str) else to_addr,
            "subject": subject,
            "html": body,
        })
        return True
    except Exception as e:
        print(f'[Store API] Resend send error: {e}')
        return False

# ── Stripe config ──
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')


def _plain(obj):
    """Recursively convert a Stripe response object into plain dicts/lists.

    stripe-python < 8 returned StripeObject, a dict subclass, so handler code
    could call .get() on it directly. From v15 StripeObject is no longer a dict
    subclass and .get() raises AttributeError, which 500s the whole webhook.
    Normalising once at the boundary keeps the handlers version-agnostic.
    Note to_dict() is shallow — nested objects stay StripeObject — so this has
    to recurse (checkout sessions nest customer_details, subs nest items.data).
    """
    if hasattr(obj, 'to_dict'):
        obj = obj.to_dict()
    if isinstance(obj, dict):
        return {k: _plain(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_plain(v) for v in obj]
    return obj

# Free-trial length applied to every new subscription checkout (card up front,
# charged only when the trial ends).
TRIAL_PERIOD_DAYS = int(os.environ.get('TRIAL_PERIOD_DAYS', '30'))

# Shared secret the individual apps present when calling /subscription-status to
# enforce access. Must match the value each app is configured with. If unset,
# the status endpoint refuses all requests (fail-closed).
SUBSCRIPTION_STATUS_SECRET = os.environ.get('SUBSCRIPTION_STATUS_SECRET', '')

# Store-side subscription states that grant access to an app.
ACTIVE_STATUSES = {'active', 'trialing'}

# Product → Stripe price ID mapping
PRICE_MAP = {
    'FLOWTRACK': os.environ.get('STRIPE_FLOWTRACK_PRICE_ID', ''),
    'QUALIFI':   os.environ.get('STRIPE_QUALIFI_PRICE_ID', ''),
    'SHIFTLOG':  os.environ.get('STRIPE_SHIFTLOG_PRICE_ID', ''),
    'REPORTR':   os.environ.get('STRIPE_REPORTR_PRICE_ID', ''),
    'INSPECTR':  os.environ.get('STRIPE_INSPECTR_PRICE_ID', ''),
    'LANDLORDR': os.environ.get('STRIPE_LANDLORDR_PRICE_ID', ''),
    'TENANTLINK': os.environ.get('STRIPE_TENANTLINK_PRICE_ID', ''),
    'PROPERTY_BUNDLE': os.environ.get('STRIPE_PROPERTY_BUNDLE_PRICE_ID', ''),
    'PERMITR':  os.environ.get('STRIPE_PERMITR_PRICE_ID', ''),
    'TASKFLOW': os.environ.get('STRIPE_TASKFLOW_PRICE_ID', ''),
    'OPSIQ':    os.environ.get('STRIPE_OPSIQ_PRICE_ID', ''),
    'COMPLI':   os.environ.get('STRIPE_COMPLI_PRICE_ID', ''),
    'EXTRACTR': os.environ.get('STRIPE_EXTRACTR_PRICE_ID', ''),
    'SUPPORTR': os.environ.get('STRIPE_SUPPORTR_PRICE_ID', ''),
    'MAINTAINR': os.environ.get('STRIPE_MAINTAINR_PRICE_ID', ''),
}

# Bundle definitions — maps bundle name to list of individual products
BUNDLE_MAP = {
    'PROPERTY_BUNDLE': ['LANDLORDR', 'TENANTLINK'],
}

# Product → App URL mapping
APP_URL_MAP = {
    'FLOWTRACK': 'https://flowtrack.plainspokenfoundrynine.com',
    'QUALIFI':   'https://qualifi.plainspokenfoundrynine.com',
    'SHIFTLOG':  'https://shiftlog.plainspokenfoundrynine.com',
    'REPORTR':   'https://reportr.plainspokenfoundrynine.com',
    'INSPECTR':  'https://inspectr.plainspokenfoundrynine.com',
    'LANDLORDR': 'https://landlordr.plainspokenfoundrynine.com',
    'TENANTLINK': 'https://tenantlinkr.plainspokenfoundrynine.com',
    'PERMITR':  'https://permitr.plainspokenfoundrynine.com',
    'TASKFLOW': 'https://taskflow.plainspokenfoundrynine.com',
    'OPSIQ':    'https://opsiq.plainspokenfoundrynine.com',
    'COMPLI':   'https://compli.plainspokenfoundrynine.com',
    'EXTRACTR': 'https://extractr.plainspokenfoundrynine.com',
    'SUPPORTR': 'https://supportr.plainspokenfoundrynine.com',
    'MAINTAINR': 'https://maintainr.plainspokenfoundrynine.com',
}

# Product → the app we suggest next, for the paid month-3 expansion email.
#
# Keyed by what the customer already has, because the pitch only lands if it
# names the connection. Pairings follow the workflow, not the product family:
# the app that picks up where the current one stops. Some pairs are deliberately
# reciprocal (REPORTR/EXTRACTR, COMPLI/PERMITR) — from either side the other
# half is genuinely the next thing you'd want.
#
# Every target is checked against index.html: it must have a live Subscribe or
# Start Free CTA. Nothing here may point at a "Join Waitlist" product, or the
# email's one call to action dead-ends.
#
# The Klaviyo template reads related_app_name / related_app_detail /
# related_app_url and has a |default: on each, so an unmapped product degrades
# to a generic "browse all apps" card rather than an empty one.
CROSS_SELL_MAP = {
    'FLOWTRACK': ('TASKFLOW',
        "FLOWTRACK shows you where work is; TASKFLOW is where it gets done — "
        "assignments, due dates and a clear view of what's blocked."),
    'TASKFLOW': ('FLOWTRACK',
        "Once tasks are running, FLOWTRACK shows the process behind them — where "
        "work queues up and which stage slows everything down."),
    'QUALIFI': ('INSPECTR',
        "Quality findings usually start with an inspection. INSPECTR handles the "
        "scheduled checks, photo evidence and sign-off that feed straight into QUALIFI."),
    'INSPECTR': ('COMPLI',
        "Inspection results are evidence. COMPLI maps them to the frameworks you're "
        "audited against, so findings become proof instead of paperwork — free to start."),
    'SHIFTLOG': ('PERMITR',
        "Handovers and permits cover the same shift change. PERMITR controls who is "
        "cleared to work on what, so your log matches what was actually authorised."),
    # COMPLI is the free tier on the storefront ("Start Free"), so lead with that —
    # an expansion email that implies a second invoice for a free app reads badly.
    'PERMITR': ('COMPLI',
        "Permits prove control on the day. COMPLI proves it across the year, mapping "
        "your permit records to the frameworks auditors ask about — and it's free to start."),
    'COMPLI': ('PERMITR',
        "COMPLI tracks the frameworks; PERMITR enforces them at the sharp end — no one "
        "starts high-risk work without a signed permit."),
    # Deliberately NOT OPSIQ from either of these, even though it is the sharpest
    # fit: OPSIQ is still "Coming Soon / Join Waitlist" on the storefront, so the
    # CTA would land on a waitlist form. Point these back at OPSIQ once it sells.
    'REPORTR': ('EXTRACTR',
        "REPORTR charts what is already in your systems. EXTRACTR goes after what "
        "isn't — the numbers still stuck in PDFs, invoices and scanned forms."),
    'EXTRACTR': ('REPORTR',
        "EXTRACTR gets the data out of your documents. REPORTR puts it on a "
        "dashboard that refreshes itself, instead of a spreadsheet you rebuild."),
    'OPSIQ': ('REPORTR',
        "OPSIQ answers one question at a time. REPORTR puts the answers you keep "
        "asking on a dashboard that refreshes itself."),
    'SUPPORTR': ('TASKFLOW',
        "Tickets that need real work behind them end up as tasks. TASKFLOW takes the "
        "handoff from SUPPORTR with an owner and a due date."),
    'LANDLORDR': ('MAINTAINR',
        "Every repair request in LANDLORDR becomes a work order in MAINTAINR — "
        "contractor assigned, parts tracked, cost recorded against the unit."),
    'TENANTLINK': ('MAINTAINR',
        "Tenants report problems in TENANTLINK; MAINTAINR turns those into scheduled "
        "work with a contractor, a cost and a completion date."),
    'PROPERTY_BUNDLE': ('MAINTAINR',
        "You already run the property and tenant side. MAINTAINR closes the loop — "
        "repair requests become scheduled work orders with costs tracked per unit."),
    'MAINTAINR': ('INSPECTR',
        "Reactive repairs drop when you catch problems early. INSPECTR runs the "
        "scheduled checks that generate work before something breaks."),
}


def _cross_sell_properties(product):
    """Klaviyo profile properties for the month-3 expansion email.

    Returns {} for an unknown product so the template's own |default: values
    apply — better a generic card than one naming an app that does not exist.
    """
    pair = CROSS_SELL_MAP.get(product)
    if not pair:
        return {}
    related, detail = pair
    return {
        'related_app_name': related,
        'related_app_detail': detail,
        # Deliberately the STORE, not APP_URL_MAP[related]: the recipient does
        # not own this app yet, so the app's own host would just show them a
        # login wall. ?product= opens that card's subscribe modal on the
        # storefront; if index.html is ever served without that handler the
        # param is ignored and they simply land on the store.
        'related_app_url': f'{STORE_URL}/?product={related}',
    }


# Product → Registration endpoint mapping
# Use loopback addresses — store API runs on the same pf9-apps host as the provisioning targets,
# so this skips Cloudflare/tunnel overhead and whatever routing weirdness affects public URLs.
REGISTER_MAP = {
    'FLOWTRACK':  'http://127.0.0.1:3001/api/auth/register',
    'REPORTR':    'http://127.0.0.1:3002/api/auth/register',
    'SHIFTLOG':   'http://127.0.0.1:3003/api/auth/register',
    'INSPECTR':   'http://127.0.0.1:3005/api/auth/register',
    'LANDLORDR':  'http://127.0.0.1:5001/api/auth/register',
    'TENANTLINK': 'http://127.0.0.1:5002/api/auth/register',
    'PERMITR':    'http://127.0.0.1:5003/api/auth/register',
    'TASKFLOW':   'http://127.0.0.1:5004/api/auth/register',
    'OPSIQ':      'http://127.0.0.1:5050/api/auth/register',
    'COMPLI':     'http://127.0.0.1:5200/api/v1/auth/register',
    'EXTRACTR':   'http://127.0.0.1:5300/api/auth/register',
    'SUPPORTR':   'http://127.0.0.1:5000/api/auth/register',
    'MAINTAINR':  'http://127.0.0.1:3008/api/auth/register',
    'QUALIFI':    'http://127.0.0.1:5400/api/auth/register',
}


# ── Database setup ──
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS demo_requests (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL,
                company     TEXT,
                email       TEXT NOT NULL,
                message     TEXT,
                product     TEXT,
                status      TEXT DEFAULT 'new',
                created_at  TEXT NOT NULL
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                id                      INTEGER PRIMARY KEY AUTOINCREMENT,
                stripe_customer_id      TEXT,
                stripe_subscription_id  TEXT UNIQUE,
                email                   TEXT NOT NULL,
                name                    TEXT,
                company                 TEXT,
                product                 TEXT NOT NULL,
                status                  TEXT DEFAULT 'active',
                provisioned             INTEGER DEFAULT 0,
                temp_password           TEXT,
                created_at              TEXT NOT NULL,
                cancelled_at            TEXT,
                trial_end               TEXT
            )
        ''')
        # Lightweight migration: add trial_end to pre-existing subscriptions tables.
        cols = {row['name'] for row in conn.execute("PRAGMA table_info(subscriptions)").fetchall()}
        if 'trial_end' not in cols:
            conn.execute('ALTER TABLE subscriptions ADD COLUMN trial_end TEXT')
        conn.commit()


def _generate_password(length=12):
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))


# ── Demo Request Routes ──
@store_bp.route('/demo-request', methods=['POST', 'OPTIONS'])
def demo_request():
    if request.method == 'OPTIONS':
        return _cors_response(jsonify({}))

    data = request.get_json(silent=True) or {}
    name    = (data.get('name') or '').strip()
    email   = (data.get('email') or '').strip()
    company = (data.get('company') or '').strip()
    message = (data.get('message') or '').strip()
    product = (data.get('product') or 'General').strip()

    if not name or not email:
        return _cors_response(jsonify({'success': False, 'error': 'Name and email are required'}), 400)

    try:
        with get_db() as conn:
            conn.execute(
                'INSERT INTO demo_requests (name, company, email, message, product, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                (name, company, email, message, product, datetime.utcnow().isoformat())
            )
            conn.commit()
    except Exception as e:
        print(f'[Store API] DB error: {e}')
        return _cors_response(jsonify({'success': False, 'error': 'Database error'}), 500)

    try:
        _send_notification(name, company, email, message, product)
    except Exception as e:
        print(f'[Store API] Email error: {e}')

    try:
        _hubspot_push_contact(
            email=email,
            name=name,
            company=company,
            list_id=_hubspot_list_for_product(product),
        )
    except Exception as e:
        print(f'[Store API] HubSpot push error: {e}')

    return _cors_response(jsonify({'success': True, 'message': 'Demo request received!'}))


@store_bp.route('/leads', methods=['GET'])
def get_leads():
    expected = os.environ.get('LEADS_SECRET', '')
    provided = request.headers.get('X-PF9-Secret', '') or request.args.get('secret', '')
    if not expected or not secrets.compare_digest(provided, expected):
        return _cors_response(jsonify({'error': 'Unauthorized'}), 401)

    with get_db() as conn:
        rows = conn.execute('SELECT * FROM demo_requests ORDER BY created_at DESC').fetchall()
    return _cors_response(jsonify({'leads': [dict(row) for row in rows], 'count': len(rows)}))


@store_bp.route('/health', methods=['GET'])
def health():
    return _cors_response(jsonify({'status': 'ok', 'service': 'store-api'}))


# ── Stripe Checkout Routes ──
@store_bp.route('/create-checkout-session', methods=['POST', 'OPTIONS'])
def create_checkout_session():
    if request.method == 'OPTIONS':
        return _cors_response(jsonify({}))

    if not stripe:
        return _cors_response(jsonify({'error': 'Stripe not configured'}), 500)

    data = request.get_json(silent=True) or {}
    product = (data.get('product') or '').strip().upper()
    email   = (data.get('email') or '').strip()
    name    = (data.get('name') or '').strip()
    company = (data.get('company') or '').strip()

    if not product or not email or not name:
        return _cors_response(jsonify({'error': 'Product, name, and email are required'}), 400)

    price_id = PRICE_MAP.get(product)
    if not price_id:
        return _cors_response(jsonify({'error': f'Unknown product: {product}'}), 400)

    try:
        session = stripe.checkout.Session.create(
            mode='subscription',
            line_items=[{'price': price_id, 'quantity': 1}],
            customer_email=email,
            success_url=f'{STORE_URL}/login.html?subscribed={product.lower()}&session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url=f'{STORE_URL}/#products',
            # 30-day free trial. Card is collected up front (payment_method_collection
            # defaults to 'always' for trials) but not charged until the trial ends,
            # at which point Stripe auto-converts to the paid subscription.
            subscription_data={'trial_period_days': TRIAL_PERIOD_DAYS},
            metadata={
                'product': product,
                'name': name,
                'company': company,
            },
        )
        return _cors_response(jsonify({'url': session.url}))
    except Exception as e:
        print(f'[Store API] Stripe error: {e}')
        return _cors_response(jsonify({'error': 'Failed to create checkout session'}), 500)


@store_bp.route('/subscription-status', methods=['GET'])
def subscription_status():
    """Read-only status lookup the individual apps call to enforce access.

    Auth: caller presents the shared secret via the `X-PF9-Secret` header (or
    `?secret=` fallback). Fail-closed — no secret configured server-side, or a
    mismatch, returns 401 and no data.

    Query params: product (store product key, e.g. TASKFLOW), email.
    Returns: {status, allowed, trial_end, product}. `allowed` is the single
    boolean the apps gate on; status is included for display/telemetry.
    """
    if not SUBSCRIPTION_STATUS_SECRET:
        return jsonify({'error': 'status endpoint not configured'}), 401
    provided = request.headers.get('X-PF9-Secret', '') or request.args.get('secret', '')
    if not secrets.compare_digest(provided, SUBSCRIPTION_STATUS_SECRET):
        return jsonify({'error': 'unauthorized'}), 401

    product = (request.args.get('product') or '').strip().upper()
    email   = (request.args.get('email') or '').strip().lower()
    if not product or not email:
        return jsonify({'error': 'product and email are required'}), 400

    # A subscription may be held directly (product == requested) or via a bundle
    # that includes it. Also tolerate the TENANTLINK/TENANTLINKR naming split.
    candidates = {product}
    if product == 'TENANTLINKR':
        candidates.add('TENANTLINK')
    elif product == 'TENANTLINK':
        candidates.add('TENANTLINKR')
    for bundle_name, members in BUNDLE_MAP.items():
        if product in members or any(c in members for c in list(candidates)):
            candidates.add(bundle_name)

    placeholders = ','.join('?' for _ in candidates)
    with get_db() as conn:
        row = conn.execute(
            f'''SELECT status, trial_end, product FROM subscriptions
                WHERE lower(email) = ? AND upper(product) IN ({placeholders})
                ORDER BY created_at DESC LIMIT 1''',
            (email, *[c.upper() for c in candidates])
        ).fetchone()

    if not row:
        return jsonify({'status': 'none', 'allowed': False, 'trial_end': None, 'product': product})

    status = (row['status'] or '').lower()
    return jsonify({
        'status': status,
        'allowed': status in ACTIVE_STATUSES,
        'trial_end': row['trial_end'],
        'product': row['product'],
    })


@store_bp.route('/stripe-webhook', methods=['POST'])
def stripe_webhook():
    if not stripe:
        return jsonify({'error': 'Stripe not configured'}), 500

    payload = request.data
    sig_header = request.headers.get('Stripe-Signature', '')

    # Fail closed: without a configured signing secret we cannot verify the
    # event came from Stripe, and this endpoint provisions real accounts. Refuse
    # rather than trust unsigned JSON.
    if not STRIPE_WEBHOOK_SECRET:
        print('[Store API] STRIPE_WEBHOOK_SECRET not configured; refusing webhook')
        return jsonify({'error': 'Webhook not configured'}), 500

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        print(f'[Store API] Webhook signature error: {e}')
        return jsonify({'error': 'Invalid signature'}), 400

    # Convert once at the boundary so every handler below can keep using plain
    # dict .get() access regardless of which stripe-python major is installed.
    obj = _plain(event['data']['object'])

    if event['type'] == 'checkout.session.completed':
        _handle_checkout_completed(obj)

    elif event['type'] == 'customer.subscription.deleted':
        _handle_subscription_cancelled(obj)

    elif event['type'] == 'customer.subscription.updated':
        _handle_subscription_updated(obj)

    elif event['type'] == 'invoice.payment_failed':
        _handle_payment_failed(obj)

    elif event['type'] == 'customer.subscription.trial_will_end':
        _handle_trial_will_end(obj)

    return jsonify({'received': True})


@store_bp.route('/create-portal-session', methods=['POST', 'OPTIONS'])
def create_portal_session():
    if request.method == 'OPTIONS':
        return _cors_response(jsonify({}))

    if not stripe:
        return _cors_response(jsonify({'error': 'Stripe not configured'}), 500)

    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip()

    if not email:
        return _cors_response(jsonify({'error': 'Email is required'}), 400)

    try:
        customers = stripe.Customer.list(email=email, limit=1)
        if not customers.data:
            return _cors_response(jsonify({'error': 'No subscription found for this email'}), 404)

        portal = stripe.billing_portal.Session.create(
            customer=customers.data[0].id,
            return_url=f'{STORE_URL}/login.html',
        )
        return _cors_response(jsonify({'url': portal.url}))
    except Exception as e:
        print(f'[Store API] Portal error: {e}')
        return _cors_response(jsonify({'error': 'Failed to create portal session'}), 500)


# ── Checkout/Webhook Handlers ──
def _handle_checkout_completed(session):
    meta = session.get('metadata', {})
    product = meta.get('product', '')
    name    = meta.get('name', '')
    company = meta.get('company', '')
    email   = session.get('customer_email', '') or session.get('customer_details', {}).get('email', '')
    customer_id = session.get('customer', '')
    subscription_id = session.get('subscription', '')

    if not product or not email:
        print(f'[Store API] Webhook missing product or email: {meta}')
        return

    # Idempotency check
    with get_db() as conn:
        existing = conn.execute(
            'SELECT id FROM subscriptions WHERE stripe_subscription_id = ?', (subscription_id,)
        ).fetchone()
        if existing:
            print(f'[Store API] Subscription {subscription_id} already processed')
            return

    # Generate temp password
    temp_password = _generate_password()

    # Pull the real subscription status + trial end from Stripe. A trial checkout
    # lands as 'trialing' (not 'active'); trial_end is a unix timestamp.
    sub_status = 'active'
    trial_end_iso = None
    price_display = None
    try:
        sub = _plain(stripe.Subscription.retrieve(subscription_id))
        sub_status = sub.get('status', 'active') or 'active'
        te = sub.get('trial_end')
        if te:
            trial_end_iso = datetime.utcfromtimestamp(int(te)).isoformat()
        # Read the amount actually being charged rather than a hardcoded figure,
        # so the pre-charge email can never quote a price that differs from the bill.
        items = ((sub.get('items') or {}).get('data')) or []
        if items:
            unit_amount = ((items[0].get('price') or {}).get('unit_amount'))
            if unit_amount is not None:
                dollars = unit_amount / 100
                price_display = f'{dollars:.0f}' if dollars == int(dollars) else f'{dollars:.2f}'
    except Exception as e:
        print(f'[Store API] Could not retrieve subscription {subscription_id}: {e}')

    # Save subscription
    with get_db() as conn:
        conn.execute(
            '''INSERT INTO subscriptions
               (stripe_customer_id, stripe_subscription_id, email, name, company, product, status, temp_password, created_at, trial_end)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (customer_id, subscription_id, email, name, company, product, sub_status, temp_password, datetime.utcnow().isoformat(), trial_end_iso)
        )
        conn.commit()

    # Provision account in the app (bundles provision multiple apps)
    products_to_provision = BUNDLE_MAP.get(product, [product])
    all_provisioned = True
    for p in products_to_provision:
        if not _provision_account(p, email, name, company, temp_password):
            all_provisioned = False

    if all_provisioned:
        # Password has been delivered to the app(s) and is about to be emailed to
        # the customer from the in-memory copy — don't retain it in cleartext.
        with get_db() as conn:
            conn.execute('UPDATE subscriptions SET provisioned = 1, temp_password = NULL WHERE stripe_subscription_id = ?', (subscription_id,))
            conn.commit()

    # Send welcome email
    try:
        _send_welcome_email(email, name, product, temp_password, all_provisioned)
    except Exception as e:
        print(f'[Store API] Welcome email error: {e}')

    # Push subscriber to HubSpot
    try:
        _hubspot_push_contact(
            email=email,
            name=name,
            company=company,
            list_id=HUBSPOT_LIST_SUBSCRIBERS,
        )
    except Exception as e:
        print(f'[Store API] HubSpot subscriber push error: {e}')

    # Enroll in the Klaviyo trial flow. trial_end_date is what the day-27
    # pre-charge email renders, so it has to be on the profile from day 0.
    trial_properties = {
        'app_name': product,
        'app_price': price_display,
        'trial_end_date': _klaviyo_format_trial_end(trial_end_iso),
        'manage_subscription_url': f'{STORE_URL}/login.html',
    }
    # Cross-sell target is a pure function of the product, so set it now rather
    # than waiting for conversion. Costs nothing, and means the month-3 email
    # has data even if the trialing -> active webhook is ever missed.
    trial_properties.update(_cross_sell_properties(product))
    _klaviyo_sync(
        email=email,
        name=name,
        properties=trial_properties,
        add_list=KLAVIYO_LIST_TRIAL,
    )

    print(f'[Store API] Subscription created: {product} for {email} (provisioned={all_provisioned})')


def _handle_subscription_cancelled(sub):
    subscription_id = sub.get('id', '')
    with get_db() as conn:
        conn.execute(
            'UPDATE subscriptions SET status = ?, cancelled_at = ? WHERE stripe_subscription_id = ?',
            ('cancelled', datetime.utcnow().isoformat(), subscription_id)
        )
        conn.commit()
        row = conn.execute(
            'SELECT email, name FROM subscriptions WHERE stripe_subscription_id = ?',
            (subscription_id,)
        ).fetchone()
    print(f'[Store API] Subscription cancelled: {subscription_id}')

    # Drop them off the trial list immediately. A cancelled trial must never
    # receive the day-27 notice warning about a charge that will not happen.
    if row and row['email']:
        _klaviyo_sync(
            email=row['email'],
            name=row['name'],
            properties={'subscription_status': 'cancelled'},
            remove_list=KLAVIYO_LIST_TRIAL,
        )


def _handle_subscription_updated(sub):
    subscription_id = sub.get('id', '')
    status = sub.get('status', '')
    te = sub.get('trial_end')
    trial_end_iso = datetime.utcfromtimestamp(int(te)).isoformat() if te else None
    with get_db() as conn:
        previous = conn.execute(
            'SELECT status, email, name, product FROM subscriptions WHERE stripe_subscription_id = ?',
            (subscription_id,)
        ).fetchone()
        conn.execute(
            'UPDATE subscriptions SET status = ?, trial_end = ? WHERE stripe_subscription_id = ?',
            (status, trial_end_iso, subscription_id)
        )
        conn.commit()
    print(f'[Store API] Subscription {subscription_id} status -> {status}')

    # trialing -> active is the day-30 conversion: hand them off from the trial
    # flow to paid onboarding. Guarded on the previous status so the repeated
    # 'active' updates Stripe sends on every renewal don't re-trigger it.
    if (
        previous
        and previous['email']
        and previous['status'] == 'trialing'
        and status == 'active'
    ):
        properties = {'app_name': previous['product'], 'subscription_status': 'active'}
        # The month-3 expansion email renders related_app_* off the profile.
        # Set it here as well as at checkout so a profile that predates the
        # checkout-side mapping still gets it on conversion.
        properties.update(_cross_sell_properties(previous['product']))
        _klaviyo_sync(
            email=previous['email'],
            name=previous['name'],
            properties=properties,
            add_list=KLAVIYO_LIST_PAID,
            remove_list=KLAVIYO_LIST_TRIAL,
        )


def _handle_trial_will_end(sub):
    """Stripe fires this ~3 days before a trial ends. Refresh the billing date
    everywhere so the day-27 pre-charge email quotes the date Stripe will
    actually charge on. The email itself is sent by Klaviyo, not here."""
    subscription_id = sub.get('id', '')
    te = sub.get('trial_end')
    trial_end_iso = datetime.utcfromtimestamp(int(te)).isoformat() if te else None

    # Look up who this is from our own records (avoids an extra Stripe call).
    row = None
    with get_db() as conn:
        if trial_end_iso:
            conn.execute(
                'UPDATE subscriptions SET trial_end = ? WHERE stripe_subscription_id = ?',
                (trial_end_iso, subscription_id)
            )
            conn.commit()
        row = conn.execute(
            'SELECT email, name, product FROM subscriptions WHERE stripe_subscription_id = ?',
            (subscription_id,)
        ).fetchone()

    print(f'[Store API] Trial ending soon for {subscription_id} (ends {trial_end_iso})')
    if not row or not row['email']:
        return

    _klaviyo_sync(
        email=row['email'],
        name=row['name'],
        properties={
            'app_name': row['product'],
            'trial_end_date': _klaviyo_format_trial_end(trial_end_iso),
        },
    )


def _handle_payment_failed(invoice):
    subscription_id = invoice.get('subscription', '')
    customer_email = invoice.get('customer_email', '') or ''
    attempt_count = invoice.get('attempt_count', 0)
    if not subscription_id:
        return
    with get_db() as conn:
        conn.execute(
            'UPDATE subscriptions SET status = ? WHERE stripe_subscription_id = ?',
            ('past_due', subscription_id)
        )
        conn.commit()
    print(f'[Store API] Payment failed for {subscription_id} (attempt {attempt_count}, {customer_email})')
    try:
        _send_payment_failed_alert(subscription_id, customer_email, attempt_count)
    except Exception as e:
        print(f'[Store API] Payment-failed alert error: {e}')


def _send_payment_failed_alert(subscription_id, customer_email, attempt_count):
    if not NOTIFY_EMAIL:
        return
    body = f"""
    <div style="font-family: sans-serif;">
        <h3>Stripe payment failed</h3>
        <p><b>Subscription:</b> {html.escape(subscription_id)}</p>
        <p><b>Customer:</b> {html.escape(customer_email) if customer_email else '(unknown)'}</p>
        <p><b>Attempt:</b> {attempt_count}</p>
        <p>Subscription marked <code>past_due</code> in store DB.</p>
    </div>
    """
    _send_email(EMAIL_FROM_INTERNAL, NOTIFY_EMAIL, f'[PF9 Store] Payment failed — {customer_email or subscription_id}', body)


def _provision_account(product, email, name, company, password):
    register_url = REGISTER_MAP.get(product)
    if not register_url:
        print(f'[Store API] No register URL for {product} (skipping provisioning)')
        return False

    # Inspectr uses 'companyName', others might use 'organizationName'
    if product == 'INSPECTR':
        payload = {'email': email, 'name': name, 'password': password, 'companyName': company}
    else:
        payload = {'email': email, 'name': name, 'password': password, 'organizationName': company}

    try:
        resp = http_requests.post(register_url, json=payload, timeout=15)
        if resp.status_code in (200, 201):
            print(f'[Store API] Provisioned {product} account for {email}')
            return True
        else:
            print(f'[Store API] Provisioning failed for {product}: {resp.status_code} {resp.text[:200]}')
            return False
    except Exception as e:
        print(f'[Store API] Provisioning error for {product}: {e}')
        return False


# ── Email Helpers ──
def _send_notification(name, company, email, message, product):
    if not NOTIFY_EMAIL:
        print('[Store API] NOTIFY_EMAIL not set, skipping notification')
        return
    e_name    = html.escape(name)
    e_company = html.escape(company) if company else '—'
    e_email   = html.escape(email)
    e_message = html.escape(message) if message else '—'
    e_product = html.escape(product)
    body = f"""
    <div style="font-family: sans-serif; max-width: 600px;">
        <h2 style="color: #111;">New Demo Request</h2>
        <table style="width:100%; border-collapse:collapse;">
            <tr><td style="padding:8px; font-weight:bold; width:120px;">Product</td><td style="padding:8px;">{e_product}</td></tr>
            <tr style="background:#f9f9f9"><td style="padding:8px; font-weight:bold;">Name</td><td style="padding:8px;">{e_name}</td></tr>
            <tr><td style="padding:8px; font-weight:bold;">Company</td><td style="padding:8px;">{e_company}</td></tr>
            <tr style="background:#f9f9f9"><td style="padding:8px; font-weight:bold;">Email</td><td style="padding:8px;"><a href="mailto:{e_email}">{e_email}</a></td></tr>
            <tr><td style="padding:8px; font-weight:bold; vertical-align:top;">Message</td><td style="padding:8px;">{e_message}</td></tr>
        </table>
        <p style="color:#888; font-size:12px; margin-top:24px;">Plainspoken Foundry Nine · store.plainspokenfoundrynine.com</p>
    </div>
    """
    if _send_email(EMAIL_FROM_INTERNAL, NOTIFY_EMAIL, f'[PF9 Store] New demo request — {product}', body):
        print(f'[Store API] Notification sent for {email}')


def _send_welcome_email(email, name, product, password, provisioned):
    first_name = html.escape(name.split()[0]) if name else 'there'
    e_email = html.escape(email)
    e_password = html.escape(password)
    bundle_products = BUNDLE_MAP.get(product)

    if bundle_products:
        subject = f'Welcome to your Property Bundle — Your accounts are ready!'
        login_rows = ''
        for bp in bundle_products:
            bp_url = APP_URL_MAP.get(bp, STORE_URL)
            login_rows += f'<tr><td style="padding:8px; font-weight:bold;">{html.escape(bp)}</td><td style="padding:8px;"><a href="{bp_url}">{bp_url}</a></td></tr>\n'
        if provisioned:
            login_section = f"""
            {login_rows}
            <tr style="background:#f9f9f9"><td style="padding:8px; font-weight:bold;">Email</td><td style="padding:8px;">{e_email}</td></tr>
            <tr><td style="padding:8px; font-weight:bold;">Temporary Password</td><td style="padding:8px; font-family:monospace; font-size:16px;">{e_password}</td></tr>
            <tr><td style="padding:8px; font-size:12px; color:#666;" colspan="2">Same login for both apps.</td></tr>
            """
        else:
            login_section = '<tr><td style="padding:8px;" colspan="2">Your accounts are being set up. We\'ll send your login details shortly.</td></tr>'
        product_label = 'Property Bundle (LANDLORDR + TENANTLINK)'
    else:
        subject = f'Welcome to {product} — Your account is ready!'
        app_url = APP_URL_MAP.get(product, STORE_URL)
        if provisioned:
            login_section = f"""
            <tr><td style="padding:8px; font-weight:bold;">Login URL</td><td style="padding:8px;"><a href="{app_url}">{app_url}</a></td></tr>
            <tr style="background:#f9f9f9"><td style="padding:8px; font-weight:bold;">Email</td><td style="padding:8px;">{e_email}</td></tr>
            <tr><td style="padding:8px; font-weight:bold;">Temporary Password</td><td style="padding:8px; font-family:monospace; font-size:16px;">{e_password}</td></tr>
            """
        else:
            login_section = '<tr><td style="padding:8px;" colspan="2">Your account is being set up. We\'ll send your login details shortly.</td></tr>'
        product_label = html.escape(product)

    body = f"""
    <div style="font-family: sans-serif; max-width: 600px;">
        <h2 style="color: #111;">Welcome to {product_label}, {first_name}!</h2>
        <p>Your subscription is active and your account{'s have' if bundle_products else ' has'} been created.</p>
        <table style="width:100%; border-collapse:collapse; margin: 20px 0;">
            {login_section}
        </table>
        <p style="color: #666;">Please change your password after your first login.</p>
        <p style="color:#888; font-size:12px; margin-top:24px;">Plainspoken Foundry Nine · store.plainspokenfoundrynine.com</p>
    </div>
    """
    if _send_email(EMAIL_FROM_CUSTOMER, email, subject, body):
        print(f'[Store API] Welcome email sent to {email}')


def _cors_response(response, status=200):
    response.headers['Access-Control-Allow-Origin']  = 'https://store.plainspokenfoundrynine.com'
    response.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.status_code = status
    return response


# ── Standalone entry point ──
if __name__ == '__main__':
    from flask import Flask
    app = Flask(__name__)
    app.register_blueprint(store_bp)
    init_db()
    print('[Store API] Starting on port 5001...')
    app.run(host='0.0.0.0', port=5001, debug=False)
