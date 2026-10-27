"""Security audit 2026-10-26 (#933): store secrets and Show Pass fulfilment.

    ./venv/bin/python tests/test_audit_933.py

Pinned: /leads and /subscription-status take their secret from the header
only (a ?secret= query string ends up in access logs); a one-time checkout is
fulfilled only once Stripe reports it paid, so a delayed payment method that
has not settled yet provisions nothing.
"""
import os, sys, tempfile

os.environ['STORE_DB_PATH'] = tempfile.mktemp(suffix='.db')
os.environ['SUBSCRIPTION_STATUS_SECRET'] = 'status-secret-for-test'
os.environ['LEADS_SECRET'] = 'leads-secret-for-test'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import store_api

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


q = '/store-api/subscription-status?product=TASKFLOW&email=a@example.com'
check(client.get(q + '&secret=status-secret-for-test').status_code == 401,
      'subscription-status: secret in the URL is refused')
check(client.get(q, headers={'X-PF9-Secret': 'status-secret-for-test'}).status_code != 401,
      'subscription-status: secret in the header still works')
check(client.get('/store-api/leads?secret=leads-secret-for-test').status_code == 401,
      'leads: secret in the URL is refused')
check(client.get('/store-api/leads', headers={'X-PF9-Secret': 'leads-secret-for-test'}).status_code == 200,
      'leads: secret in the header still works')


class Reached(Exception):
    pass


def _boom():
    raise Reached()


real_get_db = store_api.get_db
store_api.get_db = _boom
session = {'id': 'cs_test_1', 'mode': 'payment', 'payment_intent': 'pi_test_1',
           'customer_email': 'buyer@example.com', 'metadata': {'product': 'SHOWJUDGR'}}
try:
    store_api._handle_one_time_completed(dict(session, payment_status='unpaid'))
    check(True, 'one-time: unpaid checkout stops before fulfilment')
except Reached:
    check(False, 'one-time: unpaid checkout stops before fulfilment')
try:
    store_api._handle_one_time_completed(dict(session, payment_status='paid'))
    check(False, 'one-time: paid checkout goes on to fulfilment')
except Reached:
    check(True, 'one-time: paid checkout goes on to fulfilment')
store_api.get_db = real_get_db

if fails:
    print(f'{len(fails)} FAILED')
    sys.exit(1)
print('all passed')
