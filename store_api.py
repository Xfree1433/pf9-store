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
import smtplib
import os
import string
import secrets
import json
import requests as http_requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

try:
    import stripe
    stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', '')
except ImportError:
    stripe = None
    print('[Store API] WARNING: stripe package not installed')

store_bp = Blueprint('store', __name__, url_prefix='/store-api')

DB_PATH = os.environ.get('STORE_DB_PATH', '/opt/bridgr/store_leads.db')
STORE_URL = 'https://store.plainspokenfoundrynine.com'

# ── Email config ──
SMTP_HOST     = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT     = int(os.environ.get('SMTP_PORT', 587))
SMTP_USER     = os.environ.get('SMTP_USER', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
NOTIFY_EMAIL  = os.environ.get('NOTIFY_EMAIL', '')

# ── Stripe config ──
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')

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
}

# Product → Registration endpoint mapping
REGISTER_MAP = {
    'FLOWTRACK': 'https://flowtrack.plainspokenfoundrynine.com/api/auth/register',
    'REPORTR':   'https://reportr.plainspokenfoundrynine.com/api/auth/register',
    'SHIFTLOG':  'https://shiftlog.plainspokenfoundrynine.com/api/auth/register',
    'INSPECTR':  'https://inspectr.plainspokenfoundrynine.com/api/auth/register',
    'LANDLORDR': 'https://landlordr.plainspokenfoundrynine.com/api/auth/register',
    'TENANTLINK': 'https://tenantlinkr.plainspokenfoundrynine.com/api/auth/register',
    'PERMITR':  'https://permitr.plainspokenfoundrynine.com/api/auth/register',
    'TASKFLOW': 'https://taskflow.plainspokenfoundrynine.com/api/auth/register',
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
                cancelled_at            TEXT
            )
        ''')
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

    return _cors_response(jsonify({'success': True, 'message': 'Demo request received!'}))


@store_bp.route('/leads', methods=['GET'])
def get_leads():
    secret = request.args.get('secret', '')
    if secret != os.environ.get('LEADS_SECRET', 'changeme'):
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


@store_bp.route('/stripe-webhook', methods=['POST'])
def stripe_webhook():
    if not stripe:
        return jsonify({'error': 'Stripe not configured'}), 500

    payload = request.data
    sig_header = request.headers.get('Stripe-Signature', '')

    try:
        if STRIPE_WEBHOOK_SECRET:
            event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
        else:
            event = json.loads(payload)
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        print(f'[Store API] Webhook signature error: {e}')
        return jsonify({'error': 'Invalid signature'}), 400

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        _handle_checkout_completed(session)

    elif event['type'] == 'customer.subscription.deleted':
        sub = event['data']['object']
        _handle_subscription_cancelled(sub)

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

    # Save subscription
    with get_db() as conn:
        conn.execute(
            '''INSERT INTO subscriptions
               (stripe_customer_id, stripe_subscription_id, email, name, company, product, temp_password, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (customer_id, subscription_id, email, name, company, product, temp_password, datetime.utcnow().isoformat())
        )
        conn.commit()

    # Provision account in the app (bundles provision multiple apps)
    products_to_provision = BUNDLE_MAP.get(product, [product])
    all_provisioned = True
    for p in products_to_provision:
        if not _provision_account(p, email, name, company, temp_password):
            all_provisioned = False

    if all_provisioned:
        with get_db() as conn:
            conn.execute('UPDATE subscriptions SET provisioned = 1 WHERE stripe_subscription_id = ?', (subscription_id,))
            conn.commit()

    # Send welcome email
    try:
        _send_welcome_email(email, name, product, temp_password, provisioned)
    except Exception as e:
        print(f'[Store API] Welcome email error: {e}')

    print(f'[Store API] Subscription created: {product} for {email} (provisioned={provisioned})')


