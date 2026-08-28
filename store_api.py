"""
Plainspoken Foundry Nine - Store API
Handles:
- Demo request form submissions (saves to DB + sends email)
- Stripe subscription checkout + webhooks + account provisioning
- CORS enabled for store.plainspokenfoundrynine.com

TWO COPIES OF THIS FILE RUN ON xfree143. Both are live; neither is stale.

    /opt/pf9-store/store_api.py   <- this repo, deployed here.
                                     Served by pf9-store-api.service on :5011.
                                     nginx routes /store-api here.

    /opt/bridgr/store_api.py      <- NOT a leftover. bridgr's src/web/app.py
                                     imports it at line 76:
                                         from store_api import store_bp, ...
                                     That is a bare module-level import, not
                                     inside a try/except, so DELETING THAT FILE
                                     STOPS bridgr FROM STARTING. The running
                                     process holds the module in memory, so the
                                     breakage would not appear until some later,
                                     unrelated restart.

The bridgr copy is pinned at commit 851221b (2026-03-17) and does not receive
changes made here -- it predates the trials/app_count work entirely. It answers
/store-api/* on :5010, which nginx does not route to, but it does read
STRIPE_SECRET_KEY from the shared /opt/bridgr/.env. A Stripe key rotation
therefore leaves a stale key resident in the bridgr process until bridgr is
restarted, which is its own decision: xfree143's bridgr is legacy and flagged
read-only.

Do not "clean up" the bridgr copy without first changing that import.
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import sqlite3
import os
import string
import secrets
import time
import html
import re
from urllib.parse import urlparse
import requests as http_requests

try:
    import stripe
    stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', '')
except ImportError:
    stripe = None
    print('[Store API] WARNING: stripe package not installed')

try:
    import resend
    resend.api_key = os.environ.get('RESEND_API_KEY', '')
except ImportError:
    resend = None
    print('[Store API] WARNING: resend package not installed')

store_bp = Blueprint('store', __name__, url_prefix='/store-api')

DB_PATH = os.environ.get('STORE_DB_PATH', '/opt/pf9-store/store_leads.db')
STORE_URL = 'https://store.plainspokenfoundrynine.com'

# ── Email config (Resend) ──
EMAIL_FROM_CUSTOMER = os.environ.get('EMAIL_FROM_CUSTOMER', 'PF9 <welcome@plainspokenfoundrynine.com>')
EMAIL_FROM_INTERNAL = os.environ.get('EMAIL_FROM_INTERNAL', 'PF9 Alerts <alerts@plainspokenfoundrynine.com>')
NOTIFY_EMAIL        = os.environ.get('NOTIFY_EMAIL', '')

# Shared secret presented to an app's registration endpoint to prove this is the
# store fulfilling a paid subscription, for apps that keep public signup closed.
# Unset means the header is simply not sent.
PROVISION_SECRET    = os.environ.get('PROVISION_SECRET', '')

# Shared secret an APP presents to /store-api/app-activity — the reverse of
# PROVISION_SECRET, which the store presents to an app. Deliberately a separate
# value: provisioning creates accounts, so its secret is far more dangerous, and
# handing the same string to fourteen apps for a low-stakes ping would widen that
# blast radius for nothing.
#
# Unset disables the endpoint entirely (403), which is the safe default while
# no app is calling it yet — an ingest route that accepts anything because its
# secret was never configured is worse than one that is simply off.
ACTIVITY_SECRET     = os.environ.get('ACTIVITY_SECRET', '')

# How stale a profile's activity may get before the next ping is forwarded to
# Klaviyo. Six hours, because every consumer of this data branches on day
# boundaries ("has not logged in for 14 days", "did the key action during the
# trial"), so finer resolution buys nothing and costs two API calls per ping on
# an endpoint that a busy customer hits dozens of times a day.
#
# Firsts are exempt — see _record_app_activity. The first login and the first
# real action are state changes, not samples, and they are the two moments an
# activation sequence actually branches on.
ACTIVITY_SYNC_INTERVAL = int(os.environ.get('ACTIVITY_SYNC_INTERVAL_SECONDS', '21600'))


# ── HubSpot CRM config ──
HUBSPOT_TOKEN              = os.environ.get('HUBSPOT_TOKEN', '')
HUBSPOT_API_BASE           = 'https://api.hubapi.com'
HUBSPOT_LIST_MANUFACTURING = int(os.environ.get('HUBSPOT_LIST_MANUFACTURING', '12'))
HUBSPOT_LIST_PROPERTY      = int(os.environ.get('HUBSPOT_LIST_PROPERTY', '13'))
HUBSPOT_LIST_SUBSCRIBERS   = int(os.environ.get('HUBSPOT_LIST_SUBSCRIBERS', '14'))

# FIELDVIEWR and MARKUPR are here for CRM segmentation only. FIELDVIEWR is
# industrial/field operations and belongs on the manufacturing list rather than
# in neither; MARKUPR follows its own storefront card, which is
# data-category="property operations", so the two agree instead of the CRM
# quietly disagreeing with the shop page. Neither is part of the $225
# Manufacturing Suite or the $89 Property Suite — this set is read solely by
# the two HubSpot/Klaviyo list routers below and carries no pricing.
#
# Note the matching is `app in p`, a SUBSTRING test, so a new key must not be a
# substring of an unrelated product name. MARKUPR is not.
_MANUFACTURING_APPS = {'FLOWTRACK', 'QUALIFI', 'SHIFTLOG', 'REPORTR', 'INSPECTR', 'MAINTAINR', 'FIELDVIEWR'}
_PROPERTY_APPS      = {'LANDLORDR', 'TENANTLINK', 'TENANTLINKR', 'PROPERTY_BUNDLE', 'PERMITR', 'TASKFLOW', 'MARKUPR'}


# ── Klaviyo lifecycle-email config ──
# Drives the trial/paid onboarding flows — marketing only, as of 2026-08-04.
# The day-27 pre-charge notice moved back into _handle_trial_will_end: it is a
# billing notice, and routing it through Klaviyo made it consent-gated, so
# anyone who declined the checkout tick would have been charged unwarned.
# Klaviyo message ReYNde must stay OFF to avoid double-sending it.
KLAVIYO_API_KEY    = os.environ.get('KLAVIYO_API_KEY', '')
KLAVIYO_API_BASE   = 'https://a.klaviyo.com/api'
KLAVIYO_REVISION   = os.environ.get('KLAVIYO_REVISION', '2024-10-15')
KLAVIYO_LIST_TRIAL = os.environ.get('KLAVIYO_LIST_TRIAL', 'RKeAnZ')
KLAVIYO_LIST_PAID  = os.environ.get('KLAVIYO_LIST_PAID', 'SfBnvH')

# The list the checkout consent tick subscribes to. Intentionally NOT one of the
# two above: both are "Added to List" triggers for live onboarding flows, so
# subscribing to either at checkout start would begin trial onboarding for
# someone who has not paid and may never. This one must be single opt-in with no
# flow triggers hanging off it. Unset = consent is never granted; see
# _klaviyo_subscribe.
#
# W7gYXU is "Marketing Consent — Storefront", created 2026-08-03 for exactly this
# and nothing else. If you ever repoint this, check the replacement's
# opt_in_process is single_opt_in first: the ACCOUNT default is double opt-in, so
# a list created without specifying it inherits double and consent silently
# becomes pending-confirmation instead of granted.
KLAVIYO_LIST_CONSENT = os.environ.get('KLAVIYO_LIST_CONSENT', 'W7gYXU')


# /demo-request is not one form. Eight pages post to it (grepped 2026-08-04),
# and the only thing distinguishing their intents is a convention in the
# `product` string:
#
#   'SHIFTLOG' and other bare keys           contact.html — someone asking us a question
#   'SHOWJUDGR (waitlist)'                   index.html — pre-launch signup. The
#                                            live example as of 2026-08-28; older
#                                            rows carry 'FIELDVIEWR (waitlist)'
#                                            and 'MARKUPR (waitlist)' from before
#                                            those two went on sale
#   'PROPERTY_SUITE (calculator lead)'       tools/*-calculator.html — wants a PDF
#   'PROPERTY_LEAD_MAGNET (…)'               lead-magnets/*.html — wants a template
#   'AFFILIATE_PROGRAM_SIGNUP'               refer/ — wants to resell
#   'STOREFRONT (email capture)'             a modal since removed from index.html;
#                                            kept because rows carrying it still exist
#
# Those intents are not interchangeable, and two of them carry an explicit
# promise ("PDF on its way within one business day", "we'll email you at
# launch") that nothing automated currently keeps. Collapsing them into one
# undifferentiated "lead" is what makes that invisible, so the type is derived
# here and sent as a property a Klaviyo flow can branch on.
_LEAD_TYPE_MARKERS = [
    ('(waitlist)',           'waitlist'),
    ('(calculator lead)',    'calculator'),
    ('_LEAD_MAGNET',         'lead_magnet'),
    ('AFFILIATE_PROGRAM',    'affiliate'),
    ('(email capture)',      'email_capture'),
]


def _lead_type_for(product):
    """Classify a /demo-request submission by the surface it came from.

    Falls back to 'question' rather than 'unknown': contact.html sends a bare
    product name with no marker, and it is the surface where a human actually
    typed something. A new caller that forgets the convention lands there too,
    which errs toward "a person is waiting on a reply" — the safe direction.
    """
    p = (product or '').upper()
    for marker, lead_type in _LEAD_TYPE_MARKERS:
        if marker.upper() in p:
            return lead_type
    return 'question'


def _lead_vertical_for(product):
    """The vertical, by the same rule that picks the HubSpot list.

    Deliberately shares _hubspot_list_for_product's matching so a lead cannot be
    filed under Property in HubSpot and Manufacturing in Klaviyo.
    """
    p = (product or '').upper()
    if 'MANUFACTURING' in p or any(app in p for app in _MANUFACTURING_APPS):
        return 'manufacturing'
    if 'PROPERTY' in p or any(app in p for app in _PROPERTY_APPS):
        return 'property'
    return None


# The three lead-magnet pages promise, verbatim (lead-magnets/*.html:57):
# "we'll show you the template right after and email it so you can find it
# later." The page keeps the first half — it reveals the template inline on
# success — and nothing has ever kept the second.
#
# This one is worth keeping precisely because, unlike the calculator's PDF, the
# deliverable is not a document a human has to make. It is a URL that already
# exists and already serves 200 (checked 2026-08-04), so an email carrying the
# link keeps the promise exactly as written.
#
# Keyed on the product tag, and deliberately NOT derived from the Referer path
# by string substitution. The tag is still client-supplied, but here it can only
# ever select a row from this fixed table: an unrecognised tag yields no
# property at all. Nothing that is not written below can become a link we put
# in an email.
_LEAD_MAGNET_ASSETS = {
    'MANUFACTURING_LEAD_MAGNET (NCR-CAPA Log)': (
        'NCR / CAPA Log Template',
        'https://store.plainspokenfoundrynine.com/templates/ncr-capa-log-template.html',
    ),
    'MANUFACTURING_LEAD_MAGNET (Shift Handoff)': (
        'Shift Handoff Template',
        'https://store.plainspokenfoundrynine.com/templates/shift-handoff-template.html',
    ),
    'PROPERTY_LEAD_MAGNET (Inspection Checklist)': (
        'Property Inspection Checklist',
        'https://store.plainspokenfoundrynine.com/templates/property-inspection-checklist.html',
    ),
}

# 'Per-door calculator PDF request at 250 units.' / '... at 40 users.'
# Both strings are composed by our own JS from the slider position
# (tools/per-door-calculator.html:364, tools/per-user-calculator.html:367).
_CALCULATOR_SIZE_RE = re.compile(r'\bat\s+(\d{1,7})\s+(units|users)\b', re.IGNORECASE)


def _calculator_size_from(message):
    """The one number that makes a calculator lead worth anything.

    The message body is otherwise never forwarded to Klaviyo, and that rule
    still holds: what comes back here is an int and a noun from a closed set,
    not the visitor's prose. On this surface the message is not free text at
    all — the page builds the sentence and the only variable in it is the unit
    count the visitor dialled in, which is the entire substance of the request.

    Bounded at seven digits so an absurd payload cannot put an unbounded string
    on a third-party profile. Returns (count, noun) or (None, None).
    """
    m = _CALCULATOR_SIZE_RE.search(message or '')
    if not m:
        return None, None
    try:
        return int(m.group(1)), m.group(2).lower()
    except (TypeError, ValueError):
        return None, None


def _hubspot_list_for_product(product):
    """Map a product key (or calculator-lead tag) to a HubSpot list ID. None if ambiguous."""
    p = (product or '').upper()
    if 'MANUFACTURING' in p or any(app in p for app in _MANUFACTURING_APPS):
        return HUBSPOT_LIST_MANUFACTURING
    if 'PROPERTY' in p or any(app in p for app in _PROPERTY_APPS):
        return HUBSPOT_LIST_PROPERTY
    return None


def _hubspot_push_contact(email, name='', company='', list_id=None):
    """
    Upsert a contact in HubSpot and optionally add to a static list.
    Fail-soft: never raises. Logs errors and returns. Callers must
    not block on this — CRM availability is not a precondition for
    serving the request.
    """
    if not HUBSPOT_TOKEN or not email:
        return

    email_norm = email.lower().strip()
    headers = {
        'Authorization': f'Bearer {HUBSPOT_TOKEN}',
        'Content-Type': 'application/json',
    }

    parts = (name or '').strip().split(None, 1)
    properties = {'email': email_norm}
    if parts:
        properties['firstname'] = parts[0]
    if len(parts) > 1:
        properties['lastname'] = parts[1]
    if company:
        properties['company'] = company

    contact_id = None
    try:
        r = http_requests.post(
            f'{HUBSPOT_API_BASE}/crm/v3/objects/contacts',
            json={'properties': properties},
            headers=headers,
            timeout=10,
        )
        if r.status_code == 201:
            contact_id = r.json().get('id')
        elif r.status_code == 409:
            r2 = http_requests.patch(
                f'{HUBSPOT_API_BASE}/crm/v3/objects/contacts/{email_norm}?idProperty=email',
                json={'properties': properties},
                headers=headers,
                timeout=10,
            )
            if r2.status_code == 200:
                contact_id = r2.json().get('id')
            else:
                print(f'[Store API] HubSpot patch failed for {email_norm}: {r2.status_code} {r2.text[:200]}')
        else:
            print(f'[Store API] HubSpot create failed for {email_norm}: {r.status_code} {r.text[:200]}')
    except Exception as e:
        print(f'[Store API] HubSpot upsert error for {email_norm}: {e}')
        return

    if contact_id and list_id:
        try:
            r = http_requests.put(
                f'{HUBSPOT_API_BASE}/crm/v3/lists/{list_id}/memberships/add',
                json=[contact_id],
                headers=headers,
                timeout=10,
            )
            if r.status_code not in (200, 201, 204):
                print(f'[Store API] HubSpot list add failed for {email_norm} (list {list_id}): {r.status_code} {r.text[:200]}')
        except Exception as e:
            print(f'[Store API] HubSpot list add error for {email_norm}: {e}')


def _klaviyo_headers():
    return {
        'Authorization': f'Klaviyo-API-Key {KLAVIYO_API_KEY}',
        'revision': KLAVIYO_REVISION,
        'Content-Type': 'application/json',
        'accept': 'application/json',
    }


def _format_trial_end(trial_end_iso):
    """Render the billing date as the customer reads it: 'August 30, 2026'.

    Shared: it feeds both the Klaviyo `trial_end_date` profile property and the
    store's own day-27 pre-charge email, so the two can never disagree about
    the date. (Named _klaviyo_format_trial_end until the day-27 send moved back
    in-house on 2026-08-04.)
    """
    if not trial_end_iso:
        return None
    try:
        return datetime.fromisoformat(trial_end_iso).strftime('%B %-d, %Y')
    except Exception:
        return None


def _trial_price_display(sub):
    """Dollars the customer will actually be charged, as a bare string: '49', '49.50'.

    Read off the subscription's own line item rather than any stored or
    hardcoded figure, so the pre-charge email cannot quote a price that differs
    from the invoice. Returns None if the shape isn't what we expect — callers
    must handle that rather than printing 'None' at the customer.
    """
    try:
        items = ((sub.get('items') or {}).get('data')) or []
        if not items:
            return None
        unit_amount = ((items[0].get('price') or {}).get('unit_amount'))
        if unit_amount is None:
            return None
        dollars = unit_amount / 100
        return f'{dollars:.0f}' if dollars == int(dollars) else f'{dollars:.2f}'
    except Exception:
        return None


def _klaviyo_sync(email, name='', properties=None, add_list=None, remove_list=None):
    """
    Upsert a Klaviyo profile and move it between lifecycle lists.

    Fail-soft like _hubspot_push_contact: never raises, never blocks the webhook.
    Since 2026-08-04 this carries marketing onboarding only — the day-27 billing
    notice is sent directly by _handle_trial_will_end — so a failure here costs
    onboarding email, not a billing warning.
    """
    if not KLAVIYO_API_KEY or not email:
        return

    email_norm = email.lower().strip()
    attributes = {'email': email_norm}
    parts = (name or '').strip().split(None, 1)
    if parts:
        attributes['first_name'] = parts[0]
    if len(parts) > 1:
        attributes['last_name'] = parts[1]
    if properties:
        attributes['properties'] = {k: v for k, v in properties.items() if v is not None}

    profile_id = None
    try:
        r = http_requests.post(
            f'{KLAVIYO_API_BASE}/profile-import/',
            json={'data': {'type': 'profile', 'attributes': attributes}},
            headers=_klaviyo_headers(),
            timeout=10,
        )
        if r.status_code in (200, 201):
            profile_id = ((r.json() or {}).get('data') or {}).get('id')
        else:
            print(f'[Store API] Klaviyo profile upsert failed for {email_norm}: {r.status_code} {r.text[:200]}')
            return
    except Exception as e:
        print(f'[Store API] Klaviyo profile upsert error for {email_norm}: {e}')
        return

    if not profile_id:
        print(f'[Store API] Klaviyo returned no profile id for {email_norm}')
        return

    payload = {'data': [{'type': 'profile', 'id': profile_id}]}
    # remove_list takes either one list id or several. A cancellation that ends
    # the customer's last subscription has to come off both lifecycle lists, and
    # accepting a sequence here does that without a second profile upsert.
    removals = [remove_list] if isinstance(remove_list, str) else list(remove_list or [])
    for list_id, method in [(add_list, 'post')] + [(l, 'delete') for l in removals]:
        if not list_id:
            continue
        try:
            r = getattr(http_requests, method)(
                f'{KLAVIYO_API_BASE}/lists/{list_id}/relationships/profiles/',
                json=payload,
                headers=_klaviyo_headers(),
                timeout=10,
            )
            if r.status_code not in (200, 202, 204):
                print(f'[Store API] Klaviyo list {method} failed for {email_norm} (list {list_id}): {r.status_code} {r.text[:200]}')
        except Exception as e:
            print(f'[Store API] Klaviyo list {method} error for {email_norm} (list {list_id}): {e}')


def _klaviyo_event(metric, email, properties=None, name='', unique_id=None, value=None):
    """
    Record a Klaviyo event — a metric occurrence against a profile.

    Separate from _klaviyo_sync because the two answer different questions.
    _klaviyo_sync says what a person *is* (properties, list membership); this
    says what a person *did*, at a point in time. Cart abandonment is only
    expressible as the second kind: Stripe never tells us a customer closed the
    tab, so "started but has not placed an order" can only be derived from a
    recorded start.

    Fail-soft like _klaviyo_sync — never raises. Note this one runs in the
    checkout request path rather than a webhook, so the stakes are higher than
    usual: a Klaviyo outage must cost us a lifecycle email, never a sale. Every
    failure mode below ends at a print statement.

    `unique_id` is Klaviyo's idempotency key. Pass something stable and
    checkout-specific (the Stripe session or subscription id) so a
    double-clicked Subscribe button or a redelivered webhook records one event
    rather than two — the same reasoning that keeps app_count recomputed instead
    of incremented.

    The event API upserts the profile as a side effect, so a first-time visitor
    who abandons still becomes addressable. It does NOT grant marketing consent,
    which is deliberate — that is a decision for whoever configures the flow.
    """
    if not KLAVIYO_API_KEY or not email or not metric:
        return

    email_norm = email.lower().strip()

    profile_attributes = {'email': email_norm}
    parts = (name or '').strip().split(None, 1)
    if parts:
        profile_attributes['first_name'] = parts[0]
    if len(parts) > 1:
        profile_attributes['last_name'] = parts[1]

    attributes = {
        'metric': {'data': {'type': 'metric', 'attributes': {'name': metric}}},
        'profile': {'data': {'type': 'profile', 'attributes': profile_attributes}},
    }
    if properties:
        attributes['properties'] = {k: v for k, v in properties.items() if v is not None}
    if unique_id:
        attributes['unique_id'] = str(unique_id)
    if value is not None:
        attributes['value'] = value

    try:
        r = http_requests.post(
            f'{KLAVIYO_API_BASE}/events/',
            json={'data': {'type': 'event', 'attributes': attributes}},
            headers=_klaviyo_headers(),
            timeout=10,
        )
        # The events endpoint is asynchronous: 202 Accepted is the success case,
        # and it returns an empty body. Treating "not 2xx" as failure rather than
        # checking for 200 specifically avoids logging a false alarm on every send.
        if r.status_code not in (200, 201, 202):
            print(f'[Store API] Klaviyo event "{metric}" failed for {email_norm}: {r.status_code} {r.text[:200]}')
    except Exception as e:
        print(f'[Store API] Klaviyo event "{metric}" error for {email_norm}: {e}')


def _klaviyo_subscribe(email, list_id=None):
    """
    Grant email marketing consent for a profile.

    Deliberately separate from _klaviyo_sync, because adding a profile to a list
    and subscribing it are different operations in Klaviyo. The list-relationship
    POST in _klaviyo_sync grants membership only — which is why every profile the
    storefront has ever created reads NEVER_SUBSCRIBED. Consent comes from this
    endpoint and nowhere else.

    The list relationship is REQUIRED, not optional, and which list it is matters
    twice over:

      1. Omit it and the account-level default opt-in process applies instead.
         That setting is Double opt-in, so the profile would sit unconfirmed
         pending a click while this function saw a 202 and reported success.
      2. It must not be a lifecycle list. KLAVIYO_LIST_TRIAL triggers the live
         "PF9 Trial Onboarding" flow and KLAVIYO_LIST_PAID triggers the live
         "PF9 Paid Onboarding" flow, both on Added to List. Subscribing here — at
         checkout start, before Stripe has confirmed anything — would begin trial
         onboarding for someone who may never pay.

    Hence KLAVIYO_LIST_CONSENT: a dedicated single-opt-in list with no flow
    triggers. Consent itself is profile-level rather than list-level, so this one
    grant is what makes every flow deliverable to that person, not just the ones
    reading this list.

    Requires the subscriptions:write scope on KLAVIYO_API_KEY. A key without it
    returns 403 and every call here is a no-op — the same silent-failure shape
    that hid the missing events:write scope for a day. Probe rather than assume:
    a malformed POST to this endpoint returns 403 for a missing scope and 400
    once the scope is present, and creates nothing either way.

    Fail-soft like its siblings: never raises, never costs a sale. Note the
    asymmetry that creates. A customer who ticked the box believes they
    subscribed, so a failure here is worse than a failure in _klaviyo_event —
    it is a promise silently broken rather than an email silently skipped.
    That is why every branch below logs.
    """
    if not KLAVIYO_API_KEY or not email:
        return
    if not list_id:
        print('[Store API] Klaviyo subscribe skipped: KLAVIYO_LIST_CONSENT is unset, '
              'so consent was NOT granted despite the customer opting in.')
        return

    email_norm = email.lower().strip()
    payload = {
        'data': {
            'type': 'profile-subscription-bulk-create-job',
            'attributes': {
                # Klaviyo surfaces this as the consent record's origin. It is the
                # only audit trail for how a given profile came to be subscribed,
                # so keep it specific enough to be useful in a dispute.
                'custom_source': 'Storefront checkout',
                'profiles': {'data': [{
                    'type': 'profile',
                    'attributes': {
                        'email': email_norm,
                        'subscriptions': {'email': {'marketing': {'consent': 'SUBSCRIBED'}}},
                    },
                }]},
            },
            'relationships': {'list': {'data': {'type': 'list', 'id': list_id}}},
        }
    }

    try:
        r = http_requests.post(
            f'{KLAVIYO_API_BASE}/profile-subscription-bulk-create-jobs/',
            json=payload,
            headers=_klaviyo_headers(),
            timeout=10,
        )
        # Asynchronous like the events endpoint: 202 Accepted with an empty body
        # is the success case.
        if r.status_code not in (200, 201, 202):
            print(f'[Store API] Klaviyo subscribe failed for {email_norm}: {r.status_code} {r.text[:200]}')
    except Exception as e:
        print(f'[Store API] Klaviyo subscribe error for {email_norm}: {e}')


def _send_email(from_addr, to_addr, subject, body):
    """Send an email via Resend. No-op if resend/key not configured."""
    if not resend or not os.environ.get('RESEND_API_KEY'):
        print(f'[Store API] Resend not configured, skipping email to {to_addr}')
        return False
    try:
        resend.Emails.send({
            "from": from_addr,
            "to": [to_addr] if isinstance(to_addr, str) else to_addr,
            "subject": subject,
            "html": body,
        })
        return True
    except Exception as e:
        print(f'[Store API] Resend send error: {e}')
        return False

# ── Stripe config ──
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')


def _plain(obj):
    """Recursively convert a Stripe response object into plain dicts/lists.

    stripe-python < 8 returned StripeObject, a dict subclass, so handler code
    could call .get() on it directly. From v15 StripeObject is no longer a dict
    subclass and .get() raises AttributeError, which 500s the whole webhook.
    Normalising once at the boundary keeps the handlers version-agnostic.
    Note to_dict() is shallow — nested objects stay StripeObject — so this has
    to recurse (checkout sessions nest customer_details, subs nest items.data).
    """
    if hasattr(obj, 'to_dict'):
        obj = obj.to_dict()
    if isinstance(obj, dict):
        return {k: _plain(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_plain(v) for v in obj]
    return obj

# Free-trial length applied to every new subscription checkout (card up front,
# charged only when the trial ends).
TRIAL_PERIOD_DAYS = int(os.environ.get('TRIAL_PERIOD_DAYS', '30'))

# Shared secret the individual apps present when calling /subscription-status to
# enforce access. Must match the value each app is configured with. If unset,
# the status endpoint refuses all requests (fail-closed).
SUBSCRIPTION_STATUS_SECRET = os.environ.get('SUBSCRIPTION_STATUS_SECRET', '')

# Store-side subscription states that grant access to an app.
ACTIVE_STATUSES = {'active', 'trialing'}

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
    'OPSIQ':    os.environ.get('STRIPE_OPSIQ_PRICE_ID', ''),
    'COMPLI':   os.environ.get('STRIPE_COMPLI_PRICE_ID', ''),
    'EXTRACTR': os.environ.get('STRIPE_EXTRACTR_PRICE_ID', ''),
    'SUPPORTR': os.environ.get('STRIPE_SUPPORTR_PRICE_ID', ''),
    'MAINTAINR': os.environ.get('STRIPE_MAINTAINR_PRICE_ID', ''),
    # $199/mo. LIVE as of 2026-08-09: the env var is set on the store host and the
    # storefront card now calls openSubscribe, so this is a reachable money path.
    # The empty-string default still matters as the failure mode — if the var ever
    # goes missing this resolves to '' and checkout 400s instead of creating a
    # session against a bogus price.
    'FIELDVIEWR': os.environ.get('STRIPE_FIELDVIEWR_PRICE_ID', ''),
    # $59/mo. LIVE as of 2026-08-09, same as FIELDVIEWR above — env var set on
    # the store host, card calls openSubscribe. The '' default remains the
    # failure mode: a missing var 400s checkout rather than building a session
    # against a bogus price.
    'MARKUPR': os.environ.get('STRIPE_MARKUPR_PRICE_ID', ''),
    # NOT sellable yet — the storefront card is "Coming Soon" and calls
    # openWaitlist, so nothing reaches checkout. No Stripe price exists, so this
    # resolves to '' and checkout would 400 even if a card were flipped early.
    # That is the whole point of listing it now: the tables that provisioning
    # and the lifecycle emails read are populated and test-covered BEFORE the
    # money path opens, which is the ordering that kept FIELDVIEWR safe on
    # 08-08. Flipping the card is the LAST step, after the price ID is set on
    # the store host and the API is restarted.
    #
    # ⚠️ This line is not only about checkout. /store-api/app-activity gates on
    # `product not in PRICE_MAP` (see :1933), so until now every ping SHOWJUDGR
    # sent was answered 400 "unknown product" — the app has had a live activity
    # client since 08-26 (app/services/activity.py posts product="SHOWJUDGR").
    # Adding the key here is what starts accepting them. It does NOT start
    # recording them: the _owned_apps() consent gate still drops anyone who is
    # not a paying customer, and there are none yet.
    'SHOWJUDGR': os.environ.get('STRIPE_SHOWJUDGR_PRICE_ID', ''),
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
    'OPSIQ':    'https://opsiq.plainspokenfoundrynine.com',
    'COMPLI':   'https://compli.plainspokenfoundrynine.com',
    'EXTRACTR': 'https://extractr.plainspokenfoundrynine.com',
    'SUPPORTR': 'https://supportr.plainspokenfoundrynine.com',
    'MAINTAINR': 'https://maintainr.plainspokenfoundrynine.com',
    'FIELDVIEWR': 'https://fieldviewr.plainspokenfoundrynine.com',
    'MARKUPR': 'https://markupr.plainspokenfoundrynine.com',
    'SHOWJUDGR': 'https://showjudgr.plainspokenfoundrynine.com',
}

# Product → the app we suggest next, for the paid month-3 expansion email.
#
# Keyed by what the customer already has, because the pitch only lands if it
# names the connection. Pairings follow the workflow, not the product family:
# the app that picks up where the current one stops. Some pairs are deliberately
# reciprocal (REPORTR/EXTRACTR, COMPLI/PERMITR) — from either side the other
# half is genuinely the next thing you'd want.
#
# Every target is checked against index.html: it must have a live Subscribe or
# Start Free CTA. Nothing here may point at a "Join Waitlist" product, or the
# email's one call to action dead-ends.
#
# The Klaviyo template reads related_app_name / related_app_detail /
# related_app_url and has a |default: on each, so an unmapped product degrades
# to a generic "browse all apps" card rather than an empty one.
CROSS_SELL_MAP = {
    'FLOWTRACK': ('TASKFLOW',
        "FLOWTRACK shows you where work is; TASKFLOW is where it gets done — "
        "assignments, due dates and a clear view of what's blocked."),
    'TASKFLOW': ('FLOWTRACK',
        "Once tasks are running, FLOWTRACK shows the process behind them — where "
        "work queues up and which stage slows everything down."),
    'QUALIFI': ('INSPECTR',
        "Quality findings usually start with an inspection. INSPECTR handles the "
        "scheduled checks, photo evidence and sign-off that feed straight into QUALIFI."),
    'INSPECTR': ('COMPLI',
        "Inspection results are evidence. COMPLI maps them to the frameworks you're "
        "audited against, so findings become proof instead of paperwork — free to start."),
    'SHIFTLOG': ('PERMITR',
        "Handovers and permits cover the same shift change. PERMITR controls who is "
        "cleared to work on what, so your log matches what was actually authorised."),
    # COMPLI is the free tier on the storefront ("Start Free"), so lead with that —
    # an expansion email that implies a second invoice for a free app reads badly.
    'PERMITR': ('COMPLI',
        "Permits prove control on the day. COMPLI proves it across the year, mapping "
        "your permit records to the frameworks auditors ask about — and it's free to start."),
    'COMPLI': ('PERMITR',
        "COMPLI tracks the frameworks; PERMITR enforces them at the sharp end — no one "
        "starts high-risk work without a signed permit."),
    # These two point at each other rather than at OPSIQ, which is arguably the
    # sharper fit for both. That was originally forced — OPSIQ was "Coming Soon /
    # Join Waitlist" so the CTA would have dead-ended — but as of 2026-08-01 it
    # sells, so the constraint is gone and this pairing is now a live choice, not
    # a workaround. Left as-is deliberately: retargeting changes what goes out in
    # the month-3 expansion email, and OPSIQ needs the recipient to supply their
    # own Anthropic key, which is a harder ask than a one-click upsell.
    'REPORTR': ('EXTRACTR',
        "REPORTR charts what is already in your systems. EXTRACTR goes after what "
        "isn't — the numbers still stuck in PDFs, invoices and scanned forms."),
    'EXTRACTR': ('REPORTR',
        "EXTRACTR gets the data out of your documents. REPORTR puts it on a "
        "dashboard that refreshes itself, instead of a spreadsheet you rebuild."),
    'OPSIQ': ('REPORTR',
        "OPSIQ answers one question at a time. REPORTR puts the answers you keep "
        "asking on a dashboard that refreshes itself."),
    'SUPPORTR': ('TASKFLOW',
        "Tickets that need real work behind them end up as tasks. TASKFLOW takes the "
        "handoff from SUPPORTR with an owner and a due date."),
    'LANDLORDR': ('MAINTAINR',
        "Every repair request in LANDLORDR becomes a work order in MAINTAINR — "
        "contractor assigned, parts tracked, cost recorded against the unit."),
    'TENANTLINK': ('MAINTAINR',
        "Tenants report problems in TENANTLINK; MAINTAINR turns those into scheduled "
        "work with a contractor, a cost and a completion date."),
    'PROPERTY_BUNDLE': ('MAINTAINR',
        "You already run the property and tenant side. MAINTAINR closes the loop — "
        "repair requests become scheduled work orders with costs tracked per unit."),
    'MAINTAINR': ('INSPECTR',
        "Reactive repairs drop when you catch problems early. INSPECTR runs the "
        "scheduled checks that generate work before something breaks."),
}


def _cross_sell_properties(product):
    """Klaviyo profile properties for the month-3 expansion email.

    Returns {} for an unknown product so the template's own |default: values
    apply — better a generic card than one naming an app that does not exist.
    """
    pair = CROSS_SELL_MAP.get(product)
    if not pair:
        return {}
    related, detail = pair
    return {
        'related_app_name': related,
        'related_app_detail': detail,
        # Deliberately the STORE, not APP_URL_MAP[related]: the recipient does
        # not own this app yet, so the app's own host would just show them a
        # login wall. ?product= opens that card's subscribe modal on the
        # storefront; if index.html is ever served without that handler the
        # param is ignored and they simply land on the store.
        'related_app_url': f'{STORE_URL}/?product={related}',
    }


# Product → the PATH of that app's sign-in screen. Host comes from APP_URL_MAP,
# same single-source rule as REGISTER_PATH below.
#
# This closes a small but real wrongness rather than adding personalisation:
# Trial Day 3 (`Sz4DN3`) renders a button reading "Log in to FLOWTRACK →" whose
# href is `person.Properties.app_login_url|default:'https://store.plainspoken…'`.
# Nothing has ever set that property, so every trialist who clicked a button
# offering to log them into their app landed on the storefront instead.
#
# Every path below was checked against the live host on 2026-08-04, and the three
# empty strings are the finding that made the check worth doing:
#
#   /login       FLOWTRACK SHIFTLOG REPORTR MAINTAINR COMPLI EXTRACTR SUPPORTR
#                TENANTLINK      — page served, password (or magic-link) form present
#   /auth/login  LANDLORDR PERMITR TASKFLOW   — "Sign In — <APP>" served
#   ''           QUALIFI INSPECTR OPSIQ       — root IS the sign-in screen
#
# QUALIFI and INSPECTR are SPAs behind a catch-all: `/login`, `/signin` and
# `/any-nonsense-at-all` all return 200 with the same index.html, so an HTTP probe
# "confirms" a route that does not exist. Their source settles it — INSPECTR's
# App.tsx does `if (!user) return <LoginPage />` before any routing, and QUALIFI
# renders LoginPage the same way. There is no /login route in either; the root is
# the login screen. OPSIQ serves its password form at / directly.
#
# PROPERTY_BUNDLE is deliberately absent. It is two apps, so there is no single
# "log in here", and the template default (the storefront, which links to both)
# is the honest answer.
APP_LOGIN_PATH = {
    'FLOWTRACK':  '/login',
    'SHIFTLOG':   '/login',
    'REPORTR':    '/login',
    'MAINTAINR':  '/login',
    # Static file, not a route: FIELDVIEWR serves a plain SPA, and /login 404s
    # on it. Verified against the live host, not assumed from the pattern above.
    'FIELDVIEWR': '/login.html',
    'COMPLI':     '/login',
    'EXTRACTR':   '/login',
    'SUPPORTR':   '/login',
    'TENANTLINK': '/login',
    'LANDLORDR':  '/auth/login',
    'PERMITR':    '/auth/login',
    'TASKFLOW':   '/auth/login',
    'QUALIFI':    '',
    'INSPECTR':   '',
    'OPSIQ':      '',
    # Next.js like the four above, and its login page really is at /login —
    # src/app/(auth)/login/page.tsx, where (auth) is a route group and so does
    # not appear in the URL. Taken from the filesystem rather than an HTTP
    # probe for the reason spelled out under APP_TEAM_PATH: this app 307s every
    # path to /login when logged out, so a probe cannot tell a real route from
    # a made-up one.
    'MARKUPR':    '/login',
    # Flask, cloned from PERMITR's scaffold, so it follows the /auth/login shape
    # rather than the bare /login one. Read off the app's own routing first
    # (app/__init__.py registers auth_bp with url_prefix="/auth" and
    # app/routes/auth.py declares @auth_bp.route("/login")), THEN confirmed
    # against the live host with a negative control, because unlike MARKUPR this
    # app does not 307 everything to a login page: /auth/login -> 200 with a
    # type="password" field, /auth/zzznotaroute -> 404 (so the 200 is not a
    # catch-all), and the fleet-standard bare /login -> 404. That last probe is
    # the point. Copying '/login' from its neighbours here would have shipped a
    # dead link, and no offline test could have caught it — a wrong path just
    # degrades to STORE_URL and the suite still passes. Only
    # tests/test_app_links.py --live sees it.
    'SHOWJUDGR':  '/auth/login',
}

# Product → the PATH where the account owner adds colleagues.
#
# Six entries for fifteen products, and the shortfall is the point. Paid Month 1
# (`RXA7h3`) states "Your account includes unlimited users at no extra cost" and
# links "here's how to add them →". For the nine products not listed here, no
# page a customer could be sent to was found — so they keep the template default
# and the link goes to the storefront, exactly as it does today. Pointing them at
# a plausible-looking URL would be worse than the status quo, because a 404 on a
# link that just promised free seats reads as a broken product.
#
# Verified 2026-08-04, and one of those checks is why the list is short. An HTTP
# 200/redirect proves nothing on the four Next.js apps: NextAuth middleware
# 307s *every* path to /login before routing, so a made-up control path answered
# 307 as convincingly as the real one. Their entries rest on the filesystem
# instead — `src/app/(dashboard)/settings/page.tsx` exists in all four and
# contains the Team/Invite/Member UI, and `(dashboard)` is a route group, so the
# public URL is /settings.
#
#   PERMITR   /admin/users/  registered at that url_prefix; 302s to its own login
#                            while a sibling control path 404s. Trailing slash is
#                            deliberate — without it Flask 308s to an http:// URL.
#   EXTRACTR  /users         auth_bp has no url_prefix and users_page() renders
#                            users.html; 302s to login, so the route is real.
#
# Deliberately NOT included:
#   COMPLI      has invites, but only as `POST /invite` returning a JSON token.
#               There is no page to link to.
#   OPSIQ       `/auth/users` is a JSON API for its own SPA, not a page.
#   TENANTLINK  its "Invite" flow adds *tenants*, not colleagues. Sending an
#               "add your team" email there would be a category error.
#   MARKUPR     the tempting entry, and wrong. It is Next.js like the four
#               above, so /settings looks like the obvious answer — but its
#               only settings route is src/app/(dashboard)/settings/api-keys,
#               and there is no settings/page.tsx. /settings would 404. There
#               is no member-management UI anywhere in the app: Membership is
#               written by the register route and never edited again. This is
#               the filesystem check earning its keep — the pattern would have
#               produced a broken link inside the email that promises free
#               seats.
#   SHOWJUDGR   it DOES have seat management and still gets no entry, which is
#               a different reason from the rest of this list. Judges are added
#               by `POST /events/<event_id>/judge` (routes/events.py:164,
#               admin-only), a form embedded on the event detail page that
#               redirects back to events.detail. So the page a customer would
#               need is /events/<id> — there is no event-independent URL, and
#               this table cannot carry an id. A new customer has no events
#               yet, so even /events would be an empty list. The storefront
#               fallback is the honest answer until an account-level users page
#               exists.
#   QUALIFI INSPECTR SUPPORTR LANDLORDR TASKFLOW PROPERTY_BUNDLE
#               nothing found. Whether that means the seat-management UI is
#               missing or the pricing claim does not apply to them is a founder
#               question, recorded in LIFECYCLE_STATUS.md, not guessed at here.
APP_TEAM_PATH = {
    'FLOWTRACK': '/settings',
    'SHIFTLOG':  '/settings',
    'REPORTR':   '/settings',
    'MAINTAINR': '/settings',
    'PERMITR':   '/admin/users/',
    'EXTRACTR':  '/users',
    # Static file, like its login page — /users and /settings both 404 here.
    # Worth mapping rather than leaving to the STORE_URL fallback: provisioning
    # makes the buyer an admin of their own tenant, so the "add your team" link
    # is one they can actually act on.
    'FIELDVIEWR': '/admin.html',
}


def _app_link_properties(product):
    """app_login_url / add_team_url for the trial and paid onboarding emails.

    ALWAYS returns both keys, falling back to STORE_URL — which is not a
    workaround, it is byte-for-byte the string both templates already carry as
    their own |default:, so an unmapped product renders exactly as it does
    today.

    Returning {} would have been the obvious shape and is the wrong one, because
    these are PROFILE properties and profile properties persist. A customer who
    trials FLOWTRACK (which has a team page) and later converts SUPPORTR (which
    does not) has app_name overwritten to SUPPORTR while a {} here would leave
    add_team_url still pointing into FLOWTRACK — an email naming one app whose
    link opens another. Writing the fallback explicitly overwrites the stale
    value; omitting the key preserves it.

    Never writes an empty string. Klaviyo's |default: only fires on a *missing*
    value, so '' would render href="" — a CTA that silently goes nowhere, the
    one failure mode worse than pointing at the store.
    """
    base = (APP_URL_MAP.get(product) or '').rstrip('/')
    login_path = APP_LOGIN_PATH.get(product)
    team_path = APP_TEAM_PATH.get(product)
    return {
        'app_login_url': (base + login_path) if base and login_path is not None else STORE_URL,
        'add_team_url': (base + team_path) if base and team_path else STORE_URL,
    }


# Product → the four pieces of onboarding copy the lifecycle emails were shaped
# around: (step1, step2) for Trial Day 1, day3 for Trial Day 3, month1 for Paid
# Month 1. Each is (title, detail).
#
# Until now none of the eight properties behind this was set by any code path, so
# a LANDLORDR customer and a COMPLI customer both received the identical default
# instruction to "add your first item" and "configure your first alert or rule".
# Nothing rendered broken and nothing reported it, because a |default: fails
# silently — which is exactly why it survived this long.
#
# THE RULE FOR EDITING THIS TABLE: every screen, object and action named below
# was read out of that app's own routing before it was written down —
# src/app/(dashboard)/* for the Next.js four, register_blueprint(url_prefix=…)
# for the Flask apps, component and nav names for the two SPAs. Nothing here
# describes a capability that was inferred from the product's name or from the
# storefront's marketing sentence. If a feature is added or renamed, this table
# is wrong in a way no test can see, because the words are only checkable against
# a UI. Re-read the routes rather than editing from memory.
#
# PROPERTY_BUNDLE gets its own entry rather than being left to the defaults, and
# that is a correction to the first draft of this table. Leaving it out looked
# harmless — the templates have defaults, after all — but these are PROFILE
# properties, so a missing key does not fall back to the default, it preserves
# whatever the customer's previous app wrote. A FLOWTRACK customer who later
# bought the property bundle would have received a Paid Month 1 email headed
# PROPERTY_BUNDLE telling them to turn on traceability for a part number.
# Covering every key in PRICE_MAP is what makes that unreachable, and checkout
# rejects anything not in PRICE_MAP (store_api.py:1499), so full coverage here
# means no sellable product can ever inherit another one's copy.
ONBOARDING_COPY = {
    'FLOWTRACK': {
        'step1': ('Add your first parts',
            "Open Inventory and create a handful of the parts you actually stock. You do not "
            "need the whole catalogue — a dozen is enough to see counts move."),
        'step2': ('Set a reorder point on one of them',
            "Pick the part you run out of most and give it a minimum. FLOWTRACK raises it under "
            "Alerts the moment stock drops below the line, which is the difference between a "
            "record and a warning."),
        'day3': ('Run a cycle count',
            "Cycle Count is where the system starts paying for itself: count one shelf, and the "
            "variance against what FLOWTRACK expected tells you how far your current numbers "
            "have drifted."),
        'month1': ('Turn on traceability for one part number',
            "Traceability links a lot through receiving, production and sales, so when a customer "
            "asks where a batch went you answer from a screen instead of a spreadsheet archaeology "
            "session."),
    },
    'QUALIFI': {
        'step1': ('Log one real nonconformance',
            "Raise something that actually happened last week rather than a test record. QUALIFI "
            "is built around the trail an auditor reads, and a real entry shows you the shape of it."),
        'step2': ('Open a CAPA against it',
            "Assign the corrective action to a person with a due date. The link between the finding "
            "and the action is the part auditors check, and it only exists if you make it."),
        'day3': ('Load the standard you are audited against',
            "Add your active standard and map a few existing records to it. What you are looking "
            "for is the gap list — the clauses with nothing attached yet."),
        'month1': ('Export the audit trail',
            "Run the audit trail export once while nothing is at stake. It is far better to find "
            "out what your evidence looks like now than during the week of an audit."),
    },
    'SHIFTLOG': {
        'step1': ('Write one handoff',
            "Have whoever is on now log the end of their shift. One real handoff tells you more "
            "about the fit than any amount of setup."),
        'step2': ('Build the shift template your crew actually uses',
            "Shift Templates turn the things that always get asked into prompts, so the handoff "
            "stops depending on who is writing it and how tired they are."),
        'day3': ('Add a checklist to the handoff',
            "Checklists are what stop a handoff from being prose. Attach one to a shift and the "
            "next crew inherits a state, not a paragraph."),
        'month1': ('Look at your incident history',
            "A month in you have enough incidents logged to read them together. The value is not "
            "the individual entries — it is seeing the same thing appear three times."),
    },
    'REPORTR': {
        'step1': ('Connect one data source',
            "Connectors is the first stop; nothing else in REPORTR does anything until something "
            "is plugged in. Start with the system you are already exporting from by hand."),
        'step2': ('Put one number on a dashboard',
            "Build a single KPI — the one you get asked for most — and pin it. One number that "
            "refreshes itself beats a dashboard you never finish."),
        'day3': ('Schedule it to send itself',
            "Schedules is the point of the whole thing: the report that arrives on its own is the "
            "one that replaces the half-hour you spend rebuilding it."),
        'month1': ('Set an alert on a threshold',
            "Alerts invert the relationship — instead of you checking the dashboard, the dashboard "
            "tells you when a number crosses a line you care about."),
    },
    'INSPECTR': {
        'step1': ('Run one inspection on your phone',
            "Start a new inspection and walk an actual asset. INSPECTR is built for the phone in "
            "your hand on site, so doing it at a desk will undersell it."),
        'step2': ('Record a failure with a photo',
            "When something fails, capture it with severity and a picture and assign the fix. The "
            "photo is what makes the record hold up later."),
        'day3': ('Turn your paper form into a checklist',
            "Rebuild the form your team currently carries as a checklist. From then on every "
            "inspection produces comparable data rather than free text."),
        'month1': ('Pull a report across the month',
            "With a month of inspections behind you the report stops being a record of visits and "
            "starts showing which assets keep failing the same check."),
    },
    'LANDLORDR': {
        'step1': ('Add one property and its units',
            "Start with a single property rather than the whole portfolio. Everything else in "
            "LANDLORDR hangs off a unit, so one is enough to get the shape."),
        'step2': ('Attach a tenant and their lease',
            "Add the tenant, then the lease with its rent and dates. Once the lease exists the rent "
            "ledger starts keeping itself."),
        'day3': ('Log a maintenance request against a unit',
            "Raise a real request and assign a vendor. What you are checking is that the cost lands "
            "against the unit, because that is what makes the year-end numbers mean anything."),
        'month1': ('Run the reports before you need them',
            "A month of rent and expenses is enough for the reports to be worth reading — and far "
            "enough from tax season to fix whatever you find missing."),
    },
    'TENANTLINK': {
        'step1': ('Add a property and one lease',
            "Set up a single unit with its tenant and lease first. The portal a tenant sees is "
            "generated from the lease, so nothing is visible until that exists."),
        'step2': ('Invite that tenant to the portal',
            "Send the portal invite from the tenant list. They get a magic link — no password to "
            "set, which is most of why tenants actually use it."),
        'day3': ('Post a notice and watch it land',
            "Notices are the feature that replaces texting people individually. Post one and it is "
            "in the portal, timestamped, for everyone it applies to."),
        'month1': ('Use the ledger for a rent conversation',
            "The ledger exists so that a disagreement about what was paid is a matter of looking "
            "rather than arguing. Month one is a good time to check it matches your own records."),
    },
    'PERMITR': {
        'step1': ('Set up your site',
            "Add the site your crews actually work on before anything else. Permits are scoped to "
            "a site, so this is the one thing that has to come first."),
        'step2': ('Issue one permit end to end',
            "Raise a permit, approve it and close it out — the whole cycle on something low-risk. "
            "Walking it once is worth more than reading about the states."),
        'day3': ('Attach a JSA',
            "Link a job safety analysis to a permit. The permit records that the work was "
            "authorised; the JSA records what was considered before it was."),
        'month1': ('Turn your paper permit into a checklist',
            "Admin → Checklists is where the form your supervisors already carry becomes the one "
            "PERMITR enforces, so nothing gets signed with a blank left in it."),
    },
    'TASKFLOW': {
        'step1': ('Create one project',
            "Make a project for something already in flight rather than something planned. Live "
            "work is the only honest test."),
        'step2': ('Add tasks with owners and dates',
            "A task without a name against it is a note. Assign each one and give it a due date — "
            "that is what makes the board tell you anything."),
        'day3': ('Get your team into the same project',
            "TASKFLOW is only worth the switch when it is where people look. Two people in one "
            "project is the smallest version of that."),
        'month1': ('Read the project a month in',
            "After a month the useful question is not what is done but what has moved least. That "
            "is visible on the board without anyone having to admit to it."),
    },
    'OPSIQ': {
        'step1': ('Add your Anthropic API key',
            "OPSIQ runs on your own key rather than a shared one, so the first step is Settings. "
            "Nothing can be asked until that is in."),
        'step2': ('Connect the database you want to ask about',
            "Point OPSIQ at a real database — read-only is fine and is the sensible way to start. "
            "It reads your schema, so the better the table names the better the answers."),
        'day3': ('Ask the question you always ask someone else',
            "The test is not whether OPSIQ can write SQL. It is whether it answers the question "
            "you currently have to interrupt an analyst for."),
        'month1': ('Check the SQL it writes',
            "OPSIQ shows the query behind every answer. Reading a few is how you calibrate what to "
            "trust it with — and occasionally how you find out your data means something else."),
    },
    'COMPLI': {
        'step1': ('Pick the framework you are actually audited against',
            "COMPLI carries 40+ frameworks; adopt one. Adopting several on day one produces a "
            "gap list nobody reads."),
        'step2': ('Attach evidence to a control you already satisfy',
            "Start with something you are already doing well. Seeing one control go green shows "
            "you what the other hundred want from you."),
        'day3': ('Read the gap list',
            "The dashboard's value is the controls with nothing attached. That list is your "
            "actual compliance backlog, and it is usually shorter than feared."),
        'month1': ('Add your vendors',
            "Vendor risk is the part that always gets asked about and never gets started. A month "
            "in is the right time, because the framework has told you which vendors matter."),
    },
    'EXTRACTR': {
        'step1': ('Upload one document you already retype',
            "Pick a real invoice or PO — the kind someone currently keys in by hand. A clean sample "
            "PDF will not tell you whether this works on your paperwork."),
        'step2': ('Check the fields it pulled',
            "Look at what came back and correct anything wrong. The corrections are the point: "
            "they tell you where the document layout is fighting the extraction."),
        'day3': ('Run a batch from one supplier',
            "Consistency is where the time goes. Ten documents from the same supplier show you the "
            "real hit rate far better than ten from ten."),
        'month1': ('Push the output into whatever you keyed into before',
            "Extraction only saves time if it lands somewhere. A month in, the question worth "
            "answering is what still gets copied by hand after EXTRACTR has run."),
    },
    'SUPPORTR': {
        'step1': ('Point one support address at it',
            "Inbound email is what turns SUPPORTR on. Until a real address routes in, you are "
            "looking at an empty queue."),
        'step2': ('Answer one ticket from inside it',
            "Reply to a live customer through SUPPORTR rather than your inbox. That is the habit "
            "the whole thing depends on."),
        'day3': ('Write your three most repeated answers into the KB',
            "Everyone has three. Once they are articles you are pasting a link instead of "
            "retyping, and the widget can serve them before a ticket is even raised."),
        'month1': ('Look at what you answered most',
            "A month of tickets tells you which question your product keeps generating. Sometimes "
            "the fix is an article; sometimes it is a change to the product."),
    },
    # Two apps, so the copy has to work for both without pretending they are one.
    # The sequencing is real rather than diplomatic: TENANTLINK generates the
    # tenant's portal from the lease that LANDLORDR holds, so the landlord side
    # genuinely has to be set up first.
    'PROPERTY_BUNDLE': {
        'step1': ('Set up one property in LANDLORDR first',
            "Add a single property, its units, the tenant and the lease. TENANTLINK builds each "
            "tenant's portal from that lease, so there is nothing for them to log into until it "
            "exists."),
        'step2': ('Invite that tenant into TENANTLINK',
            "Send the portal invite from the tenant list. They get a magic link rather than a "
            "password to set, which is most of the reason tenants actually use it."),
        'day3': ('Run one maintenance request through both sides',
            "Have the tenant raise it in the portal and handle it on the landlord side with a "
            "vendor and a cost. That round trip is the whole point of buying the pair."),
        'month1': ('Reconcile the ledger against your own records',
            "A month of rent and expenses is enough for the ledger to be worth checking — and it "
            "is the same ledger the tenant sees, so any disagreement is settled by looking."),
    },
    'MAINTAINR': {
        'step1': ('Add the assets that actually break',
            "Load the equipment that causes you trouble, not the whole plant register. Ten assets "
            "you care about beat four hundred you do not."),
        'step2': ('Raise a work order against one',
            "Create a real work order with a technician and parts. The cost against the asset is "
            "what makes everything downstream worth having."),
        'day3': ('Put one asset on a PM schedule',
            "Schedules are the shift from reacting to planning. Start with the asset whose failures "
            "cost you the most and let MAINTAINR raise the work."),
        'month1': ('Read the downtime record',
            "A month of downtime entries is enough to rank your assets honestly. That ranking is "
            "usually not the one people expect, and it is what the predictive side runs on."),
    },
    'FIELDVIEWR': {
        'step1': ('Point it at one real tag',
            "Open I/O Connections, add your Modbus TCP source and hit Test read before you bind "
            "anything. One tag reading correctly tells you more than a finished-looking screen "
            "that is quietly showing simulated numbers."),
        'step2': ('Trace your own drawing',
            "Load your plot plan or P&ID as an underlay in the builder and drop equipment straight "
            "onto it. Operators trust a screen that looks like the plant they walk — a generic "
            "diagram is the one they stop checking."),
        'day3': ('Set limits on the tag that matters',
            "Give your most important tag real LL/L/H/HH limits. One alarm that fires when "
            "something is genuinely wrong beats twenty that everyone has learned to scroll past."),
        'month1': ('Read the trends, not the live screen',
            "A month of history is where this stops being a display and starts being evidence. "
            "The historian shows you the slow drift nobody catches watching a live number."),
    },
    # Written from the viewer toolbar and the version panel, per the rule above.
    # The tools named here — Calibrate, Length, Area, Cloud, Arrow, Text — are
    # the literal labels in src/components/viewer/Toolbar.tsx, and "Not
    # calibrated" is the message the viewer itself shows.
    'MARKUPR': {
        'step1': ('Upload a drawing you are actually working from',
            "Open Documents and upload one real PDF — a floor plan, a site drawing, a shop "
            "detail. A live sheet shows you the fit in a way a sample file never does."),
        'step2': ('Calibrate the sheet before you measure anything',
            "Open the document, use the Calibrate tool to set one known distance, then Save "
            "scale. Until you do, the viewer says Not calibrated and the Length and Area tools "
            "report page units instead of feet. This is the step that makes a measurement worth "
            "quoting from."),
        'day3': ('Redline a sheet and export it flattened',
            "Mark one up with Cloud, Arrow and Text, then export. The export flattens your "
            "markups into an ordinary PDF, which is what lets you send it to the people who "
            "need to read it and do not have MARKUPR."),
        'month1': ('Upload the next revision as a new version',
            "When a drawing gets reissued, add it to the same document rather than starting a "
            "new one. The version history keeps every markup attached to the sheet it was made "
            "against, and locking a version stops two people redlining the same one at once — "
            "which is the argument this replaces."),
    },
    # Present before the product is sellable, which is deliberate rather than
    # premature: the table has to cover every PRICE_MAP key or a SHOWJUDGR
    # customer inherits whatever their previous app wrote into these profile
    # properties. Written from the app's own routing — events_bp (/events/new,
    # /events/<id>/class, /events/<id>/criterion), registration_bp's public
    # /r/<token>, parking_bp (/parking/event/<id>/plan, map-picker) and
    # series_bp — not from the storefront's marketing sentence.
    'SHOWJUDGR': {
        'step1': ('Create your show and open registration',
            "Add the show you are actually running next, then flip it to open and send entrants "
            "the public sign-up link. They fill in their own car details, which is the half of "
            "show morning that otherwise happens on paper at a folding table."),
        'step2': ('Build the judging sheet your classes really use',
            "Add your classes, then the criteria judges score against. A criterion can belong to "
            "one class instead of the whole show, so the class you judge on originality stops "
            "inheriting the standard sheet everything else uses."),
        'day3': ('Lay out the field before show day',
            "Frame your venue on the satellite map, drop spots on it and drag them to follow the "
            "real drives and islands, then print the sheet. Deciding where 300 cars go is the "
            "job that eats the week before a show, and it is the one worth doing early."),
        'month1': ('Turn your calendar into a season series',
            "Link this year's shows into a series and points carry across all of them on their "
            "own. Standings that lived in one volunteer's spreadsheet become a page you can hand "
            "to every entrant, which is the part nobody else in this category does well."),
    },
}


def _onboarding_properties(product):
    """The eight per-app copy properties for Trial Day 1/3 and Paid Month 1.

    Returns {} for an unmapped product — and unlike _app_link_properties this is
    correct rather than a hazard. These are prose, not hrefs: a stale title from
    a previously-owned app reads as slightly odd advice, whereas a stale URL
    sends someone to the wrong login. And there is no neutral string to
    overwrite with; the templates' own defaults are the neutral version, and
    they only fire when the property is absent.
    """
    copy = ONBOARDING_COPY.get(product)
    if not copy:
        return {}
    props = {}
    for key, prefix in (('step1', 'onboarding_step1'), ('step2', 'onboarding_step2'),
                        ('day3', 'day3_feature'), ('month1', 'month1_feature')):
        title, detail = copy[key]
        props[f'{prefix}_title'] = title
        props[f'{prefix}_detail'] = detail
    return props


def _owned_apps(email):
    """Distinct PF9 apps this address currently pays for, bundles expanded.

    Recomputed from the subscriptions table rather than incremented on the
    Klaviyo profile. Stripe redelivers webhooks, so anything doing `count += 1`
    drifts upward on every replay; recomputing is idempotent and self-heals a
    profile that is already wrong.

    "Owns" is deliberately ACTIVE_STATUSES rather than a set restated here, so
    this can never drift from what actually grants access to an app. If a grace
    period like `past_due` is ever added there, a customer in grace would keep
    their access; without this coupling they would also start being pitched an
    app they already own, which is the exact failure the split exists to
    prevent. `trialing` is in that set, and rightly so: someone on day 3 of a
    second app's trial has plainly already expanded.
    """
    email_norm = (email or '').strip().lower()
    if not email_norm:
        return []
    # Placeholders are generated from the set's length, so the values still go
    # through parameter binding — nothing user-supplied reaches the SQL text.
    statuses = sorted(ACTIVE_STATUSES)
    placeholders = ','.join('?' * len(statuses))
    with get_db() as conn:
        rows = conn.execute(
            f"SELECT DISTINCT product FROM subscriptions "
            f"WHERE lower(email) = ? AND status IN ({placeholders})",
            (email_norm, *statuses)
        ).fetchall()
    apps = set()
    for row in rows:
        # A bundle is one subscription row but several apps, and the customer
        # experiences it as several apps — count it that way.
        apps.update(BUNDLE_MAP.get(row['product'], [row['product']]))
    return sorted(apps)


def _owned_app_properties(email):
    """Klaviyo profile properties backing the month-3 conditional split.

    `app_count` is what the split reads. `apps_owned` exists so a human opening
    the profile can see *which* apps produced that number — a bare integer is
    unauditable the day the split misfires.

    Note the failure direction: if this returns 0 because the lookup found
    nothing, the split sends the expansion email, which is exactly today's
    behaviour. A wrong answer here degrades to the status quo rather than
    silently suppressing mail.
    """
    apps = _owned_apps(email)
    return {'app_count': len(apps), 'apps_owned': ', '.join(apps)}


# ── App activity ingest ──
#
# The one segmentation trigger PLAYBOOK_LIFECYCLE.md listed as "not wired, and
# larger than it looks": last_login / last_action per app, which every activation
# sequence needs and none of them can have, because the store has never had a way
# to hear from the apps. Provisioning already goes store -> app; this is the
# return leg.
#
# Why not read it out of PostHog instead, which already receives app_login and
# core_action_performed and would need no app changes at all: the store holds no
# PostHog read key (only the fifteen apps' write keys exist, in their own envs),
# and POSTHOG_INSTRUMENTATION_STATUS.md carries an explicit warning that its
# per-app checkmarks were "written in May" and never re-verified. Building the
# activation sequences on top of an unverified claim is how a flow ends up
# silently branching on data that was never arriving.
ACTIVITY_KINDS = {'login', 'action'}


def _activity_properties(email):
    """Cross-app activity summary for the Klaviyo profile.

    Aggregated over every app because a Klaviyo profile is per PERSON, not per
    app — and the item that made this repo careful about profile properties is
    that they persist, so a per-app value written under a per-person name
    becomes a lie the moment the customer opens a second app.

    That is why there is no `has_activated` boolean here, which was the obvious
    thing to write. A customer who activated FLOWTRACK and then starts a
    SUPPORTR trial is not activated in SUPPORTR, but a single boolean says they
    are, and the SUPPORTR activation nudge would be suppressed for the one
    person who most needs it. `activated_apps` carries the same information
    without collapsing it: a flow branches on "activated_apps contains
    SUPPORTR", which stays true per app no matter how many they own.

    `last_login_at` / `last_action_at` genuinely are per-person facts — "has not
    been back in 14 days" is a question about the human — so those keep their
    plain names.
    """
    email_norm = (email or '').strip().lower()
    if not email_norm:
        return {}
    with get_db() as conn:
        rows = conn.execute(
            'SELECT product, last_login_at, last_action_at, last_action, action_count '
            'FROM app_activity WHERE email = ?', (email_norm,)
        ).fetchall()
    if not rows:
        return {}

    def newest(field):
        stamps = [r[field] for r in rows if r[field]]
        return max(stamps) if stamps else None

    # Both timestamps are UTC isoformat from the same clock, so a string max is
    # a chronological max. Whichever row owns the most recent stamp of either
    # kind is the app they were last in.
    latest_row, latest_stamp = None, ''
    for r in rows:
        stamp = max(r['last_login_at'] or '', r['last_action_at'] or '')
        if stamp > latest_stamp:
            latest_row, latest_stamp = r, stamp

    activated = sorted(r['product'] for r in rows if (r['action_count'] or 0) > 0)
    return {
        'last_login_at': newest('last_login_at'),
        'last_action_at': newest('last_action_at'),
        'last_active_app': latest_row['product'] if latest_row is not None else None,
        'last_action': latest_row['last_action'] if latest_row is not None else None,
        'activated_apps': ', '.join(activated),
        'activated_app_count': len(activated),
    }


def _record_app_activity(email, product, kind, action=''):
    """Upsert one (customer, app) activity row. Returns (row, should_sync).

    The timestamp is the server's receipt time, not a value the caller supplies.
    An app behind a queue, or with a skewed clock, would otherwise be able to
    write a "last login" in the future — and a future timestamp does not look
    like a bug, it looks like an active customer, so every "has not logged in
    for 14 days" check would quietly exclude them forever. If batching ever
    becomes real, accepting occurred_at is a deliberate change with a reason,
    not a field left open on the off chance.

    should_sync implements the throttle, with firsts exempt. The first login and
    the first key action are state changes rather than samples: they are exactly
    what an activation branch reads, and delaying either by up to six hours
    would mean a customer who activates an hour after signup still receives the
    "here's how to get started" nudge that afternoon.
    """
    email_norm = (email or '').strip().lower()
    now = datetime.utcnow()
    now_iso = now.isoformat()
    is_login = kind == 'login'

    with get_db() as conn:
        conn.execute(
            'INSERT INTO app_activity (email, product) VALUES (?, ?) '
            'ON CONFLICT(email, product) DO NOTHING',
            (email_norm, product)
        )
        if is_login:
            conn.execute(
                'UPDATE app_activity SET '
                '  login_count    = login_count + 1, '
                '  first_login_at = COALESCE(first_login_at, ?), '
                '  last_login_at  = ? '
                'WHERE email = ? AND product = ?',
                (now_iso, now_iso, email_norm, product)
            )
        else:
            # COALESCE(NULLIF(...)) so that an action ping which does not name
            # the action leaves the last named one in place. Blanking it would
            # be strictly worse than keeping a slightly older name: the field
            # exists so a human reading the profile can tell what the customer
            # actually did.
            conn.execute(
                'UPDATE app_activity SET '
                '  action_count    = action_count + 1, '
                '  first_action_at = COALESCE(first_action_at, ?), '
                '  last_action_at  = ?, '
                '  last_action     = COALESCE(NULLIF(?, \'\'), last_action) '
                'WHERE email = ? AND product = ?',
                (now_iso, now_iso, (action or '').strip(), email_norm, product)
            )
        conn.commit()
        row = conn.execute(
            'SELECT * FROM app_activity WHERE email = ? AND product = ?',
            (email_norm, product)
        ).fetchone()

    is_first = row['login_count'] == 1 if is_login else row['action_count'] == 1
    if is_first or not row['last_synced_at']:
        return row, True
    try:
        age = (now - datetime.fromisoformat(row['last_synced_at'])).total_seconds()
    except (TypeError, ValueError):
        # An unparseable stamp is corruption, and the safe reading of corruption
        # is "we do not know when we last synced" — sync, rather than sit on it.
        return row, True
    return row, age >= ACTIVITY_SYNC_INTERVAL


def _mark_activity_synced(email, product):
    with get_db() as conn:
        conn.execute(
            'UPDATE app_activity SET last_synced_at = ? WHERE email = ? AND product = ?',
            (datetime.utcnow().isoformat(), (email or '').strip().lower(), product)
        )
        conn.commit()


# Product → registration endpoint PATH. The host comes from APP_URL_MAP above,
# so where an app lives is recorded in exactly one place.
#
# This used to be a map of full loopback URLs, introduced on the belief that the
# store API ran on the same host as the apps. It does not: store_api runs on
# xfree143, every target here runs on pf9-2. So 127.0.0.1:<port> resolved to
# nothing and provisioning had been failing for every product — silently, since
# _provision_account swallows connection errors and the customer just gets the
# "we'll send your login details shortly" wording in the welcome email.
#
# Three of those ports were also simply wrong (OPSIQ was on 5050, which is
# actually SUPPORTR; SUPPORTR was on 5000, which is dead; MAINTAINR was on 3008,
# not 3006). Deriving the host from APP_URL_MAP makes that whole class of drift
# impossible — there are no ports here to get out of date.
#
# Public HTTPS is not a fallback, it is the only transport that reaches all of
# these: most of the Flask/gunicorn apps on pf9-2 bind 127.0.0.1 only, so no
# cross-host address exists for them. Verified from xfree143 that Cloudflare
# passes server-to-server POSTs through to every one of these origins.
REGISTER_PATH = {
    'FLOWTRACK':  '/api/auth/register',
    'REPORTR':    '/api/auth/register',
    'SHIFTLOG':   '/api/auth/register',
    'INSPECTR':   '/api/auth/register',
    'LANDLORDR':  '/api/auth/register',
    'TENANTLINK': '/api/auth/register',
    'PERMITR':    '/api/auth/register',
    'TASKFLOW':   '/api/auth/register',
    'OPSIQ':      '/api/auth/register',
    'COMPLI':     '/api/v1/auth/register',   # COMPLI versions its API; the rest do not
    'EXTRACTR':   '/api/auth/register',
    'SUPPORTR':   '/api/auth/register',
    'MAINTAINR':  '/api/auth/register',
    'QUALIFI':    '/api/auth/register',
    # Added with the endpoint itself — FIELDVIEWR had no register route at all
    # until now, so it was the one product that could have taken money and
    # silently provisioned nothing. It creates a dedicated tenant per customer
    # and requires PROVISION_SECRET; without the secret it 404s.
    'FIELDVIEWR': '/api/auth/register',
    # NOT /api/auth/register. MARKUPR's route is /api/register, and the
    # difference is not cosmetic: its NextAuth middleware allowlist covers
    # /api/auth by prefix, so a route under that path would have been let
    # through by accident — which is exactly why FLOWTRACK never hit the
    # redirect bug and MARKUPR did. Fixed on the app side; recorded here so
    # nobody "corrects" this line to match the others.
    'MARKUPR':    '/api/register',
    # The fleet-standard path and the fleet-standard env var name
    # (PROVISION_SECRET, not an app-prefixed one). Verified on the app side:
    # api_register_bp is registered with url_prefix="/api/auth". Fail-closed
    # like FIELDVIEWR — 404 while the secret env is unset, 403 on a bad header,
    # so a forgotten env var reads as "provisioning broken", never as open
    # self-registration. Already armed on the host as of 2026-08-26.
    'SHOWJUDGR':  '/api/auth/register',
}


def _register_url(product):
    """Public registration endpoint for a product, or None if we don't have one."""
    base = APP_URL_MAP.get(product)
    path = REGISTER_PATH.get(product)
    if not base or not path:
        return None
    return base.rstrip('/') + path


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
                cancelled_at            TEXT,
                trial_end               TEXT,
                trial_notice_sent_for   TEXT
            )
        ''')
        # Lightweight migration: add later columns to pre-existing subscriptions tables.
        #
        # init_db() runs at import in wsgi_store.py, and gunicorn starts 2 workers
        # without --preload, so on the restart that first ships a new column both
        # workers can read the same PRAGMA and both attempt the ALTER. The loser
        # gets "duplicate column name" and dies during boot. Tolerating exactly
        # that error — and nothing else — makes the migration safe to race.
        def add_column(name, decl):
            if name in cols:
                return
            try:
                conn.execute(f'ALTER TABLE subscriptions ADD COLUMN {name} {decl}')
            except sqlite3.OperationalError as e:
                if 'duplicate column name' not in str(e).lower():
                    raise
                print(f'[Store API] Column {name} already added by another worker')

        # One row per (customer, app) — a running summary, NOT an event log.
        #
        # A log would be the obvious shape and is the wrong one here. The store
        # runs on a single small box with a SQLite file and no retention job, so
        # a table that grows one row per login grows forever, and nothing in the
        # lifecycle programme ever asks "when was the 40th login" — every
        # consumer asks "when was the last one" and "has this person ever done
        # the key action". Both are answerable from a fixed-size row.
        #
        # counts are kept because Klaviyo will NOT see every ping (see
        # ACTIVITY_SYNC_INTERVAL): they are the true totals, sent on the App
        # Activity event, so a flow counting metric occurrences would under-report
        # where these do not. The throttle costs resolution in time, never
        # accuracy in count.
        conn.execute('''
            CREATE TABLE IF NOT EXISTS app_activity (
                email           TEXT NOT NULL,
                product         TEXT NOT NULL,
                first_login_at  TEXT,
                last_login_at   TEXT,
                first_action_at TEXT,
                last_action_at  TEXT,
                last_action     TEXT,
                login_count     INTEGER NOT NULL DEFAULT 0,
                action_count    INTEGER NOT NULL DEFAULT 0,
                last_synced_at  TEXT,
                PRIMARY KEY (email, product)
            )
        ''')

        cols = {row['name'] for row in conn.execute("PRAGMA table_info(subscriptions)").fetchall()}
        add_column('trial_end', 'TEXT')
        # Claim-marker for the day-27 pre-charge email. Holds the trial_end the
        # notice was sent FOR, not a send timestamp, so that extending a trial
        # re-arms the notice for the new date instead of being swallowed as a
        # duplicate. Existing rows get NULL = "not yet sent", which is correct:
        # no row predating this column was ever sent one.
        add_column('trial_notice_sent_for', 'TEXT')
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

    lead_id = None
    try:
        with get_db() as conn:
            cur = conn.execute(
                'INSERT INTO demo_requests (name, company, email, message, product, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                (name, company, email, message, product, datetime.utcnow().isoformat())
            )
            lead_id = cur.lastrowid
            conn.commit()
    except Exception as e:
        print(f'[Store API] DB error: {e}')
        return _cors_response(jsonify({'success': False, 'error': 'Database error'}), 500)

    try:
        _send_notification(name, company, email, message, product)
    except Exception as e:
        print(f'[Store API] Email error: {e}')

    try:
        _hubspot_push_contact(
            email=email,
            name=name,
            company=company,
            list_id=_hubspot_list_for_product(product),
        )
    except Exception as e:
        print(f'[Store API] HubSpot push error: {e}')

    # Until now this endpoint ended at SQLite, one internal email, and HubSpot,
    # so the strongest intent signal the store can produce — a named person
    # asking for something by name — never reached the system that does the
    # emailing. Every Klaviyo flow hangs off checkout or subscription events, so
    # someone who raised a hand and did not buy got nothing at all.
    #
    # This records the fact and sends nothing. 'Lead Captured' did not exist as a
    # metric on the account before this (checked against the live metrics list on
    # 2026-08-04, 25 metrics, no such name), and a flow triggers on a metric
    # someone bound it to — so nothing can already be listening. It starts
    # mattering when a flow is built on it, which is a deliberate act.
    #
    # _klaviyo_event also upserts the profile WITHOUT granting marketing consent,
    # which is what makes this safe to call for a person who only asked a
    # question: they become addressable by a flow someone chooses to build, not
    # subscribed to marketing they never asked for.
    try:
        lead_type = _lead_type_for(product)
        lead_properties = {
            'lead_type': lead_type,
            'vertical': _lead_vertical_for(product),
        }
        # `product` is defaulted to 'General' upstream, but a payload of all
        # whitespace survives that and strips to ''. Writing an empty property
        # is worse than writing none: it satisfies Klaviyo's `|default:` and
        # prints a blank where the fallback should have been.
        if product:
            lead_properties['product_tag'] = product   # raw, as the page sent it
        # Only when it names something we can actually sell. PROPERTY_SUITE and
        # MANUFACTURING_SUITE are marketing groupings and are not in PRICE_MAP,
        # so writing them here would make `product` mean two different things
        # depending on the surface.
        #
        # MARKUPR was the third example here and no longer is. It went into
        # PRICE_MAP on 08-08 and its card flipped to Subscribe on 08-09, so the
        # plain name is now sold and this branch writes it — which is correct.
        # The suffixed 'MARKUPR (waitlist)' string is still not a PRICE_MAP key,
        # so legacy rows and any future waitlist card behave as before.
        #
        # SHOWJUDGR (added 08-28) is the case that shows why the test is
        # membership and not truthiness: it IS a PRICE_MAP key but its price ID
        # resolves to '' until the live price exists. Membership means "a product
        # we know", which is the right thing to write here — and its Coming Soon
        # card posts 'SHOWJUDGR (waitlist)', which is not a key, so a pre-launch
        # lead still gets no `product` property.
        if product in PRICE_MAP:
            lead_properties['product'] = product
        if company:
            lead_properties['company'] = company
        # The free text is deliberately not forwarded. It is the most sensitive
        # field on the form, it has no use in a marketing tool, and for every
        # surface except contact.html it is boilerplate our own JS wrote. The
        # internal notification email already carries it to a human.
        if lead_type == 'question':
            lead_properties['has_question'] = bool(message)

        # The bare product name, for copy that has to read as a sentence.
        # openWaitlist() in index.html (the post is at :1106 as of 08-28) sends
        # 'SHOWJUDGR (waitlist)', and "You're on the SHOWJUDGR (waitlist)
        # waitlist" is not a sentence. Only emitted here, where the
        # marker is a known suffix and stripping it leaves exactly the thing
        # being waited on — the other tags carry no name worth extracting.
        #
        # Shape-checked before it is emitted, and this is the one property here
        # that genuinely needs it. Unlike every other value in this block it is
        # BOTH attacker-controlled AND rendered into an email body — and the
        # submitter also chooses the recipient, so a free-form pass-through would
        # let anyone put arbitrary prose in front of a third party over our
        # domain and our sending reputation. Klaviyo does escape it (verified
        # 2026-08-04: a `<script>` tag renders as `&lt;script&gt;`), so this is
        # not about markup; it is about the sentence.
        #
        # `^[A-Z0-9]{2,20}$` is not a guess at what looks safe — it is exactly
        # what the callers sent. Between 2026-08-09 and 2026-08-28 index.html had
        # NO waitlist callers at all (FIELDVIEWR and MARKUPR were the last two and
        # both flipped to Subscribe); the code stayed because the shape was still
        # reachable via store_leads.db rows. As of 2026-08-28 it is live again —
        # SHOWJUDGR ships as a Coming Soon card and sends 'SHOWJUDGR (waitlist)'.
        # It matches for the same reason the other two did: the pattern was never
        # a whitelist of specific names, so nothing here changes.
        # Anything else falls through to the template's `|default:'PF9'`.
        if lead_type == 'waitlist' and product:
            bare = product.split(' (')[0].strip()
            if re.fullmatch(r'[A-Z0-9]{2,20}', bare):
                lead_properties['product_name'] = bare

        # The asset this person was promised by email, resolved server-side so
        # a flow can render one link instead of branching three ways on a
        # source page. Absent for any tag not in the table, which is what the
        # template's `|default:` is for.
        if lead_type == 'lead_magnet':
            asset = _LEAD_MAGNET_ASSETS.get(product)
            if asset:
                lead_properties['lead_magnet_name'] = asset[0]
                lead_properties['lead_magnet_url'] = asset[1]

        # What they were actually comparing. Without it the PDF request says
        # nothing beyond "someone wants a PDF", and the person making that PDF
        # by hand has to go back to the row to find the number.
        if lead_type == 'calculator':
            size, noun = _calculator_size_from(message)
            if size:
                lead_properties['calculator_size'] = size
                lead_properties['calculator_unit'] = noun

        # Path only, never the query string: a referrer's query can carry
        # anything, and this one is written to a third party.
        referer = request.headers.get('Referer') or ''
        if referer:
            try:
                path = urlparse(referer).path
                if path:
                    lead_properties['source_page'] = path
            except Exception:
                pass

        # contact.html is the ONLY one of the eight surfaces with a name field.
        # The other seven send `name: email.split('@')[0]` (index.html:960,
        # per-door-calculator.html:361, per-user-calculator.html:364, the three
        # lead magnets, refer/). Passing that through would write `j.smith` into
        # person.first_name — and EVERY live template greets with
        # `{{ person.first_name|default:'there' }}`, so one calculator lead would
        # permanently downgrade that person's greeting from "Hi there," to
        # "Hi j.smith," in every email they ever get from us, including the paid
        # lifecycle ones. The default is the better copy; let it win.
        #
        # Compared against the local part rather than switched on lead_type,
        # because that is the fact that actually matters and it does not depend
        # on the classifier being right about a surface added later.
        local_part = email.split('@')[0] if '@' in email else email
        real_name = name if (name or '').strip().lower() != local_part.strip().lower() else None

        _klaviyo_event(
            metric='Lead Captured',
            email=email,
            name=real_name,
            # The row id, so a Klaviyo event can be traced back to the row a
            # human replies from. The submit button is disabled for the duration
            # of the request on every surface, so a double click cannot produce
            # two rows to begin with.
            unique_id=f'lead-{lead_id}' if lead_id else None,
            properties=lead_properties,
        )
    except Exception as e:
        # Belt and braces: _klaviyo_event is already fail-soft, but this runs in
        # the visitor's request path and nothing here is worth a 500.
        print(f'[Store API] Klaviyo lead event error: {e}')

    return _cors_response(jsonify({'success': True, 'message': 'Demo request received!'}))


@store_bp.route('/leads', methods=['GET'])
def get_leads():
    expected = os.environ.get('LEADS_SECRET', '')
    provided = request.headers.get('X-PF9-Secret', '') or request.args.get('secret', '')
    if not expected or not secrets.compare_digest(provided, expected):
        return _cors_response(jsonify({'error': 'Unauthorized'}), 401)

    with get_db() as conn:
        rows = conn.execute('SELECT * FROM demo_requests ORDER BY created_at DESC').fetchall()
    return _cors_response(jsonify({'leads': [dict(row) for row in rows], 'count': len(rows)}))


@store_bp.route('/health', methods=['GET'])
def health():
    return _cors_response(jsonify({'status': 'ok', 'service': 'store-api'}))


@store_bp.route('/app-activity', methods=['POST'])
def app_activity():
    """An app reports that one of its users logged in, or did the key action.

    Server-to-server only, and deliberately NOT wrapped in _cors_response: the
    caller has to present a shared secret, and any endpoint a browser can reach
    with a secret header is an endpoint whose secret is in someone's devtools.
    The store's CORS policy allows only Content-Type anyway, so a browser could
    not send the header cross-origin even if this returned the headers — leaving
    them off makes that intentional rather than incidental.

        POST /store-api/app-activity
        X-PF9-Activity-Secret: <ACTIVITY_SECRET>
        {"email": "...", "product": "FLOWTRACK", "kind": "login"|"action",
         "action": "scan"}            # `action` optional, only read for kind=action

    Nothing here sends mail. It writes one SQLite row and, at most, updates a
    Klaviyo profile — the flows that will consume it do not exist yet, which is
    the correct order: the data has to be accumulating before a flow branching
    on it means anything, because Klaviyo flows do not backfill.
    """
    # Fail closed. An unconfigured secret disables the route rather than opening
    # it, so shipping this before the value is set cannot create a window where
    # anyone can write to customer profiles.
    provided = request.headers.get('X-PF9-Activity-Secret', '')
    if not ACTIVITY_SECRET or not secrets.compare_digest(provided, ACTIVITY_SECRET):
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    product = (data.get('product') or '').strip().upper()
    kind = (data.get('kind') or '').strip().lower()
    action = (data.get('action') or '').strip()[:64]

    if '@' not in email:
        return jsonify({'error': 'valid email required'}), 400
    if kind not in ACTIVITY_KINDS:
        return jsonify({'error': f'kind must be one of {sorted(ACTIVITY_KINDS)}'}), 400
    # PRICE_MAP rather than APP_URL_MAP: this is the same gate checkout uses, so
    # the set of products that can appear in activity is exactly the set that can
    # appear in a subscription, and no reconciliation between the two is needed.
    if product not in PRICE_MAP:
        return jsonify({'error': 'unknown product'}), 400

    # The consent gate, and the reason this endpoint cannot simply forward
    # everything it receives. An app's users are not all customers — the buyer
    # invites colleagues, and those colleagues never visited the store, never
    # gave us an address and never agreed to hear from us. _klaviyo_event upserts
    # a profile as a side effect, so forwarding their logins would quietly build
    # a marketing database out of people who have no idea we exist.
    #
    # Checked BEFORE the row is written, not after, which was this endpoint's
    # first shape. Recording them locally sounded harmless — it is our own box
    # and the count is mildly useful — but it means an unbounded table of the
    # addresses of people who never transacted with the store, kept in a
    # database whose entire contents are otherwise leads and subscriptions, for
    # a population we have already decided we will never email. The diagnostic
    # this gives up ("are pings arriving at all?") is covered by the log line,
    # and logs rotate where the DB does not.
    if not _owned_apps(email):
        print(f'[Store API] app-activity from a non-customer ({product}/{kind}); not recorded')
        return jsonify({'ok': True, 'synced': False, 'reason': 'not a store customer'})

    row, should_sync = _record_app_activity(email, product, kind, action)
    if not should_sync:
        return jsonify({'ok': True, 'synced': False, 'reason': 'throttled'})

    # Both Klaviyo helpers are fail-soft and document that they never raise, so
    # this looks redundant. It is not: the caller here is an app's LOGIN handler.
    # If anything in this block ever does raise — a future edit, a change in
    # those helpers, a sqlite error in _mark_activity_synced — the store would
    # return 500 to a login, and a client written the obvious way (post, then
    # check the status) would turn a marketing telemetry failure into customers
    # unable to sign in. Nothing about lifecycle email is worth that risk.
    try:
        _klaviyo_sync(email=email, properties=_activity_properties(email))
        # Sent as well as the profile properties because only an event can be
        # triggered or filtered on with a time window — "did the key action since
        # entering this flow" is not expressible against a property, however
        # fresh the property is.
        _klaviyo_event('App Activity', email, properties={
            'product': product,
            'kind': kind,
            'action': action or None,
            # True totals from SQLite, not a count of what Klaviyo received. The
            # throttle drops pings, so a metric-occurrence count in Klaviyo would
            # under-report; these do not.
            'login_count': row['login_count'],
            'action_count': row['action_count'],
            'first_of_kind': (row['login_count'] == 1) if kind == 'login'
                             else (row['action_count'] == 1),
        })
        # Deliberately after the sends, and skipped when they blow up: the mark
        # is what starts the six-hour throttle, so recording it on a failed
        # attempt would suppress retries for six hours over an error we did not
        # even confirm happened.
        _mark_activity_synced(email, product)
    except Exception as e:
        print(f'[Store API] app-activity sync error for {email} ({product}): {e}')
        return jsonify({'ok': True, 'synced': False, 'reason': 'sync error'})
    return jsonify({'ok': True, 'synced': True})


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
    # Absent or false means no consent. Deliberately not in the required-field
    # check below: a tick you cannot check out without is not consent, and it
    # would put a marketing gate in front of a paying customer.
    consent = bool(data.get('marketing_consent'))

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
            # 30-day free trial. Card is collected up front (payment_method_collection
            # defaults to 'always' for trials) but not charged until the trial ends,
            # at which point Stripe auto-converts to the paid subscription.
            subscription_data={'trial_period_days': TRIAL_PERIOD_DAYS},
            metadata={
                'product': product,
                'name': name,
                'company': company,
            },
        )
    except Exception as e:
        print(f'[Store API] Stripe error: {e}')
        return _cors_response(jsonify({'error': 'Failed to create checkout session'}), 500)

    # The success return deliberately sits OUTSIDE the try above. Anything added
    # after this point that raises would otherwise be caught by that handler and
    # reported to the customer as "Failed to create checkout session" — a 500 for
    # a checkout that Stripe already created successfully.

    # Record the *start* of checkout. This is the only signal that a customer
    # ever wanted this app: Stripe is silent when someone closes the tab, so
    # without this event, abandonment is invisible and the L2 cart-abandon
    # sequence has nothing to trigger on. Fires after Session.create() succeeds,
    # so a Stripe failure is never reported to Klaviyo as an abandoned cart.
    _klaviyo_event(
        metric='Started Checkout',
        email=email,
        name=name,
        # Stripe's session id, so a double-clicked Subscribe button records one
        # abandonment rather than two — and so does a retried request.
        unique_id=session.id,
        properties={
            'app_name': product,
            'product': product,
            'company': company or None,
            # Two links, because they expire differently and the emails are
            # 47 hours apart:
            #   resume_link  — Stripe's own hosted page, keeps the exact cart,
            #                  but Stripe expires checkout sessions after 24h.
            #   restart_link — the storefront card, never expires, costs the
            #                  customer a re-typed name and email.
            # L2-E1 (1h) should use resume_link. L2-E2 (48h) MUST NOT: by then
            # the session is dead and the link renders an expired-page error.
            'resume_link': session.url,
            'restart_link': f'{STORE_URL}/?product={product}',
        },
    )

    # Consent, if they asked for it. Runs after the event above so the profile
    # already carries a name, and inside the same outside-the-try region so a
    # Klaviyo failure cannot surface as "Failed to create checkout session".
    #
    # Granting it *here* rather than in the webhook is the whole point: checkout
    # start is the only moment that covers someone who abandons, and abandoners
    # are exactly who the L2 sequence exists to reach. A webhook-time grant would
    # reach only the customers who completed — the ones least in need of it.
    if consent:
        _klaviyo_subscribe(email, list_id=KLAVIYO_LIST_CONSENT)

    return _cors_response(jsonify({'url': session.url}))


@store_bp.route('/subscription-status', methods=['GET'])
def subscription_status():
    """Read-only status lookup the individual apps call to enforce access.

    Auth: caller presents the shared secret via the `X-PF9-Secret` header (or
    `?secret=` fallback). Fail-closed — no secret configured server-side, or a
    mismatch, returns 401 and no data.

    Query params: product (store product key, e.g. TASKFLOW), email.
    Returns: {status, allowed, trial_end, product}. `allowed` is the single
    boolean the apps gate on; status is included for display/telemetry.
    """
    if not SUBSCRIPTION_STATUS_SECRET:
        return jsonify({'error': 'status endpoint not configured'}), 401
    provided = request.headers.get('X-PF9-Secret', '') or request.args.get('secret', '')
    if not secrets.compare_digest(provided, SUBSCRIPTION_STATUS_SECRET):
        return jsonify({'error': 'unauthorized'}), 401

    product = (request.args.get('product') or '').strip().upper()
    email   = (request.args.get('email') or '').strip().lower()
    if not product or not email:
        return jsonify({'error': 'product and email are required'}), 400

    # A subscription may be held directly (product == requested) or via a bundle
    # that includes it. Also tolerate the TENANTLINK/TENANTLINKR naming split.
    candidates = {product}
    if product == 'TENANTLINKR':
        candidates.add('TENANTLINK')
    elif product == 'TENANTLINK':
        candidates.add('TENANTLINKR')
    for bundle_name, members in BUNDLE_MAP.items():
        if product in members or any(c in members for c in list(candidates)):
            candidates.add(bundle_name)

    placeholders = ','.join('?' for _ in candidates)
    with get_db() as conn:
        row = conn.execute(
            f'''SELECT status, trial_end, product FROM subscriptions
                WHERE lower(email) = ? AND upper(product) IN ({placeholders})
                ORDER BY created_at DESC LIMIT 1''',
            (email, *[c.upper() for c in candidates])
        ).fetchone()

    if not row:
        return jsonify({'status': 'none', 'allowed': False, 'trial_end': None, 'product': product})

    status = (row['status'] or '').lower()
    return jsonify({
        'status': status,
        'allowed': status in ACTIVE_STATUSES,
        'trial_end': row['trial_end'],
        'product': row['product'],
    })


@store_bp.route('/stripe-webhook', methods=['POST'])
def stripe_webhook():
    if not stripe:
        return jsonify({'error': 'Stripe not configured'}), 500

    payload = request.data
    sig_header = request.headers.get('Stripe-Signature', '')

    # Fail closed: without a configured signing secret we cannot verify the
    # event came from Stripe, and this endpoint provisions real accounts. Refuse
    # rather than trust unsigned JSON.
    if not STRIPE_WEBHOOK_SECRET:
        print('[Store API] STRIPE_WEBHOOK_SECRET not configured; refusing webhook')
        return jsonify({'error': 'Webhook not configured'}), 500

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        print(f'[Store API] Webhook signature error: {e}')
        return jsonify({'error': 'Invalid signature'}), 400

    # Convert once at the boundary so every handler below can keep using plain
    # dict .get() access regardless of which stripe-python major is installed.
    obj = _plain(event['data']['object'])

    if event['type'] == 'checkout.session.completed':
        _handle_checkout_completed(obj)

    elif event['type'] == 'customer.subscription.deleted':
        _handle_subscription_cancelled(obj)

    elif event['type'] == 'customer.subscription.updated':
        _handle_subscription_updated(obj)

    elif event['type'] == 'invoice.payment_failed':
        _handle_payment_failed(obj)

    elif event['type'] == 'customer.subscription.trial_will_end':
        _handle_trial_will_end(obj)

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

    # Pull the real subscription status + trial end from Stripe. A trial checkout
    # lands as 'trialing' (not 'active'); trial_end is a unix timestamp.
    sub_status = 'active'
    trial_end_iso = None
    price_display = None
    try:
        sub = _plain(stripe.Subscription.retrieve(subscription_id))
        sub_status = sub.get('status', 'active') or 'active'
        te = sub.get('trial_end')
        if te:
            trial_end_iso = datetime.utcfromtimestamp(int(te)).isoformat()
        # Read the amount actually being charged rather than a hardcoded figure,
        # so the pre-charge email can never quote a price that differs from the bill.
        price_display = _trial_price_display(sub)
    except Exception as e:
        print(f'[Store API] Could not retrieve subscription {subscription_id}: {e}')

    # Save subscription
    with get_db() as conn:
        conn.execute(
            '''INSERT INTO subscriptions
               (stripe_customer_id, stripe_subscription_id, email, name, company, product, status, temp_password, created_at, trial_end)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (customer_id, subscription_id, email, name, company, product, sub_status, temp_password, datetime.utcnow().isoformat(), trial_end_iso)
        )
        conn.commit()

    # Provision account in the app (bundles provision multiple apps)
    products_to_provision = BUNDLE_MAP.get(product, [product])
    results = {p: _provision_account(p, email, name, company, temp_password)
               for p in products_to_provision}

    # Only claim the account is ready when every app said 'ok'. 'exists' counts
    # as not-ready on purpose: the customer can get in, but not with the password
    # this email is about to quote, so the honest thing is to fall back to the
    # "we'll send your login details shortly" wording and alert.
    all_provisioned = all(r == 'ok' for r in results.values())

    if not all_provisioned:
        try:
            _send_provisioning_alert(email, product, results, subscription_id)
        except Exception as e:
            print(f'[Store API] Provisioning alert error: {e}')

    if all_provisioned:
        # Password has been delivered to the app(s) and is about to be emailed to
        # the customer from the in-memory copy — don't retain it in cleartext.
        with get_db() as conn:
            conn.execute('UPDATE subscriptions SET provisioned = 1, temp_password = NULL WHERE stripe_subscription_id = ?', (subscription_id,))
            conn.commit()

    # Send welcome email
    try:
        _send_welcome_email(email, name, product, temp_password, all_provisioned)
    except Exception as e:
        print(f'[Store API] Welcome email error: {e}')

    # Push subscriber to HubSpot
    try:
        _hubspot_push_contact(
            email=email,
            name=name,
            company=company,
            list_id=HUBSPOT_LIST_SUBSCRIBERS,
        )
    except Exception as e:
        print(f'[Store API] HubSpot subscriber push error: {e}')

    # Enroll in the Klaviyo trial flow. trial_end_date/app_price are kept on the
    # profile for the onboarding copy; the day-27 pre-charge email no longer
    # reads them — it takes both straight off the Stripe subscription instead.
    trial_properties = {
        'app_name': product,
        'app_price': price_display,
        'trial_end_date': _format_trial_end(trial_end_iso),
        'manage_subscription_url': f'{STORE_URL}/login.html',
        # Starting a trial clears any earlier 'cancelled'. The property is
        # account-level and nothing else resets it on the way back up:
        # _handle_subscription_updated only writes 'active' at conversion, three
        # weeks later, so without this a returning customer would sit at
        # 'cancelled' through their entire second trial.
        #
        # This does NOT currently rescue their welcome email — X2tesT is set to
        # "No re-entry" (verified 2026-08-02: reentry_criteria absent from the
        # flow definition), so a returning customer never re-enters that flow at
        # all and the day-27 filter never gets to judge them. The reason to
        # write it anyway is that 'cancelled' on someone who is actively
        # trialing is simply false, and the day-27 filter has now made this
        # property load-bearing: any flow or segment keyed on it inherits the
        # lie, and enabling re-entry later would turn it into a silent
        # suppression of the whole onboarding sequence.
        'subscription_status': 'trialing',
    }
    # Cross-sell target is a pure function of the product, so set it now rather
    # than waiting for conversion. Costs nothing, and means the month-3 email
    # has data even if the trialing -> active webhook is ever missed.
    trial_properties.update(_cross_sell_properties(product))
    # Trial Day 3's only CTA is "Log in to <app> →", and until now it sent every
    # trialist to the storefront. Set at checkout because day 3 arrives long
    # before the conversion webhook that the paid emails hang off.
    trial_properties.update(_app_link_properties(product))
    # Trial Day 1 and Day 3 read the per-app onboarding copy. Both land inside
    # the trial, so checkout is the only place early enough to set them.
    trial_properties.update(_onboarding_properties(product))
    # Seed the multi-app count from day 0 too. The subscription row for this
    # checkout is already committed above, so it is included in the count.
    trial_properties.update(_owned_app_properties(email))
    _klaviyo_sync(
        email=email,
        name=name,
        properties=trial_properties,
        add_list=KLAVIYO_LIST_TRIAL,
    )

    # Closes out the L2 cart-abandon flow. That flow filters on "has not Placed
    # Order since starting", so without this event every customer who *did*
    # finish still gets the "you didn't finish" email an hour later — the single
    # worst-looking failure in the whole lifecycle programme.
    #
    # Note this is emitted per checkout, not per person: an existing customer
    # buying a second app both starts and completes a new checkout, and the pair
    # has to balance. Filtering on trial-list membership instead would treat
    # them as already-converted and never mail them at all.
    _klaviyo_event(
        metric='Placed Order',
        email=email,
        name=name,
        # Stripe redelivers webhooks; the guard at the top of this handler
        # catches most replays, but the subscription id makes the event itself
        # idempotent rather than relying on that.
        unique_id=subscription_id,
        # price_display is either None or a formatted number, so this cannot
        # raise. Gives Klaviyo the revenue figure behind the L2 recovery KPI.
        value=float(price_display) if price_display else None,
        properties={
            'app_name': product,
            'product': product,
            'company': company or None,
        },
    )

    print(f'[Store API] Subscription created: {product} for {email} (provisioned={all_provisioned})')


