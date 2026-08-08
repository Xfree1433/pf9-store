"""End-to-end: an app's REAL activity client -> a real store server -> a real row.

    ./venv/bin/python tests/test_app_client_e2e.py [APP_DIR] [PRODUCT]

Defaults to PERMITR, the first app wired (2026-08-05). Point it at the next
app's repo as each one is integrated:

    ./venv/bin/python tests/test_app_client_e2e.py ~/Documents/PlainSpokenFoundryNine/apps/SUPPORTR SUPPORTR

Exits non-zero on failure. Nothing leaves the process: the Klaviyo helpers are
replaced with recorders and the store runs on localhost.

Why this exists alongside tests/test_app_activity.py, which already covers the
route thoroughly: that suite drives the endpoint with Flask's `test_client`,
which is right for testing the store but bypasses every part of an *app-side*
client that can actually be wrong in production -- the URL, the header name,
JSON serialisation, the socket, and the daemon thread. A client can pass a
test_client-based check and still send nothing to the real host. So this runs a
real werkzeug server on a real port and lets the app's own `requests.post`
reach it, importing the app's module from its own repo rather than a copy.
"""
import os
import sys
import json
import time
import socket
import tempfile
import threading
import importlib.util

STORE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_DIR = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else
                             '~/Documents/PlainSpokenFoundryNine/apps/PERMITR')
PRODUCT = sys.argv[2] if len(sys.argv) > 2 else 'PERMITR'

# The client sits beside the app package, and the apps do not agree on what that
# package is called: most use app/, OPSIQ uses opsiq/, QUALIFI's backend is flat.
# Search rather than hardcode, so adding an app does not mean editing this line.
CLIENT = next(
    (p for p in (os.path.join(APP_DIR, d, 'store_activity.py')
                 for d in ('app', 'opsiq', 'backend', '.'))
     if os.path.exists(p)),
    os.path.join(APP_DIR, 'app', 'store_activity.py'))

os.environ['STORE_DB_PATH'] = tempfile.mktemp(suffix='.db')
os.environ['KLAVIYO_API_KEY'] = 'test-key-not-used'
sys.path.insert(0, STORE)
import store_api  # noqa: E402

SECRET = 'e2e-secret-value'
store_api.ACTIVITY_SECRET = SECRET

synced, events = [], []
store_api._klaviyo_sync = lambda **k: synced.append(k)
store_api._klaviyo_event = lambda metric, email, **k: events.append(
    dict(metric=metric, email=email, **k))
store_api.init_db()

EMAIL = 'first.customer@example.com'
with store_api.get_db() as conn:
    conn.execute(
        'INSERT INTO subscriptions (stripe_subscription_id, email, name, product, status, created_at) '
        'VALUES (?, ?, ?, ?, ?, ?)',
        ('sub_e2e', EMAIL, 'Test Customer', PRODUCT, 'active', '2026-08-05T00:00:00'))
    conn.commit()

from flask import Flask                       # noqa: E402
from werkzeug.serving import make_server      # noqa: E402

flask_app = Flask(__name__)
flask_app.register_blueprint(store_api.store_bp)
_s = socket.socket()
_s.bind(('127.0.0.1', 0))
PORT = _s.getsockname()[1]
_s.close()
srv = make_server('127.0.0.1', PORT, flask_app)
threading.Thread(target=srv.serve_forever, daemon=True).start()
time.sleep(0.3)

os.environ['STORE_ACTIVITY_URL'] = f'http://127.0.0.1:{PORT}/store-api/app-activity'
os.environ['ACTIVITY_SECRET'] = SECRET

if not os.path.exists(CLIENT):
    print(f'no client at {CLIENT} -- is {PRODUCT} wired yet?')
    sys.exit(1)
spec = importlib.util.spec_from_file_location('app_store_activity', CLIENT)
sa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sa)

fails = []


def expect(label, cond, detail=''):
    print(f'  {"ok  " if cond else "FAIL"}  {label}' +
          (f'   <- {detail}' if detail and not cond else ''))
    if not cond:
        fails.append(label)


def rows():
    with store_api.get_db() as conn:
        return [dict(r) for r in conn.execute('SELECT * FROM app_activity').fetchall()]


def fire(*a, **k):
    del synced[:], events[:]
    t = sa.report(*a, **k)
    if t:
        t.join(10)
    return t


print(f'\n{PRODUCT} client -> store, over a real socket\n')

expect(f'client declares PRODUCT={PRODUCT}', sa.PRODUCT == PRODUCT, sa.PRODUCT)
expect('product is a PRICE_MAP key', sa.PRODUCT in store_api.PRICE_MAP)

t = fire(EMAIL, 'login')
expect('login ping was sent', t is not None)
r = rows()
expect('exactly one app_activity row', len(r) == 1, r)
expect('row is (customer, product)',
       bool(r) and r[0]['email'] == EMAIL and r[0]['product'] == PRODUCT, r)
expect('login_count = 1', bool(r) and r[0]['login_count'] == 1, r)
expect('last_login_at stamped', bool(r and r[0]['last_login_at']), r)
expect('Klaviyo profile synced', len(synced) == 1, synced)
expect('App Activity event fired', any(e['metric'] == 'App Activity' for e in events), events)

fire(EMAIL, 'action', 'core_action')
r = rows()
expect('still one row (summary, not a log)', len(r) == 1, r)
expect('action_count = 1', bool(r) and r[0]['action_count'] == 1, r)
expect('last_action recorded', bool(r) and r[0].get('last_action') == 'core_action', r)
expect('activated_apps carries the product',
       any(PRODUCT in str(s) for s in synced), synced)

before = rows()[0]['login_count']

# The storefront demo account is traffic, not usage. Clients guard it internally
# so no call site has to remember; a client that skips this still passes the
# consent gate, but burns a round trip on every demo click.
t = fire('demo@plainspokenfoundrynine.com', 'login')
expect('demo login not sent', t is None)
expect('demo wrote no row', len(rows()) == 1, rows())

os.environ['ACTIVITY_SECRET'] = ''
t = fire(EMAIL, 'login')
expect('no secret => nothing sent (safe to deploy early)', t is None)
expect('no secret => count unchanged', rows()[0]['login_count'] == before, rows())
os.environ['ACTIVITY_SECRET'] = SECRET

os.environ['STORE_ACTIVITY_URL'] = 'http://127.0.0.1:1/store-api/app-activity'
try:
    t = sa.report(EMAIL, 'login')
    if t:
        t.join(10)
    expect('unreachable store does not raise', True)
except Exception as e:
    expect('unreachable store does not raise', False, e)
os.environ['STORE_ACTIVITY_URL'] = f'http://127.0.0.1:{PORT}/store-api/app-activity'

# The caller is a login view: the synchronous part of report() must survive
# anything, or marketing telemetry becomes a 500 on the sign-in page.
for bad in [None, 123, object(), b'x@y.com', ['a@b.c']]:
    try:
        t = sa.report(bad, 'login')
        if t:
            t.join(5)
        expect(f'survives email={type(bad).__name__}', True)
    except Exception as e:
        expect(f'survives email={type(bad).__name__}', False, e)

fire('colleague.never.bought@example.com', 'login')
expect('non-customer wrote no row', len(rows()) == 1, rows())
expect('non-customer not sent to Klaviyo', not synced and not events, (synced, events))

print()
print('final row:', json.dumps(rows()[0], indent=2, default=str))
srv.shutdown()
print('\n' + ('FAILED: ' + ', '.join(fails) if fails else 'ALL PASSED'))
sys.exit(1 if fails else 0)
