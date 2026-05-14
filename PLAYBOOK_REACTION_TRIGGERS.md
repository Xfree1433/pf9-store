# PF9 Reaction Triggers Setup

**What this is:** the alerts that automatically pull you back to the project when something real happens. No timed reminders — only event-driven notifications.

**Time to set up everything below:** ~20 minutes one-time. Then alerts run forever.

**Already in place** (don't redo):
- `store_api.py` already emails `NOTIFY_EMAIL` env var on every Stripe `checkout.session.completed` event. **First sale alert is live.** Check `/opt/bridgr/.env` to confirm `NOTIFY_EMAIL=` is set to your address.

---

## 1. GA4 — Custom traffic alerts (5 min)

Triggers you to react to traffic spikes (HN landing) or conversion drops (T2 guardrail breach).

**Setup:**

1. GA4 → **Admin** (gear icon, bottom-left)
2. Property column → **Custom insights**
3. Click **Create**
4. Create these 4 alerts:

### Alert A: Traffic spike (HN / Product Hunt landing)
- **Insight name:** "Traffic spike — investigate source"
- **Evaluation frequency:** Daily
- **Audience:** All users
- **Metric:** Active users
- **Condition:** % change vs same day previous week > 200%
- **Send email to:** your email

### Alert B: video_play drop (T2 guardrail)
- **Insight name:** "video_play dropped — check funnel"
- **Evaluation frequency:** Daily
- **Metric:** Event count where event_name = `video_play`
- **Condition:** % change vs same day previous week < -25%
- **Send email to:** your email

### Alert C: subscribe_modal_open drop (T2 guardrail)
- **Insight name:** "Subscribe modal opens dropped"
- **Evaluation frequency:** Daily
- **Metric:** Event count where event_name = `subscribe_modal_open`
- **Condition:** % change vs same day previous week < -25%
- **Send email to:** your email

### Alert D: First conversion (motivation)
- **Insight name:** "🎉 First purchase event"
- **Evaluation frequency:** Daily
- **Metric:** Event count where event_name = `purchase`
- **Condition:** Value > 0 (first time triggering)
- **Send email to:** your email

**Expected behavior:** A, B, C only fire when something abnormal happens. D fires the day of your first paid subscription — pair with the existing Stripe email for double confirmation.

---

## 2. HubSpot — New contact notifications (3 min)

Fires when a lead lands in any of your 3 active lists. Tells you to log in and look.

**Setup:**

1. HubSpot → **Settings (gear)** → **Notifications**
2. Click **Email notifications**
3. Toggle on:
   - **Contacts → Contact added to list** for lists 12, 13, 14
4. Save

**Expected behavior:** every time the calculator, contact form, lead magnet, modal, or Stripe webhook adds a contact to a list, you get an email within 30 seconds. Low frequency early on; will pick up after HN/paid launches.

---

## 3. Stripe — Sale alerts (1 min)

The most motivating alert. Stripe sends an email on every charge by default; this confirms it's enabled and pointed at the right address.

**Verify:**

1. Stripe Dashboard → **Settings (gear)** → **Notifications**
2. Confirm **Successful payment** is checked
3. Confirm the email address listed is one you actually read
4. (Optional) Also enable **Disputes** and **Failed payments**

**Expected behavior:** the first time a real customer subscribes, Stripe and `store_api.py` both send you emails within seconds. You'll know.

---

## 4. Google Search Console — Indexing & coverage alerts (1 min)

Tells you when Google has indexing problems or surfaces a manual action.

**Setup:**

1. GSC → **Settings (gear, bottom-left)** → **Users and permissions**
2. Confirm your email is listed as Owner
3. **Settings** → **Email preferences** → toggle on:
   - **Performance** alerts (significant change in performance)
   - **Coverage** alerts (new indexing issues)
   - **Manual actions** (in the unlikely event Google penalizes you)
4. Save

**Expected behavior:** monthly digest at minimum; immediate alert on coverage issues. Pulls you back when GSC has news.

---

## 5. Google Alerts — Brand mentions (1 min)

Tells you when journalists, bloggers, competitors, or customers mention PF9 anywhere on the indexed web.

**Setup:**

1. Open https://www.google.com/alerts
2. Create alerts for each of these terms:
   - `"Plainspoken Foundry Nine"`
   - `"plainspokenfoundrynine"`
   - `"PF9 software"` (the unqualified "PF9" is too noisy)
   - `"plainspokenfoundrynine.com"`
3. Set frequency to **As-it-happens**
4. Set sources to **All sources** and language to **English**

**Expected behavior:** every blog post, forum mention, news article, or anywhere your brand surfaces on Google's crawler. You'll see HN, Reddit, Product Hunt mentions within minutes-to-hours of publication.

---

## 6. YouTube — Subscriber + comment notifications (1 min)

Tells you when channel activity picks up. Mostly for awareness; not action-critical.

**Setup:**

1. YouTube Studio → **Settings (gear, bottom-left)** → **Notifications**
2. Toggle on:
   - Comments and replies
   - New subscribers
   - (Skip) Channel feedback summaries (too noisy)
3. Save

**Expected behavior:** sparse for now. Picks up after HN drives YouTube traffic and the channel SEO work gets indexed.

---

## 7. Cowork — Agent activity alerts (when agents are live)

Not applicable yet — no agents running. When you stand up the Lifecycle agent (`AGENTS.md` Agent 4), set its approval queue to email you. Already covered in `AGENTS.md` § Agent 4 setup.

---

## Summary: the email noise you'll see going forward

After all alerts are set up, you'll get:

| Frequency | Source | Action when it fires |
|---|---|---|
| **Rare (months)** | T2 guardrail breach (Alert B/C) | Open `PLAYBOOK_CRO.md` § T2, evaluate revert |
| **Rare (first occurrence)** | First sale (Stripe + GA4 D + `store_api.py`) | Celebrate. Reply to the customer personally. |
| **Per HN/PH wave** | Traffic spike (Alert A) | Open GA4 → Realtime, watch the wave. Engage in HN/PH comments. |
| **Per lead** | HubSpot list add | Open HubSpot, look at the contact, decide if manual follow-up makes sense (most weeks: yes, while volume is low) |
| **Per brand mention** | Google Alerts | Open the link, decide if it warrants a reply or share |
| **Monthly** | GSC performance digest | Read the search-query trends; update tags/copy if a new pattern appears |

**Expected baseline volume after launch:** maybe 5–15 alerts per week initially. Manageable.

---

## What I (the agent) can do later

- Add a daily/weekly aggregate email from `store_api.py` if the individual alerts become overwhelming (combines new contacts + Stripe activity + key GA4 numbers into one digest)
- Write a "weekly Friday review" template if you want to formalize the review cadence
- Add Slack webhook integration if you want alerts in a channel instead of email

## What I cannot do from this session

- Toggle these alerts on for you — every one requires logging into the respective service
- Set a "remind me in N days" reminder that persists across sessions — the harness doesn't have that capability