# Stripe's `cancellation_details.feedback` enum, rendered as a noun phrase that
# reads correctly inside a sentence — the win-back email says "you mentioned
# {{ reason }}", and "you mentioned too_expensive" is worse than saying nothing.
#
# This is the data half of the L6 intercept the playbook specifies as a page of
# our own. It cannot be a page of our own: cancelling happens inside Stripe's
# hosted billing portal (login.html only opens it via /create-portal-session),
# so there is no moment between the cancel click and the cancellation that our
# frontend owns. Stripe asks the same question natively and hands back the
# answer here.
#
# Nothing populates `feedback` until the cancellation-reason question is turned
# on in the Stripe billing-portal configuration — verified 2026-08-04 against
# the one real cancellation on the live account, which carries
# reason='cancellation_requested' and feedback=None. So today this writes only
# `cancel_mechanism` and no copy-bearing property, which is why the win-back
# email keeps its generic wording and upgrades itself once answers arrive.
_CANCEL_FEEDBACK_PHRASES = {
    'too_expensive':    'the price',
    'missing_features': 'a missing feature',
    'switched_service': 'switching to something else',
    'unused':           'not using it',
    'customer_service': 'the support you got',
    'too_complex':      'it being hard to use',
    'low_quality':      'the quality',
    'other':            None,  # deliberately unmapped; 'other' says nothing usable
}


