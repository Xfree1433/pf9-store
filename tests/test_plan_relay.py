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


class _Recorder:
    """Stand-in for http_requests: records the one POST and returns a canned resp."""
    def __init__(self, status_code=200):
        self.status_code = status_code
        self.calls = []

    def post(self, url, json=None, headers=None, timeout=None):
        self.calls.append({'url': url, 'json': json, 'headers': headers})
        return _FakeResp(self.status_code)


print('=== only tiered products expose a relay URL, and it mirrors /register ===')
# SHOWJUDGR is the only app enforcing per-tier limits today, so it is the only
# one that should receive lifecycle pushes. Deriving /plan from /register keeps
# it behind the same PROVISION_SECRET and impossible to point at a stray host.
for product in sorted(PLAN_RELAY_PRODUCTS):
    url = _plan_relay_url(product)
    expect(f'{product} has a relay url', bool(url), repr(url))
    expect(f'{product} relay url ends in /plan',
           bool(url) and url.endswith('/plan'), repr(url))
    reg = APP_URL_MAP[product].rstrip('/') + REGISTER_PATH[product]
    expect(f'{product} relay url is its register url with /register->/plan',
           url == reg[:-len('/register')] + '/plan', repr(url))

print()
print('=== an untiered product gets no relay url (push is a no-op for it) ===')
for product in ['FLOWTRACK', 'COMPLI', 'MARKUPR', '', None, 'NOPE']:
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
    print('=== an untiered product never touches the network ===')
    rec3 = _Recorder(200)
    store_api.http_requests = rec3
    _notify_app_plan_change('FLOWTRACK', 'sub_abc', 'canceled')
    expect('no POST for an untiered product', rec3.calls == [], str(rec3.calls))

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
    class _Boom:
        def post(self, *a, **k):
            raise RuntimeError('network down')
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
