"""Drive the real /create-portal-session route with Stripe and email stubbed.

    ./venv/bin/python tests/test_portal_session.py

Security audit 2026-10-26: the route returned the Stripe billing-portal URL to
whoever typed an email, so anyone could open any customer's billing. Pinned
here: no URL ever comes back in the response, the link is emailed only to the
address itself, a non-customer gets the identical answer (no enumeration), and
repeat requests for one address within a minute send nothing.
"""
import os, sys, tempfile

os.environ['STORE_DB_PATH'] = tempfile.mktemp(suffix='.db')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import store_api

PORTAL_URL = 'https://billing.stripe.com/p/session/test_SECRET123'
sent = []


class _List:
    def __init__(self, data):
        self.data = data


class _Cust:
    id = 'cus_test1'


class _Stripe:
    class Customer:
        @staticmethod
        def list(email, limit):
            return _List([_Cust()] if email == 'buyer@example.com' else [])

    class billing_portal:
        class Session:
            @staticmethod
            def create(customer, return_url):
                class _S:
                    url = PORTAL_URL
                return _S()


store_api.stripe = _Stripe
store_api._send_email = lambda frm, to, subj, body: sent.append((to, subj, body)) or True

from flask import Flask
app = Flask(__name__)
app.register_blueprint(store_api.store_bp)
client = app.test_client()
fails = []


def check(cond, label):
    print(('PASS ' if cond else 'FAIL ') + label)
    if not cond:
        fails.append(label)


def post(email):
    return client.post('/store-api/create-portal-session', json={'email': email})


r = post('buyer@example.com')
check(r.status_code == 200, 'customer: 200')
check(PORTAL_URL not in r.get_data(as_text=True), 'customer: portal URL is NOT in the response')
check(r.get_json().get('sent') is True, 'customer: response says sent')
check(len(sent) == 1 and sent[0][0] == 'buyer@example.com', 'customer: one email, to the address itself')
check(len(sent) == 1 and PORTAL_URL in sent[0][2], 'customer: the email carries the link')

r2 = post('stranger@example.com')
check(r2.get_json() == r.get_json() and r2.status_code == r.status_code,
      'non-customer: identical answer (no enumeration)')
check(len(sent) == 1, 'non-customer: no email sent')

r3 = post('buyer@example.com')
check(r3.get_json() == r.get_json() and len(sent) == 1, 'repeat within a minute: same answer, no second email')

check(post('').status_code == 400, 'blank email: 400')

if fails:
    print(f'{len(fails)} FAILED')
    sys.exit(1)
print('all passed')