def _cancel_reason_properties(sub):
    """Cancellation feedback from Stripe's portal, shaped for email copy.

    Returns only the keys that have real values, so a template tag either gets
    something worth printing or falls through to its default. Writing an empty
    string instead would defeat `|default:` and print a blank mid-sentence.
    """
    details = sub.get('cancellation_details') or {}
    props = {}

    feedback = details.get('feedback')
    # `reason` is set by Stripe on every cancellation ('cancellation_requested'
    # when a human asked). It records the mechanism, not a motive, so it is kept
    # for analytics and deliberately never used as email copy.
    if details.get('reason'):
        props['cancel_mechanism'] = details['reason']
    if feedback:
        props['cancel_feedback'] = feedback          # raw enum, for segmenting
        phrase = _CANCEL_FEEDBACK_PHRASES.get(feedback)
        if phrase:
            props['cancel_reason'] = phrase          # prose, for merge tags

    comment = (details.get('comment') or '').strip()
    if comment:
        props['cancel_comment'] = comment
    return props


def _handle_subscription_cancelled(sub):
    subscription_id = sub.get('id', '')
    with get_db() as conn:
        conn.execute(
            'UPDATE subscriptions SET status = ?, cancelled_at = ? WHERE stripe_subscription_id = ?',
            ('cancelled', datetime.utcnow().isoformat(), subscription_id)
        )
        conn.commit()
        row = conn.execute(
            'SELECT email, name, product FROM subscriptions WHERE stripe_subscription_id = ?',
            (subscription_id,)
        ).fetchone()
    print(f'[Store API] Subscription cancelled: {subscription_id}')

    if not (row and row['email']):
        return

    email = row['email']
    cancelled_product = row['product']

    # Recomputed AFTER the status update above, so this is what the customer
    # still pays for — the subscription just cancelled is already excluded.
    remaining = _owned_apps(email)

    properties = {
        # Name the app they actually cancelled. app_name otherwise carries
        # whatever the last checkout happened to write, which for a multi-app
        # customer is the wrong app to put in a "you closed your ___" subject.
        'app_name': cancelled_product,
        'cancelled_app': cancelled_product,
    }
    # Cancelling is the other moment app_count can change, and until now it was
    # only refreshed on the way up. A stale-high count silently suppresses the
    # month-3 expansion pitch for someone who has since dropped back to one app.
    properties.update(_owned_app_properties(email))

    if remaining:
        # Still a customer. Cancelling one app of several must NOT flag the
        # profile cancelled outright — that would pull a paying subscriber into
        # the win-back sequence and strip them off the lists carrying their
        # remaining apps' mail. subscription_status is deliberately left alone
        # rather than rewritten to 'active': the remaining apps may be trialing,
        # and guessing here would replace one wrong answer with another.
        remove_lists = None
    else:
        properties['subscription_status'] = 'cancelled'
        # Last app gone. Off both lifecycle lists.
        #
        # This stops them ENTERING the trial and paid flows. It does NOT, on its
        # own, stop mail to someone already mid-flow — and the day-27 notice is
        # exactly that case, since it sits behind a 24-day delay. Klaviyo only
        # documents the "must still be a member at send time" guarantee for
        # SEGMENTS; a list-triggered flow re-checks nothing unless the flow
        # carries a profile filter.
        #
        # So a trial cancelled on day 10 used to still get "your card is charged
        # on [date]" on day 27. The fix is NOT more code here: it is the
        # flow-level profile filter added to PF9 Trial Onboarding (X2tesT) on
        # 2026-08-02, which reads
        #     subscription_status not-equals 'cancelled' OR subscription_status not-set
        # (one condition_group, so OR). That filter is what makes the
        # subscription_status write above load-bearing — it is the only thing
        # the flow inspects to decide whether to keep sending, so changing that
        # value's spelling here silently disarms the guard.
        # See LIFECYCLE_STATUS.md, "Day-27 filter — 2026-08-02".
        remove_lists = [KLAVIYO_LIST_TRIAL, KLAVIYO_LIST_PAID]

    _klaviyo_sync(
        email=email,
        name=row['name'],
        properties=properties,
        remove_list=remove_lists,
    )

    cancel_properties = {
        'app_name': cancelled_product,
        'product': cancelled_product,
        # Lets the flow drop someone who cancelled one app of several. They
        # have not churned, and win-back copy addressed to a current
        # customer reads as if we do not know who they are.
        'remaining_app_count': len(remaining),
        'reactivate_link': f'{STORE_URL}/?product={cancelled_product}',
    }
    # Empty until the portal's cancellation-reason question is enabled, so this
    # adds nothing today and needs no flow change to start working later.
    cancel_properties.update(_cancel_reason_properties(sub))

    # The trigger for L6 churn-save and L7 win-back. Writing a profile property
    # does not start a Klaviyo flow — only a list join, a segment join, or a
    # metric does — so without this event those sequences have nothing to hang
    # off, however good the data on the profile is.
    _klaviyo_event(
        metric='Cancelled Subscription',
        email=email,
        name=row['name'],
        unique_id=subscription_id,
        properties=cancel_properties,
    )


