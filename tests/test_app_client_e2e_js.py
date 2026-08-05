"""End-to-end for the JS apps: their REAL client -> a real store -> a real row.

    ./venv/bin/python tests/test_app_client_e2e_js.py APP_DIR PRODUCT

    ./venv/bin/python tests/test_app_client_e2e_js.py \
        ~/Documents/PlainSpokenFoundryNine/FLOWTRACK FLOWTRACK

The twin of tests/test_app_client_e2e.py, which does the same job for the Flask
apps. Same store, same socket, same assertions; the only difference is that the
client under test is TypeScript or ESM JavaScript, so it is driven by a node
subprocess instead of imported into this process.

The .ts clients are loaded by node's built-in type stripping (unflagged since
node 23.6) rather than compiled to a copy first, so what runs here is the file
that ships -- a test against a transpiled duplicate could pass while the real
module is broken.

Exits non-zero on failure. Nothing leaves the machine: the Klaviyo helpers are
replaced with recorders and the store runs on localhost.
"""
import os
import sys
import json
import time
import socket
import shutil
import tempfile
import subprocess
import threading

STORE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_DIR = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else
                             '~/Documents/PlainSpokenFoundryNine/FLOWTRACK')
PRODUCT = sys.argv[2] if len(sys.argv) > 2 else 'FLOWTRACK'

# Next.js apps keep it at src/lib/store-activity.ts; INSPECTR's server is plain
# ESM JavaScript, so its copy is server/store-activity.js.
CLIENT = next(
    (p for p in (os.path.join(APP_DIR, *parts) for parts in
                 (('src', 'lib', 'store-activity.ts'),
                  ('server', 'store-activity.js')))
     if os.path.exists(p)), None)

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

URL = f'http://127.0.0.1:{PORT}/store-api/app-activity'

if not shutil.which('node'):
    print('node not on PATH')
    sys.exit(1)
if CLIENT is None:
    print(f'no client under {APP_DIR} -- is {PRODUCT} wired yet?')
    sys.exit(1)

# The driver imports the app's client and calls it exactly as the app does,
# then waits for the in-flight request so the assertions below are not racing
# it. `sent` distinguishes "the client declined to send" (null) from "the
# client sent something", which is what the demo/no-secret cases turn on.
DRIVER = r'''
const [clientPath, email, kind, action] = process.argv.slice(2);
const m = await import(clientPath);
// argv cannot carry a NUL, so hostile values arrive as these sentinels.
// No real email can contain '<', so there is no collision with a live value.
const arg = email === '<null>' ? null
          : email === '<undefined>' ? undefined
          : email === '<number>' ? 123
          : email === '<object>' ? {}
          : email === '<array>' ? ['a@b.c']
          : email;
const p = m.report(arg, kind, action);
if (p) await p;
console.log(JSON.stringify({ sent: p !== null, product: m.PRODUCT }));
'''
_driver = tempfile.NamedTemporaryFile('w', suffix='.mjs', delete=False)
_driver.write(DRIVER)
_driver.close()

fails = []


def expect(label, cond, detail=''):
    print(f'  {"ok  " if cond else "FAIL"}  {label}' +
          (f'   <- {detail}' if detail and not cond else ''))
    if not cond:
        fails.append(label)


def rows():
    with store_api.get_db() as conn:
        return [dict(r) for r in conn.execute('SELECT * FROM app_activity').fetchall()]


def fire(email, kind, action='', secret=SECRET, url=URL):
    """Run the app's client in node. Returns (sent, product) or raises."""
    del synced[:], events[:]
    env = dict(os.environ, ACTIVITY_SECRET=secret, STORE_ACTIVITY_URL=url)
    proc = subprocess.run(
        ['node', _driver.name, CLIENT, str(email), kind, action],
        capture_output=True, text=True, env=env, timeout=60)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip()[-800:])
    return json.loads(proc.stdout.strip().splitlines()[-1])


print(f'\n{PRODUCT} client -> store, over a real socket')
print(f'client: {CLIENT}\n')

first = fire(EMAIL, 'login')
expect(f'client declares PRODUCT={PRODUCT}', first['product'] == PRODUCT, first['product'])
expect('product is a PRICE_MAP key', first['product'] in store_api.PRICE_MAP)

expect('login ping was sent', first['sent'])
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
res = fire('demo@plainspokenfoundrynine.com', 'login')
expect('demo login not sent', not res['sent'])
expect('demo wrote no row', len(rows()) == 1, rows())

res = fire(EMAIL, 'login', secret='')
expect('no secret => nothing sent (safe to deploy early)', not res['sent'])
expect('no secret => count unchanged', rows()[0]['login_count'] == before, rows())

# Port 1 refuses instantly; the point is that the client swallows it rather
# than rejecting, which in node would take the whole process down.
try:
    fire(EMAIL, 'login', url='http://127.0.0.1:1/store-api/app-activity')
    expect('unreachable store does not reject', True)
except Exception as e:
    expect('unreachable store does not reject', False, e)

# The caller is a sign-in callback: report() must survive anything, or
# marketing telemetry becomes a failed login.
for bad in ['null', 'undefined', 'number', 'object', 'array']:
    try:
        fire(f'<{bad}>', 'login')
        expect(f'survives email={bad}', True)
    except Exception as e:
        expect(f'survives email={bad}', False, e)

fire('colleague.never.bought@example.com', 'login')
expect('non-customer wrote no row', len(rows()) == 1, rows())
expect('non-customer not sent to Klaviyo', not synced and not events, (synced, events))

print()
print('final row:', json.dumps(rows()[0], indent=2, default=str))
srv.shutdown()
os.unlink(_driver.name)
print('\n' + ('FAILED: ' + ', '.join(fails) if fails else 'ALL PASSED'))
sys.exit(1 if fails else 0)
