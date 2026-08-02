"""Create the three PF9 metrics by firing one event each through the DEPLOYED
_klaviyo_event. Metrics in Klaviyo are created by their first event and CANNOT
be deleted, so this uses the real emitter rather than a hand-rolled POST: the
metric names and payload shape come from the code that will emit them in
production, not from a transcription of it.

Properties mirror the real call sites so Klaviyo's flow editor learns the
property names now, while building L2/L6/L7 later.

Dry run by default. Pass 'fire' to actually send.
"""
import os
import sys
import tempfile

FIRE = len(sys.argv) > 1 and sys.argv[1] == 'fire'

# Pull the key out of the env file without echoing it anywhere.
# Both files are consulted, override last, mirroring what the service sees.
# In practice only the override defines it (verified 2026-08-02).
key = ''
for path in ('/opt/bridgr/.env', '/opt/pf9-store/pf9-store-api.env'):
    try:
        fh = open(path)
    except OSError:
        continue
    with fh:
        for line in fh:
            line = line.strip()
            if line.startswith('KLAVIYO_API_KEY='):
                key = line.split('=', 1)[1].strip().strip('"').strip("'")
if not key:
    sys.exit('KLAVIYO_API_KEY not found in either env file')
os.environ['KLAVIYO_API_KEY'] = key

# Never touch the production DB; import must not resolve to it.
os.environ['STORE_DB_PATH'] = tempfile.mktemp(suffix='.db')

sys.path.insert(0, '/opt/pf9-store')
import store_api

print(f'key loaded: {len(key)} chars, prefix {key[:6]}...')
print(f'store_api.KLAVIYO_API_KEY populated: {bool(store_api.KLAVIYO_API_KEY)}')
print(f'STORE_URL: {store_api.STORE_URL}')

# Must be a domain we own. Klaviyo returns 202 for events on RFC-2606 reserved
# domains (example.com) and then silently discards them — no metric is created
# and nothing surfaces in the API. Verified 2026-08-02.
EMAIL = 'metric-bootstrap@plainspokenfoundrynine.com'
STAMP = 'metric-bootstrap-20260802'

EVENTS = [
    dict(
        metric='Started Checkout',
        email=EMAIL, name='Metric Bootstrap',
        unique_id=f'{STAMP}-started-checkout',
        properties={
            'app_name': 'FLOWTRACK',
            'product': 'FLOWTRACK',
            'company': 'PF9 Internal Test',
            'resume_link': 'https://checkout.stripe.com/c/pay/test-bootstrap',
            'restart_link': f'{store_api.STORE_URL}/?product=FLOWTRACK',
        },
    ),
    dict(
        metric='Placed Order',
        email=EMAIL, name='Metric Bootstrap',
        unique_id=f'{STAMP}-placed-order',
        value=49.0,
        properties={
            'app_name': 'FLOWTRACK',
            'product': 'FLOWTRACK',
            'company': 'PF9 Internal Test',
        },
    ),
    dict(
        metric='Cancelled Subscription',
        email=EMAIL, name='Metric Bootstrap',
        unique_id=f'{STAMP}-cancelled-subscription',
        properties={
            'app_name': 'FLOWTRACK',
            'product': 'FLOWTRACK',
            'remaining_app_count': 0,
            'reactivate_link': f'{store_api.STORE_URL}/?product=FLOWTRACK',
        },
    ),
]

for ev in EVENTS:
    print(f"\n{'FIRE' if FIRE else 'DRY '}  {ev['metric']}")
    print(f"      unique_id={ev['unique_id']}")
    print(f"      props={sorted(ev['properties'])}")
    if 'value' in ev:
        print(f"      value={ev['value']}")
    if FIRE:
        # _klaviyo_event is fail-soft and returns None either way, so "it ran"
        # is not "it worked" — that conflation is precisely what hid the missing
        # events:write scope for as long as it was hidden. Confirm against the
        # metrics list afterwards rather than trusting this loop.
        store_api._klaviyo_event(**ev)
        print('      called (check stderr above for a 4xx; see verification below)')

if FIRE:
    print('\nCalled all three. This does NOT mean they landed.')
    print('Verify — the metric list is the only real proof:')
    print('  Klaviyo MCP get_metrics, or:')
    print("  curl -s -H \"Authorization: Klaviyo-API-Key $KEY\" -H 'revision: 2024-10-15' \\")
    print("    'https://a.klaviyo.com/api/metrics/' | grep -o '\"name\":\"[^\"]*\"'")
    print('Expect Started Checkout, Placed Order, Cancelled Subscription.')
    print('Two failure modes have actually happened, both silent:')
    print('  1. key lacks events:write -> 403, swallowed by the fail-soft emitter')
    print('  2. profile email on a reserved domain -> 202 accepted, then discarded')
    print('Both leave the metric list unchanged, which is why it is the only proof.')
else:
    print('\nDRY RUN — nothing sent. Re-run with: fire')