def _handle_subscription_updated(sub):
    subscription_id = sub.get('id', '')
    status = sub.get('status', '')
    te = sub.get('trial_end')
    trial_end_iso = datetime.utcfromtimestamp(int(te)).isoformat() if te else None
    with get_db() as conn:
        previous = conn.execute(
            'SELECT status, email, name, product FROM subscriptions WHERE stripe_subscription_id = ?',
            (subscription_id,)
        ).fetchone()
        conn.execute(
            'UPDATE subscriptions SET status = ?, trial_end = ? WHERE stripe_subscription_id = ?',
            (status, trial_end_iso, subscription_id)
        )
        conn.commit()
    print(f'[Store API] Subscription {subscription_id} status -> {status}')

    # trialing -> active is the day-30 conversion: hand them off from the trial
    # flow to paid onboarding. Guarded on the previous status so the repeated
    # 'active' updates Stripe sends on every renewal don't re-trigger it.
    if (
        previous
        and previous['email']
        and previous['status'] == 'trialing'
        and status == 'active'
    ):
        properties = {'app_name': previous['product'], 'subscription_status': 'active'}
        # The month-3 expansion email renders related_app_* off the profile.
        # Set it here as well as at checkout so a profile that predates the
        # checkout-side mapping still gets it on conversion.
        properties.update(_cross_sell_properties(previous['product']))
        # Paid Month 1 reads add_team_url. Re-set both links here rather than
        # relying on the checkout-side write: a customer converting a SECOND app
        # has app_name overwritten to the new product above, and leaving
        # app_login_url pointing at the first app would send them to the wrong
        # login from an email that names the new one.
        properties.update(_app_link_properties(previous['product']))
        # Paid Month 1 reads month1_feature_*. Re-set on conversion for the same
        # reason as the links: a customer converting a second app needs the copy
        # to match the app_name written just above, not the one they trialed first.
        properties.update(_onboarding_properties(previous['product']))
        # Refresh the multi-app count that the month-3 conditional split reads.
        # This is the moment it can change: converting a second app is what
        # turns a single-app customer into someone who should NOT be pitched an
        # expansion. Note app_name above is overwritten with the newest product,
        # so it carries no history — app_count is the only multi-app signal.
        properties.update(_owned_app_properties(previous['email']))
        _klaviyo_sync(
            email=previous['email'],
            name=previous['name'],
            properties=properties,
            add_list=KLAVIYO_LIST_PAID,
            remove_list=KLAVIYO_LIST_TRIAL,
        )


