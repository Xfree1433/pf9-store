"""Drive the real /store-api/app-activity route. Nothing leaves the process.

    ./venv/bin/python tests/test_app_activity.py

Exits non-zero on failure.

This endpoint is the store's only inbound channel from the app fleet, and three
of the things it must do are invisible when they break:

  * it must refuse everything when its secret is unset, because it ships before
    the secret is configured and an ingest route that is open by default is a
    write path into customer profiles;
  * it must not forward activity for people who are not customers — an app's
    users include colleagues the buyer invited, who never visited the store and
    never gave us an address, and _klaviyo_event upserts a profile as a side
    effect, so forwarding them silently builds a marketing list out of strangers;
  * it must never 500, because the caller is an app's login handler.

None of those raise, and none of them are visible in a health check.
"""
import os, sys, json, tempfile, sqlite3

os.environ['STORE_DB_PATH'] = tempfile.mktemp(suffix='.db')
os.environ['KLAVIYO_API_KEY'] = 'test-key-not-used'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import store_api

SECRET = 'test-activity-secret'
store_api.ACTIVITY_SECRET = SECRET

synced, events = [], []
store_api._klaviyo_sync = lambda **k: synced.append(k)
store_api._klaviyo_event = lambda metric, email, **k: events.append(
    dict(metric=metric, email=email, **k))

store_api.init_db()

from flask import Flask
app = Flask(__name__)
app.register_blueprint(store_api.store_bp)
client = app.test_client()

fails = []

# A product the store does not sell, for the validation case below.
#
# Chosen at runtime rather than hardcoded, because the hardcoded value was
# MARKUPR and this test started failing the day MARKUPR was added to PRICE_MAP.
# The fixture was silently coupled to the shape of the catalogue: making a
# product sellable broke a test that has nothing to do with that product. Every
# candidate here is a real PF9 app deliberately not sold through the store, so
# the case still reads as "a name the fleet uses but the catalogue does not".
UNSELLABLE = next(
    (p for p in ('WELLR', 'CURBKIT', 'PAPERCLIPR', 'LISTNER', 'FIELDVIEWR')
     if p not in store_api.PRICE_MAP),
    None,
)
assert UNSELLABLE, 'every candidate is now sellable — pick a new one'


def expect(label, cond, detail=''):
    print(f'  {"ok " if cond else "FAIL"}  {label}{("  <- " + str(detail)) if detail and not cond else ""}')
    if not cond:
        fails.append(label)


def post(body, secret=SECRET):
    del synced[:], events[:]
    headers = {'X-PF9-Activity-Secret': secret} if secret is not None else {}
    r = client.post('/store-api/app-activity', json=body, headers=headers)
    return r, (r.get_json() or {})


def subscribe(email, product, status='active'):
    """Put a real subscription row in, so _owned_apps sees a customer."""
    with store_api.get_db() as conn:
        conn.execute(
            'INSERT INTO subscriptions (stripe_subscription_id, email, name, product, status, created_at) '
            'VALUES (?, ?, ?, ?, ?, ?)',
            (f'sub_{email}_{product}', email, 'Test Customer', product, status, '2026-08-04T00:00:00')
        )
        conn.commit()


def rows():
    return sqlite3.connect(os.environ['STORE_DB_PATH']).execute(
        'SELECT COUNT(*) FROM app_activity').fetchone()[0]


print('=== the secret gate, which is the whole security model ===')
for label, sec in [('no header at all', None), ('empty header', ''),
                   ('wrong secret', 'nope'),
                   ('right value, wrong case', SECRET.upper())]:
    r, _ = post({'email': 'a@example.com', 'product': 'FLOWTRACK', 'kind': 'login'}, secret=sec)
    expect(f'{label:24} -> 403', r.status_code == 403, r.status_code)

# The case that matters most on the day this deploys: the env var is not set
# yet. Fail CLOSED — an unconfigured secret must disable the route, not make
# every request match it.
before = rows()
store_api.ACTIVITY_SECRET = ''
for sec in [None, '', 'anything']:
    r, _ = post({'email': 'a@example.com', 'product': 'FLOWTRACK', 'kind': 'login'}, secret=sec)
    expect(f'ACTIVITY_SECRET unset, secret={sec!r:10} -> 403', r.status_code == 403, r.status_code)
expect('and nothing was written while unconfigured', rows() == before, rows())
store_api.ACTIVITY_SECRET = SECRET

print()
print('=== validation rejects before it writes ===')
before = rows()
for label, body in [
    ('missing email',      {'product': 'FLOWTRACK', 'kind': 'login'}),
    ('not an email',       {'email': 'nope', 'product': 'FLOWTRACK', 'kind': 'login'}),
    ('missing kind',       {'email': 'a@example.com', 'product': 'FLOWTRACK'}),
    ('unknown kind',       {'email': 'a@example.com', 'product': 'FLOWTRACK', 'kind': 'deleted'}),
    ('missing product',    {'email': 'a@example.com', 'kind': 'login'}),
    ('unsellable product', {'email': 'a@example.com', 'product': UNSELLABLE, 'kind': 'login'}),
    ('path traversal',     {'email': 'a@example.com', 'product': '../etc/passwd', 'kind': 'login'}),
    ('empty body',         {}),
]:
    r, _ = post(body)
    expect(f'{label:20} -> 400', r.status_code == 400, r.status_code)
