"""Check the subscription lifecycle relay to tiered apps (#513).

    ./venv/bin/python tests/test_plan_relay.py

Exits non-zero on failure. Offline — the one network call (_notify_app_plan_change)
is exercised against a fake http_requests so nothing leaves the box.

The store owns the Stripe subscription (the app holds no Stripe key), so when a
subscription is cancelled / renewed / changes rung, the store has to PUSH that to
a tiered app or the app keeps granting caps a lapsed customer no longer pays for.
This checks the two things that make that push land on the right door with the
right words: the URL derivation, and the payload/secret of the POST itself.
"""
import os, sys

os.environ.setdefault('KLAVIYO_API_KEY', '')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import store_api
from store_api import (_plan_relay_url, _notify_app_plan_change,
                       PLAN_RELAY_PRODUCTS, REGISTER_PATH, APP_URL_MAP)

fails = []


def expect(label, ok, detail=''):
    if not ok:
        fails.append(f'{label}{": " + detail if detail else ""}')
    print(f'  {"ok " if ok else "FAIL"}  {label}{"" if ok else "  <- " + detail}')


class _FakeResp:
    def __init__(self, status_code, text=''):
        self.status_code = status_code
        self.text = text


class _Boom:
    def post(self, *a, **k):
        raise RuntimeError('network down')


class _Recorder:
    """Stand-in for http_requests: records the one POST and returns a canned resp."""
    def __init__(self, status_code=200):
        self.status_code = status_code
        self.calls = []

    def post(self, url, json=None, headers=None, timeout=None):
        self.calls.append({'url': url, 'json': json, 'headers': headers})
        return _FakeResp(self.status_code)


print('=== every store product exposes a relay URL, and it mirrors /register ===')
# Since 2026-11-14 every store app locks a lapsed customer (#1040), so every
# product gets lifecycle pushes. Deriving /plan from /register keeps it behind
# the same PROVISION_SECRET and impossible to point at a stray host.
expect('every provisioned product is relayed', PLAN_RELAY_PRODUCTS == set(REGISTER_PATH),
       repr(set(REGISTER_PATH) - PLAN_RELAY_PRODUCTS))
expect('COMPLI keeps its versioned path', _plan_relay_url('COMPLI', ).endswith('/api/v1/auth/plan'),
       repr(_plan_relay_url('COMPLI')))
expect('MARKUPR keeps its short path', _plan_relay_url('MARKUPR').endswith('/api/plan'),
       repr(_plan_relay_url('MARKUPR')))
for product in sorted(PLAN_RELAY_PRODUCTS):
    url = _plan_relay_url(product)
    expect(f'{product} has a relay url', bool(url), repr(url))
    expect(f'{product} relay url ends in /plan',
           bool(url) and url.endswith('/plan'), repr(url))
    reg = APP_URL_MAP[product].rstrip('/') + REGISTER_PATH[product]
    expect(f'{product} relay url is its register url with /register->/plan',
           url == reg[:-len('/register')] + '/plan', repr(url))

print()
print('=== an unknown product gets no relay url (push is a no-op for it) ===')
for product in ['', None, 'NOPE', 'SHOWJUDGR (waitlist)']:
    expect(f'{str(product):<10} -> None', _plan_relay_url(product) is None,
           repr(_plan_relay_url(product)))