def _handle_trial_will_end(sub):
    """Stripe fires this 3 days before a trial ends — day 27 of a 30-day trial.

    Sends the pre-charge notice, and refreshes the billing date in Klaviyo so
    anything else keyed off the profile still agrees with Stripe.

    The send lives here rather than in Klaviyo (where it lived until
    2026-08-04) because it is a billing notice, not marketing. The Klaviyo path
    could only reach a profile with marketing consent, so a customer who
    declined the checkout tick — or later unsubscribed — would have been
    charged with no warning at all. Marking the Klaviyo message transactional
    would have fixed that, but it needs a paid plan, a metric-triggered flow and
    Klaviyo's approval, none of which apply here. Stripe's own trial reminder is
    not a substitute either: it fires at 7 days, not 3.

    Fail-soft on everything except the send, which is the point of the handler.
    """
    subscription_id = sub.get('id', '')
    te = sub.get('trial_end')
    trial_end_iso = datetime.utcfromtimestamp(int(te)).isoformat() if te else None
    trial_end_display = _format_trial_end(trial_end_iso)
    price_display = _trial_price_display(sub)

    # Look up who this is from our own records (avoids an extra Stripe call).
    row = None
    with get_db() as conn:
        if trial_end_iso:
            conn.execute(
                'UPDATE subscriptions SET trial_end = ? WHERE stripe_subscription_id = ?',
                (trial_end_iso, subscription_id)
            )
            conn.commit()
        row = conn.execute(
            'SELECT email, name, product, status FROM subscriptions '
            'WHERE stripe_subscription_id = ?',
            (subscription_id,)
        ).fetchone()

    print(f'[Store API] Trial ending soon for {subscription_id} (ends {trial_end_iso})')
    if not row or not row['email']:
        print(f'[Store API] No local record for {subscription_id}; cannot send pre-charge notice')
        return

    _klaviyo_sync(
        email=row['email'],
        name=row['name'],
        properties={
            'app_name': row['product'],
            'trial_end_date': trial_end_display,
        },
    )

    # A trial that won't convert must not be told its card is about to be
    # charged. Read cancellation off the Stripe object, not our status column:
    # a customer who cancels during the trial via the billing portal gets
    # cancel_at_period_end=True and arrives here as a `customer.subscription
    # .updated`, which leaves our status at 'trialing'. Checking only the DB
    # would send them a false charge notice.
    if sub.get('cancel_at_period_end') or sub.get('canceled_at') or row['status'] == 'cancelled':
        print(f'[Store API] {subscription_id} is cancelling; no pre-charge notice')
        return

    # Refuse to send a billing notice that cannot name the amount or the date.
    # Silence is recoverable; a notice reading "charged $None" is not.
    if not price_display or not trial_end_display:
        print(
            f'[Store API] ALERT: cannot build pre-charge notice for {subscription_id} '
            f'(price={price_display!r}, date={trial_end_display!r}) — not sending'
        )
        try:
            _send_email(
                EMAIL_FROM_INTERNAL, NOTIFY_EMAIL,
                f'[PF9 Store] Pre-charge notice NOT sent — {subscription_id}',
                f'<p>{html.escape(row["email"])} is charged in 3 days and could not be told.</p>'
                f'<p>price={html.escape(str(price_display))}, '
                f'date={html.escape(str(trial_end_display))}</p>'
            )
        except Exception as e:
            print(f'[Store API] Pre-charge alert error: {e}')
        return

    # Claim the send before making it. Stripe retries webhooks on any non-2xx,
    # and gunicorn runs two workers, so without an atomic claim a retry or a
    # concurrent delivery would email the customer twice. Claiming on the
    # trial_end being notified about — rather than a bare "sent" flag — means a
    # retry for the same date is suppressed while a genuinely new date (an
    # extended trial) is allowed through. rowcount 0 = someone else has it.
    with get_db() as conn:
        claimed = conn.execute(
            'UPDATE subscriptions SET trial_notice_sent_for = ? '
            'WHERE stripe_subscription_id = ? '
            '  AND (trial_notice_sent_for IS NULL OR trial_notice_sent_for <> ?)',
            (trial_end_iso, subscription_id, trial_end_iso)
        ).rowcount
        conn.commit()

    if not claimed:
        print(f'[Store API] Pre-charge notice already sent for {subscription_id}; skipping')
        return

    try:
        sent = _send_trial_ending_email(
            email=row['email'],
            name=row['name'],
            product=row['product'],
            price_display=price_display,
            trial_end_display=trial_end_display,
        )
    except Exception as e:
        print(f'[Store API] Pre-charge notice error for {subscription_id}: {e}')
        sent = False

    if not sent:
        # Release the claim so Stripe's retry gets a real second attempt. Worst
        # case this ends in a duplicate; for a billing warning that is the
        # better failure than never arriving.
        with get_db() as conn:
            conn.execute(
                'UPDATE subscriptions SET trial_notice_sent_for = NULL '
                'WHERE stripe_subscription_id = ?',
                (subscription_id,)
            )
            conn.commit()
        print(f'[Store API] ALERT: pre-charge notice FAILED for {row["email"]} ({subscription_id})')