expect('no rows written by any rejected request', rows() == before, rows())

print()
print('=== a non-customer is not forwarded, and not stored either ===')
# The buyer's colleagues log in too. They are not in subscriptions, they never
# came to the store, and creating Klaviyo profiles for them would be building a
# marketing list out of people who have never heard of us.
#
# Not written to our own DB either: it would be an unbounded table of the
# addresses of people who never transacted with the store, for a population we
# have already decided we will never email.
before = rows()
r, body = post({'email': 'colleague@example.com', 'product': 'FLOWTRACK', 'kind': 'login'})
expect('200, not an error', r.status_code == 200, r.status_code)
expect('synced=False', body.get('synced') is False, body)
expect('reason names the gate', body.get('reason') == 'not a store customer', body)
expect('no profile write', synced == [], synced)
expect('no event', events == [], events)
expect('no row written', rows() == before, rows())
expect('their address is nowhere in the DB',
       sqlite3.connect(os.environ['STORE_DB_PATH']).execute(
           'SELECT COUNT(*) FROM app_activity WHERE email = ?',
           ('colleague@example.com',)).fetchone() == (0,))

# Cancelled is not a customer either — _owned_apps is ACTIVE_STATUSES, so this
# follows the same set that grants app access rather than a list restated here.
subscribe('churned@example.com', 'FLOWTRACK', status='cancelled')
r, body = post({'email': 'churned@example.com', 'product': 'FLOWTRACK', 'kind': 'login'})
expect('cancelled customer not forwarded', body.get('synced') is False, body)

print()
print('=== a real customer: first login syncs immediately ===')
subscribe('dana@example.com', 'FLOWTRACK')
r, body = post({'email': 'Dana@Example.COM ', 'product': 'flowtrack', 'kind': 'LOGIN'})
expect('200', r.status_code == 200, r.status_code)
expect('synced=True', body.get('synced') is True, body)
expect('one profile write', len(synced) == 1, synced)
expect('one event', len(events) == 1, events)
expect('metric is App Activity', events[0].get('metric') == 'App Activity', events)
expect('email normalised to lower', events[0].get('email') == 'dana@example.com', events)
props = (synced[0] if synced else {}).get('properties', {})
print('   profile props:', json.dumps(props, sort_keys=True))
expect('last_login_at set', bool(props.get('last_login_at')), props)
expect('last_active_app=FLOWTRACK', props.get('last_active_app') == 'FLOWTRACK', props)
expect('no last_action_at yet', props.get('last_action_at') is None, props)
expect('NOT activated by a mere login', props.get('activated_apps') == '', props)
expect('activated_app_count 0', props.get('activated_app_count') == 0, props)
ev = (events[0] if events else {}).get('properties', {})
expect('event login_count=1', ev.get('login_count') == 1, ev)
expect('event first_of_kind', ev.get('first_of_kind') is True, ev)

print()
print('=== the throttle, and the two firsts that are exempt from it ===')
# Every consumer of this data branches on day boundaries, so forwarding every
# login would be two API calls per page load for no gain. But the first login
# and the first key action are state changes, not samples — they are exactly
# what an activation branch reads, and delaying either by six hours would send
# a "here's how to get started" nudge to someone who already started.
r, body = post({'email': 'dana@example.com', 'product': 'FLOWTRACK', 'kind': 'login'})
expect('2nd login is throttled', body.get('synced') is False, body)
expect('throttled means no calls at all', synced == [] and events == [], (synced, events))
expect('reason=throttled', body.get('reason') == 'throttled', body)

r, body = post({'email': 'dana@example.com', 'product': 'FLOWTRACK',
                'kind': 'action', 'action': 'scan'})
expect('FIRST action bypasses the throttle', body.get('synced') is True, body)
props = (synced[0] if synced else {}).get('properties', {})
expect('now activated', props.get('activated_apps') == 'FLOWTRACK', props)
expect('activated_app_count 1', props.get('activated_app_count') == 1, props)
expect('last_action recorded', props.get('last_action') == 'scan', props)

r, body = post({'email': 'dana@example.com', 'product': 'FLOWTRACK',
                'kind': 'action', 'action': 'scan'})
expect('2nd action is throttled', body.get('synced') is False, body)

# An action ping with no name must not blank the name we already have — the
# field exists so a human reading the profile can tell what the customer did.
post({'email': 'dana@example.com', 'product': 'FLOWTRACK', 'kind': 'action'})
kept = sqlite3.connect(os.environ['STORE_DB_PATH']).execute(
    'SELECT last_action, action_count FROM app_activity WHERE email=? AND product=?',
    ('dana@example.com', 'FLOWTRACK')).fetchone()
