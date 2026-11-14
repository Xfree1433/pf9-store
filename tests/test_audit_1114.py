"""Store fixes from the 2026-11-14 code audit (board #1043).

    ./venv/bin/python tests/test_audit_1114.py

1. /subscription-status: any ACTIVE row wins over a newer inactive one (a
   cancelled trial under a payer's email must not lock the payer out).
2. Checkout start and demo request are throttled per visitor.
3. A Stripe replay of a paid-but-unprovisioned checkout alerts a human.
4. If Stripe can't be asked for the subscription's status, retry once and alert.
"""
import os, sys, tempfile, time

os.environ['STORE_DB_PATH'] = tempfile.mktemp(suffix='.db')
os.environ.setdefault('KLAVIYO_API_KEY', '')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import store_api

sent = []
store_api._send_email = lambda frm, to, subj, body: sent.append((to, subj, body)) or True
store_api.NOTIFY_EMAIL = 'ops@example.com'
store_api.init_db()

from flask import Flask
app = Flask(__name__)
app.register_blueprint(store_api.store_bp)
client = app.test_client()
fails = []


def check(cond, label):
    print(('PASS ' if cond else 'FAIL ') + label)
    if not cond:
        fails.append(label)


def add_sub(sub_id, email, product, status, created, provisioned=1):
    with store_api.get_db() as c:
        c.execute('INSERT INTO subscriptions (stripe_subscription_id, email, product, status, created_at, provisioned) '
                  'VALUES (?,?,?,?,?,?)', (sub_id, email, product, status, created, provisioned))
        c.commit()


print('=== 1. subscription-status: an active row beats a newer cancelled one ===')
store_api.SUBSCRIPTION_STATUS_SECRET = 'status-secret'
add_sub('sub_payer', 'payer@example.com', 'TASKFLOW', 'active', '2026-01-01T00:00:00')
add_sub('sub_grief', 'payer@example.com', 'TASKFLOW', 'canceled', '2026-06-01T00:00:00')
r = client.get('/store-api/subscription-status?product=TASKFLOW&email=payer@example.com', headers={'X-PF9-Secret': 'status-secret'})
d = r.get_json()
check(r.status_code == 200 and d['allowed'] is True and d['status'] == 'active', f'payer still allowed: {d}')
add_sub('sub_gone', 'gone@example.com', 'TASKFLOW', 'active', '2026-01-01T00:00:00')
with store_api.get_db() as c:
    c.execute("UPDATE subscriptions SET status='canceled' WHERE stripe_subscription_id='sub_gone'"); c.commit()
d = client.get('/store-api/subscription-status?product=TASKFLOW&email=gone@example.com', headers={'X-PF9-Secret': 'status-secret'}).get_json()
check(d['allowed'] is False and d['status'] == 'canceled', f'only-cancelled customer still refused: {d}')

print('=== 2. per-visitor throttles ===')
store_api._VISITOR_HITS.clear()
codes = [client.post('/store-api/demo-request', json={}, environ_base={'REMOTE_ADDR': '203.0.113.9'}).status_code for _ in range(7)]
check(codes[:5].count(429) == 0 and codes[5:] == [429, 429], f'demo-request: 5 allowed then 429: {codes}')
other = client.post('/store-api/demo-request', json={}, environ_base={'REMOTE_ADDR': '203.0.113.10'}).status_code
check(other != 429, 'a different visitor is not throttled')
store_api._VISITOR_HITS.clear()
codes = [client.post('/store-api/create-checkout-session', json={}, environ_base={'REMOTE_ADDR': '203.0.113.9'}).status_code for _ in range(22)]
check(codes[:20].count(429) == 0 and codes[20:] == [429, 429], f'checkout: 20 allowed then 429 (last: {codes[18:]})')
store_api._VISITOR_HITS.clear()
# Behind the tunnel every request arrives from loopback: the CF header decides.
a = [client.post('/store-api/demo-request', json={}, headers={'CF-Connecting-IP': '198.51.100.1'},
                 environ_base={'REMOTE_ADDR': '127.0.0.1'}).status_code for _ in range(6)]
b = client.post('/store-api/demo-request', json={}, headers={'CF-Connecting-IP': '198.51.100.2'},
                environ_base={'REMOTE_ADDR': '127.0.0.1'}).status_code
check(a[-1] == 429 and b != 429, f'tunnel visitors are told apart by CF-Connecting-IP: {a} / {b}')
store_api._VISITOR_HITS.clear()
spoof = [client.post('/store-api/demo-request', json={}, headers={'CF-Connecting-IP': f'10.0.0.{i}'},
                     environ_base={'REMOTE_ADDR': '203.0.113.50'}).status_code for i in range(7)]
check(spoof[-1] == 429, f'a direct caller cannot dodge the limit with a forged CF header: {spoof}')

print('=== 3. replay of a paid-but-unprovisioned checkout alerts ===')
sent.clear()
add_sub('sub_crashed', 'crash@example.com', 'TASKFLOW', 'active', '2026-11-14T00:00:00', provisioned=0)
session = {'metadata': {'product': 'TASKFLOW', 'name': 'C'}, 'customer_email': 'crash@example.com',
           'customer': 'cus_x', 'subscription': 'sub_crashed', 'mode': 'subscription'}
handler = store_api._handle_checkout_completed
handler(session)
check(any('crash@example.com' in (s[1] + s[2]) for s in sent), f'alert sent for the unprovisioned replay ({len(sent)} mail)')
sent.clear()
add_sub('sub_done', 'done@example.com', 'TASKFLOW', 'active', '2026-11-14T00:00:00', provisioned=1)
handler({**session, 'customer_email': 'done@example.com', 'subscription': 'sub_done'})
check(sent == [], 'a normal (provisioned) replay stays silent')

print('=== 4. Stripe status lookup: one retry, then an alert ===')
sent.clear(); calls = []


class _Boom:
    class Subscription:
        @staticmethod
        def retrieve(sid):
            calls.append(sid)
            raise RuntimeError('stripe down')


orig = (store_api.stripe, store_api._provision_account, time.sleep)
store_api.stripe = _Boom
store_api._provision_account = lambda *a, **k: 'ok'
time.sleep = lambda s: None
try:
    handler({**session, 'customer_email': 'new@example.com', 'subscription': 'sub_new'})
finally:
    store_api.stripe, store_api._provision_account, time.sleep = orig
check(len(calls) == 2, f'retried once ({len(calls)} calls)')
check(any('assumed' in s[1].lower() for s in sent), 'a human is told the status was assumed')
with store_api.get_db() as c:
    row = c.execute("SELECT status FROM subscriptions WHERE stripe_subscription_id='sub_new'").fetchone()
check(row is not None and row['status'] == 'active', 'the paid checkout is still recorded (as before)')

print()
if fails:
    print('FAILURES:'); [print('  -', f) for f in fails]; sys.exit(1)
print('all 11-14 store checks passed')