def _handle_payment_failed(invoice):
    subscription_id = invoice.get('subscription', '')
    customer_email = invoice.get('customer_email', '') or ''
    attempt_count = invoice.get('attempt_count', 0)
    if not subscription_id:
        return
    with get_db() as conn:
        conn.execute(
            'UPDATE subscriptions SET status = ? WHERE stripe_subscription_id = ?',
            ('past_due', subscription_id)
        )
        conn.commit()
    print(f'[Store API] Payment failed for {subscription_id} (attempt {attempt_count}, {customer_email})')
    try:
        _send_payment_failed_alert(subscription_id, customer_email, attempt_count)
    except Exception as e:
        print(f'[Store API] Payment-failed alert error: {e}')


def _send_payment_failed_alert(subscription_id, customer_email, attempt_count):
    if not NOTIFY_EMAIL:
        return
    body = f"""
    <div style="font-family: sans-serif;">
        <h3>Stripe payment failed</h3>
        <p><b>Subscription:</b> {html.escape(subscription_id)}</p>
        <p><b>Customer:</b> {html.escape(customer_email) if customer_email else '(unknown)'}</p>
        <p><b>Attempt:</b> {attempt_count}</p>
        <p>Subscription marked <code>past_due</code> in store DB.</p>
    </div>
    """
    _send_email(EMAIL_FROM_INTERNAL, NOTIFY_EMAIL, f'[PF9 Store] Payment failed — {customer_email or subscription_id}', body)