print()
print('=== a cancel push POSTs the handle+status with the provisioning secret ===')
orig_req, orig_secret = store_api.http_requests, store_api.PROVISION_SECRET
try:
    rec = _Recorder(200)
    store_api.http_requests = rec
    store_api.PROVISION_SECRET = 'sekret'
    _notify_app_plan_change('SHOWJUDGR', 'sub_abc', 'canceled')
    expect('exactly one POST was made', len(rec.calls) == 1, str(len(rec.calls)))
    call = rec.calls[0] if rec.calls else {'url': '', 'json': {}, 'headers': {}}
    expect('POST hits the /plan endpoint', call['url'].endswith('/api/auth/plan'),
           call['url'])
    expect('payload carries the subscription handle',
           call['json'].get('stripeSubscriptionId') == 'sub_abc', repr(call['json']))
    expect('payload carries the status',
           call['json'].get('status') == 'canceled', repr(call['json']))
    expect('a status-only push sends no plan key',
           'plan' not in call['json'], repr(call['json']))
    expect('the provisioning secret rides the header',
           call['headers'].get('X-PF9-Provision-Secret') == 'sekret',
           repr(call['headers']))

    print()
    print('=== a rung change carries the new plan code ===')
    rec2 = _Recorder(200)
    store_api.http_requests = rec2
    _notify_app_plan_change('SHOWJUDGR', 'sub_abc', 'active', plan='annual')
    c2 = rec2.calls[0] if rec2.calls else {'json': {}}
    expect('plan code is forwarded on a rung change',
           c2['json'].get('plan') == 'annual', repr(c2['json']))

    print()
    print('=== an unknown product never touches the network ===')
    rec3 = _Recorder(200)
    store_api.http_requests = rec3
    _notify_app_plan_change('NOPE', 'sub_abc', 'canceled')
    expect('no POST for an unknown product', rec3.calls == [], str(rec3.calls))

    print()
    print('=== #1040: the push carries the customer email so the app can find them ===')
    rec6 = _Recorder(200)
    store_api.http_requests = rec6
    _notify_app_plan_change('FLOWTRACK', 'sub_abc', 'canceled', email='buyer@example.com')
    c6 = rec6.calls[0] if rec6.calls else {'url': '', 'json': {}}
    expect('FLOWTRACK cancel reaches its /api/auth/plan', c6['url'].endswith('/api/auth/plan'), c6['url'])
    expect('payload carries the email', c6['json'].get('email') == 'buyer@example.com', repr(c6['json']))
    expect('payload carries the product', c6['json'].get('product') == 'FLOWTRACK', repr(c6['json']))

    print()
    print('=== #1040: a switch-off that does not land alerts a human; unlocks only log ===')
    alerts = []
    orig_alert_send = store_api._send_email
    store_api._send_email = lambda *a, **k: alerts.append(a)
    try:
        for code, status, product, want in [(500, 'canceled', 'TASKFLOW', 1), (500, 'unpaid', 'TASKFLOW', 1),
                                            (404, 'canceled', 'COMPLI', 1), (404, 'canceled', 'SHOWJUDGR', 0),
                                            (500, 'active', 'TASKFLOW', 0), (500, 'past_due', 'TASKFLOW', 0),
                                            (200, 'canceled', 'TASKFLOW', 0)]:
            alerts.clear()
            store_api.http_requests = _Recorder(code)
            _notify_app_plan_change(product, 'sub_x', status, email='buyer@example.com')
            expect(f'{product} {status} HTTP {code} -> {want} alert(s)', len(alerts) == want, str(len(alerts)))
    finally:
        store_api._send_email = orig_alert_send

    print()
    print('=== a 404 (no org for that handle) is swallowed, not raised ===')
    rec4 = _Recorder(404)
    store_api.http_requests = rec4
    try:
        _notify_app_plan_change('SHOWJUDGR', 'sub_missing', 'canceled')
        raised = False
    except Exception:
        raised = True
    expect('404 does not raise', not raised)

    print()
    print('=== a transport error never breaks the caller ===')
    store_api.http_requests = _Boom()
    try:
        _notify_app_plan_change('SHOWJUDGR', 'sub_abc', 'canceled')
        raised = False
    except Exception:
        raised = True
    expect('a raised POST is caught inside the helper', not raised)

    print()
    print('=== a missing handle or status is a no-op (nothing to sync) ===')
    rec5 = _Recorder(200)
    store_api.http_requests = rec5
    _notify_app_plan_change('SHOWJUDGR', '', 'canceled')
    _notify_app_plan_change('SHOWJUDGR', 'sub_abc', '')
    expect('no POST when the handle or status is blank', rec5.calls == [],
           str(rec5.calls))
finally:
    store_api.http_requests, store_api.PROVISION_SECRET = orig_req, orig_secret

print()
if fails:
    print('FAILURES:')
    for f in fails:
        print('  -', f)
    sys.exit(1)
print('all plan-relay checks passed')