def _handle_subscription_cancelled(sub):
    subscription_id = sub.get('id', '')
    with get_db() as conn:
        conn.execute(
            'UPDATE subscriptions SET status = ?, cancelled_at = ? WHERE stripe_subscription_id = ?',
            ('cancelled', datetime.utcnow().isoformat(), subscription_id)
        )
        conn.commit()
    print(f'[Store API] Subscription cancelled: {subscription_id}')


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
    if not SMTP_USER or not SMTP_PASSWORD or not NOTIFY_EMAIL:
        print('[Store API] Email not configured, skipping notification')
        return

    msg = MIMEMultipart('alternative')
    msg['Subject'] = f'[PF9 Store] New demo request — {product}'
    msg['From']    = SMTP_USER
    msg['To']      = NOTIFY_EMAIL

    html = f"""
    <div style="font-family: sans-serif; max-width: 600px;">
        <h2 style="color: #111;">New Demo Request</h2>
        <table style="width:100%; border-collapse:collapse;">
            <tr><td style="padding:8px; font-weight:bold; width:120px;">Product</td><td style="padding:8px;">{product}</td></tr>
            <tr style="background:#f9f9f9"><td style="padding:8px; font-weight:bold;">Name</td><td style="padding:8px;">{name}</td></tr>
            <tr><td style="padding:8px; font-weight:bold;">Company</td><td style="padding:8px;">{company or '—'}</td></tr>
            <tr style="background:#f9f9f9"><td style="padding:8px; font-weight:bold;">Email</td><td style="padding:8px;"><a href="mailto:{email}">{email}</a></td></tr>
            <tr><td style="padding:8px; font-weight:bold; vertical-align:top;">Message</td><td style="padding:8px;">{message or '—'}</td></tr>
        </table>
        <p style="color:#888; font-size:12px; margin-top:24px;">Plainspoken Foundry Nine · store.plainspokenfoundrynine.com</p>
    </div>
    """
    msg.attach(MIMEText(html, 'html'))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, NOTIFY_EMAIL, msg.as_string())

    print(f'[Store API] Notification sent for {email}')


def _send_welcome_email(email, name, product, password, provisioned):
    if not SMTP_USER or not SMTP_PASSWORD:
        print('[Store API] Email not configured, skipping welcome email')
        return

    first_name = name.split()[0] if name else 'there'
    bundle_products = BUNDLE_MAP.get(product)

    msg = MIMEMultipart('alternative')
    msg['From']    = SMTP_USER
    msg['To']      = email

    if bundle_products:
        # Bundle welcome email — list all apps
        msg['Subject'] = f'Welcome to your Property Bundle — Your accounts are ready!'
        login_rows = ''
        for bp in bundle_products:
            bp_url = APP_URL_MAP.get(bp, STORE_URL)
            login_rows += f'<tr><td style="padding:8px; font-weight:bold;">{bp}</td><td style="padding:8px;"><a href="{bp_url}">{bp_url}</a></td></tr>\n'
        if provisioned:
            login_section = f"""
            {login_rows}
            <tr style="background:#f9f9f9"><td style="padding:8px; font-weight:bold;">Email</td><td style="padding:8px;">{email}</td></tr>
            <tr><td style="padding:8px; font-weight:bold;">Temporary Password</td><td style="padding:8px; font-family:monospace; font-size:16px;">{password}</td></tr>
            <tr><td style="padding:8px;" colspan="2" style="font-size:12px; color:#666;">Same login for both apps.</td></tr>
            """
        else:
            login_section = f"""
            <tr><td style="padding:8px;" colspan="2">Your accounts are being set up. We'll send your login details shortly.</td></tr>
            """
        product_label = 'Property Bundle (LANDLORDR + TENANTLINK)'
    else:
        # Single product welcome email
        msg['Subject'] = f'Welcome to {product} — Your account is ready!'
        app_url = APP_URL_MAP.get(product, STORE_URL)
        if provisioned:
            login_section = f"""
            <tr><td style="padding:8px; font-weight:bold;">Login URL</td><td style="padding:8px;"><a href="{app_url}">{app_url}</a></td></tr>
            <tr style="background:#f9f9f9"><td style="padding:8px; font-weight:bold;">Email</td><td style="padding:8px;">{email}</td></tr>
            <tr><td style="padding:8px; font-weight:bold;">Temporary Password</td><td style="padding:8px; font-family:monospace; font-size:16px;">{password}</td></tr>
            """
        else:
            login_section = f"""
            <tr><td style="padding:8px;" colspan="2">Your account is being set up. We'll send your login details shortly.</td></tr>
            """
        product_label = product

    html = f"""
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
    msg.attach(MIMEText(html, 'html'))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, email, msg.as_string())

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