def _send_provisioning_alert(email, product, results, subscription_id):
    """Tell someone when a paid customer did not get their account.

    This is the gap that let broken provisioning run unnoticed: the failure is
    soft by design (the customer is charged, gets a softened welcome email, and
    nothing else happens), so with no alert there was no signal at all. Every
    other money-affecting failure here already emails NOTIFY_EMAIL.
    """
    if not NOTIFY_EMAIL:
        print('[Store API] NOTIFY_EMAIL not set, skipping provisioning alert')
        return
    rows = ''
    for p, r in results.items():
        ok = (r == 'ok')
        colour = '#0a7d28' if ok else ('#b26a00' if r == 'exists' else '#c00')
        rows += (f'<tr><td style="padding:6px; font-weight:bold;">{html.escape(p)}</td>'
                 f'<td style="padding:6px; color:{colour};">{html.escape(str(r))}</td></tr>\n')
    body = f"""
    <div style="font-family: sans-serif;">
        <h3>Provisioning incomplete — customer paid</h3>
        <p><b>Customer:</b> {html.escape(email)}</p>
        <p><b>Purchased:</b> {html.escape(product)}</p>
        <p><b>Subscription:</b> {html.escape(subscription_id or '(unknown)')}</p>
        <table style="border-collapse:collapse;">{rows}</table>
        <p>The welcome email was sent without login details. The temp password is
        still in the <code>subscriptions</code> row for this subscription — create
        the account manually with it, or reset and send new credentials.</p>
    </div>
    """
    _send_email(EMAIL_FROM_INTERNAL, NOTIFY_EMAIL,
                f'[PF9 Store] Provisioning failed — {email} ({product})', body)