expect('unnamed action keeps the last name', kept[0] == 'scan', kept)
expect('...and still counts', kept[1] == 3, kept)

print()
print('=== no per-person boolean can claim a per-app fact ===')
# This is the bug the personalisation work found the hard way: profile
# properties persist, so a per-app truth written under a per-person name becomes
# a lie the moment the customer opens a second app. A `has_activated` boolean
# would say a FLOWTRACK-activated customer is activated in SUPPORTR too, and
# suppress the SUPPORTR nudge for the one person who most needs it.
subscribe('dana@example.com', 'SUPPORTR')
r, body = post({'email': 'dana@example.com', 'product': 'SUPPORTR', 'kind': 'login'})
props = (synced[0] if synced else {}).get('properties', {})
print('   profile props:', json.dumps(props, sort_keys=True))
expect('synced (first login for this app)', body.get('synced') is True, body)
expect('no has_activated boolean exists at all', 'has_activated' not in props, props)
expect('activated_apps still names only FLOWTRACK',
       props.get('activated_apps') == 'FLOWTRACK', props)
expect('last_active_app moved to SUPPORTR', props.get('last_active_app') == 'SUPPORTR', props)
expect('two rows for this customer',
       sqlite3.connect(os.environ['STORE_DB_PATH']).execute(
           'SELECT COUNT(*) FROM app_activity WHERE email=?', ('dana@example.com',)
       ).fetchone() == (2,))

r, body = post({'email': 'dana@example.com', 'product': 'SUPPORTR',
                'kind': 'action', 'action': 'resolve ticket'})
props = (synced[0] if synced else {}).get('properties', {})
expect('now activated in both, listed separately',
       props.get('activated_apps') == 'FLOWTRACK, SUPPORTR', props)
expect('activated_app_count 2', props.get('activated_app_count') == 2, props)

print()
print('=== every property Klaviyo receives is a type it can filter on ===')
for k, v in sorted(props.items()):
    expect(f'{k:20} is str/int/None', v is None or isinstance(v, (str, int)), repr(v))

print()
print('=== a Klaviyo outage must never break an app login ===')
# The caller is a login handler. A client written the obvious way — post, then
# check the status — would turn a telemetry failure into customers unable to
# sign in, so the one thing this route may never do is 500.
def boom(*a, **k):
    raise RuntimeError('Klaviyo down')
store_api._klaviyo_sync = boom
before = rows()
r, body = post({'email': 'dana@example.com', 'product': 'FLOWTRACK', 'kind': 'action', 'action': 'scan'})
expect('still 200', r.status_code == 200, r.status_code)
expect('ok true', body.get('ok') is True, body)
expect('honest about not syncing', body.get('synced') is False, body)
# And the throttle must NOT have started, or one outage suppresses six hours of
# retries over a failure we never confirmed.
stamp = sqlite3.connect(os.environ['STORE_DB_PATH']).execute(
    'SELECT last_synced_at FROM app_activity WHERE email=? AND product=?',
    ('dana@example.com', 'FLOWTRACK')).fetchone()[0]
r2, body2 = post({'email': 'dana@example.com', 'product': 'FLOWTRACK', 'kind': 'login'})
stamp2 = sqlite3.connect(os.environ['STORE_DB_PATH']).execute(
    'SELECT last_synced_at FROM app_activity WHERE email=? AND product=?',
    ('dana@example.com', 'FLOWTRACK')).fetchone()[0]
expect('failed sync did not start the throttle clock', stamp == stamp2, (stamp, stamp2))
store_api._klaviyo_sync = lambda **k: synced.append(k)

print()
print('=== the row is a fixed-size summary, not a log that grows forever ===')
before = rows()
for _ in range(25):
    post({'email': 'dana@example.com', 'product': 'FLOWTRACK', 'kind': 'login'})
expect('25 more pings added 0 rows', rows() == before, rows())
count = sqlite3.connect(os.environ['STORE_DB_PATH']).execute(
    'SELECT login_count FROM app_activity WHERE email=? AND product=?',
    ('dana@example.com', 'FLOWTRACK')).fetchone()[0]
expect('...but every one of them was counted', count >= 25, count)

print()
print('=== the endpoint is server-to-server, so it emits no CORS headers ===')
# A browser that can reach this is a browser with the secret in its devtools.
# The store's CORS policy allows only Content-Type, so the header could not be
# sent cross-origin anyway — leaving the headers off makes that deliberate.
r, _ = post({'email': 'dana@example.com', 'product': 'FLOWTRACK', 'kind': 'login'})
expect('no Access-Control-Allow-Origin',
       'Access-Control-Allow-Origin' not in r.headers, dict(r.headers))

os.unlink(os.environ['STORE_DB_PATH'])
print()
if fails:
    print('FAILURES:')
    for f in fails:
        print('  -', f)
    sys.exit(1)
print('all app-activity checks passed')