def _provision_account(product, email, name, company, password):
    """Create the customer's account in one app.

    Returns 'ok', 'exists', or a short failure reason. 'exists' is deliberately
    not 'ok': the account is usable, but it keeps whatever password it already
    had, so the temp password in the welcome email would not work.
    """
    register_url = _register_url(product)
    if not register_url:
        print(f'[Store API] No register URL for {product} (skipping provisioning)')
        return 'no register url configured'

    # Every app's register handler was read to confirm this: all of them take
    # organizationName except INSPECTR, which takes companyName, and several
    # accept either. Sending both keys covers all of them with one payload —
    # the Next.js apps parse with a non-strict zod schema and the Flask apps
    # read named keys, so in both cases the unused one is ignored rather than
    # rejected. (An earlier read of a 400 on an empty body suggested COMPLI
    # needed org_name; its source shows it already aliases organizationName.)
    org = company or name or email.split('@')[0]
    payload = {
        'email': email,
        'name': name or email.split('@')[0],
        'password': password,
        'organizationName': org,
        'companyName': org,
    }

    # Identify ourselves rather than riding the default 'python-requests/x.y.z'.
    # A Cloudflare rule on these zones returns 403 (error 1010) to some scripted
    # user agents — 'Python-urllib/3.11' is blocked outright, measured. The
    # requests default happens to pass today, but provisioning is a revenue path
    # and should not depend on a third-party library's UA string staying off
    # someone's blocklist.
    headers = {'User-Agent': 'PF9-Store/1.0'}

    # FLOWTRACK keeps public registration closed in production, so the only way
    # to fulfil a paid FLOWTRACK subscription is to present this shared secret.
    # Sent to every app: the others ignore an unknown header, and hardcoding
    # "only FLOWTRACK gets it" would just be another per-product special case to
    # forget about the next time an app closes its signup.
    if PROVISION_SECRET:
        headers['X-PF9-Provision-Secret'] = PROVISION_SECRET

    # Two attempts: this now crosses the network, and losing the one shot at
    # provisioning to a transient blip means a paying customer with no account.
    last = 'unknown error'
    for attempt in (1, 2):
        try:
            resp = http_requests.post(register_url, json=payload, headers=headers, timeout=20)
            if resp.status_code in (200, 201):
                print(f'[Store API] Provisioned {product} account for {email}')
                return 'ok'
            if resp.status_code == 409:
                print(f'[Store API] {product} account already exists for {email}')
                return 'exists'
            last = f'HTTP {resp.status_code} {resp.text[:200]}'
            # 4xx is the app telling us the request is wrong; retrying is pointless.
            if 400 <= resp.status_code < 500:
                break
        except Exception as e:
            last = str(e)
        if attempt == 1:
            time.sleep(2)

    print(f'[Store API] Provisioning failed for {product} ({email}): {last}')
    return last


# ── Email Helpers ──
def _send_notification(name, company, email, message, product):
    if not NOTIFY_EMAIL:
        print('[Store API] NOTIFY_EMAIL not set, skipping notification')
        return
    e_name    = html.escape(name)
    e_company = html.escape(company) if company else '—'
    e_email   = html.escape(email)
    e_message = html.escape(message) if message else '—'
    e_product = html.escape(product)
    body = f"""
    <div style="font-family: sans-serif; max-width: 600px;">
        <h2 style="color: #111;">New Demo Request</h2>
        <table style="width:100%; border-collapse:collapse;">
            <tr><td style="padding:8px; font-weight:bold; width:120px;">Product</td><td style="padding:8px;">{e_product}</td></tr>
            <tr style="background:#f9f9f9"><td style="padding:8px; font-weight:bold;">Name</td><td style="padding:8px;">{e_name}</td></tr>
            <tr><td style="padding:8px; font-weight:bold;">Company</td><td style="padding:8px;">{e_company}</td></tr>
            <tr style="background:#f9f9f9"><td style="padding:8px; font-weight:bold;">Email</td><td style="padding:8px;"><a href="mailto:{e_email}">{e_email}</a></td></tr>
            <tr><td style="padding:8px; font-weight:bold; vertical-align:top;">Message</td><td style="padding:8px;">{e_message}</td></tr>
        </table>
        <p style="color:#888; font-size:12px; margin-top:24px;">Plainspoken Foundry Nine · store.plainspokenfoundrynine.com</p>
    </div>
    """
    if _send_email(EMAIL_FROM_INTERNAL, NOTIFY_EMAIL, f'[PF9 Store] New demo request — {product}', body):
        print(f'[Store API] Notification sent for {email}')


def _send_welcome_email(email, name, product, password, provisioned):
    first_name = html.escape(name.split()[0]) if name else 'there'
    e_email = html.escape(email)
    e_password = html.escape(password)
    bundle_products = BUNDLE_MAP.get(product)

    if bundle_products:
        subject = f'Welcome to your Property Bundle — Your accounts are ready!'
        login_rows = ''
        for bp in bundle_products:
            bp_url = APP_URL_MAP.get(bp, STORE_URL)
            login_rows += f'<tr><td style="padding:8px; font-weight:bold;">{html.escape(bp)}</td><td style="padding:8px;"><a href="{bp_url}">{bp_url}</a></td></tr>\n'
        if provisioned:
            login_section = f"""
            {login_rows}
            <tr style="background:#f9f9f9"><td style="padding:8px; font-weight:bold;">Email</td><td style="padding:8px;">{e_email}</td></tr>
            <tr><td style="padding:8px; font-weight:bold;">Temporary Password</td><td style="padding:8px; font-family:monospace; font-size:16px;">{e_password}</td></tr>
            <tr><td style="padding:8px; font-size:12px; color:#666;" colspan="2">Same login for both apps.</td></tr>
            """
        else:
            login_section = '<tr><td style="padding:8px;" colspan="2">Your accounts are being set up. We\'ll send your login details shortly.</td></tr>'
        product_label = 'Property Bundle (LANDLORDR + TENANTLINK)'
    else:
        subject = f'Welcome to {product} — Your account is ready!'
        app_url = APP_URL_MAP.get(product, STORE_URL)
        if provisioned:
            login_section = f"""
            <tr><td style="padding:8px; font-weight:bold;">Login URL</td><td style="padding:8px;"><a href="{app_url}">{app_url}</a></td></tr>
            <tr style="background:#f9f9f9"><td style="padding:8px; font-weight:bold;">Email</td><td style="padding:8px;">{e_email}</td></tr>
            <tr><td style="padding:8px; font-weight:bold;">Temporary Password</td><td style="padding:8px; font-family:monospace; font-size:16px;">{e_password}</td></tr>
            """
        else:
            login_section = '<tr><td style="padding:8px;" colspan="2">Your account is being set up. We\'ll send your login details shortly.</td></tr>'
        product_label = html.escape(product)

    body = f"""
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
    if _send_email(EMAIL_FROM_CUSTOMER, email, subject, body):
        print(f'[Store API] Welcome email sent to {email}')


def _send_trial_ending_email(email, name, product, price_display, trial_end_display):
    """The day-27 pre-charge notice. Returns True only if Resend accepted it.

    Copy is ported from Klaviyo template TGNJvL so the wording the customer gets
    is the wording that was written and reviewed. The difference is delivery:
    this goes out on the `customer.subscription.trial_will_end` webhook, which
    is billing infrastructure, so it does not depend on marketing consent and
    reaches customers who never ticked the box. See _handle_trial_will_end.

    Both price_display and trial_end_display are required. A billing notice that
    cannot state the amount or the date is worse than no notice, so the caller
    checks for them before getting here.
    """
    first_name = html.escape(name.split()[0]) if name else 'there'
    bundle_products = BUNDLE_MAP.get(product)
    # `product` reaches us from checkout metadata, so escape it for the HTML
    # body. The subject is plain text and takes the raw label — escaping there
    # would show a literal '&amp;' in the inbox.
    plain_label = 'Property Bundle' if bundle_products else product
    app_label = html.escape(plain_label)
    e_price = html.escape(str(price_display))
    e_date = html.escape(str(trial_end_display))
    manage_url = f'{STORE_URL}/login.html'

    subject = f'Your {plain_label} trial ends {trial_end_display}'
    body = f"""
    <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,sans-serif; max-width:600px; color:#1a1a1a;">
        <p style="font-size:12px; font-weight:700; letter-spacing:0.08em; text-transform:uppercase; margin:0 0 24px;">Plainspoken Foundry Nine</p>
        <p style="font-size:15px; line-height:1.65;">Hi {first_name},</p>
        <p style="font-size:15px; line-height:1.65;">Your {app_label} trial ends on <strong>{e_date}</strong>. Here's exactly what happens:</p>
        <div style="border:1px solid #1a1a1a; border-radius:4px; padding:16px 20px; margin:20px 0;">
            <p style="margin:0; font-size:15px; line-height:1.6;"><strong>Your card is charged ${e_price} on {e_date}</strong>, then monthly after that. It's the card you entered at checkout.</p>
        </div>
        <table style="width:100%; border-collapse:collapse; border:1px solid #e8e8e8; margin:20px 0; font-size:14px; line-height:1.5;">
            <tr><td style="padding:14px 20px; border-bottom:1px solid #f0f0f0;"><strong>Nothing changes in the app.</strong> Everything you've set up stays exactly as it is.</td></tr>
            <tr><td style="padding:14px 20px; border-bottom:1px solid #f0f0f0;"><strong>Flat pricing.</strong> ${e_price}/mo, unlimited users — adding your team doesn't change the bill.</td></tr>
            <tr><td style="padding:14px 20px;"><strong>Cancel any time</strong>, including before {e_date} if you'd rather not continue. Takes about 15 seconds, and you won't be charged.</td></tr>
        </table>
        <p style="font-size:15px; line-height:1.65;">You don't need to do anything to keep going.</p>
        <p><a href="{manage_url}" style="display:inline-block; background:#1a1a1a; color:#fff; text-decoration:none; padding:12px 24px; border-radius:4px; font-size:14px; font-weight:600;">Manage your subscription →</a></p>
        <p style="font-size:15px; line-height:1.65;">Questions about pricing or adding more apps? Reply here — I read this inbox.</p>
        <p style="font-size:15px; line-height:1.65;">Mark</p>
        <hr style="border:none; border-top:1px solid #e8e8e8; margin:24px 0;"/>
        <p style="font-size:13px; color:#888; margin:0;">This is a billing notice about your {app_label} subscription, sent because your trial is ending. It isn't marketing, and there's nothing to unsubscribe from — it stops when your subscription does.</p>
    </div>
    """
    sent = _send_email(EMAIL_FROM_CUSTOMER, email, subject, body)
    if sent:
        print(f'[Store API] Trial-ending email sent to {email} (charges {trial_end_display})')
    return sent


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
