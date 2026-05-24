# PF9 Lifecycle Agent Activation Guide

**What this is:** the complete, paste-ready package to stand up the Cowork Lifecycle agent (Agent 4 from `AGENTS.md`). Work through it in the Cowork UI. Budget ~45 min to configure + 48h dry-run before it sends anything real.

**Prerequisite reality check first** — see § 0.

---

## § 0. Should you turn this on yet?

The deferred trigger in `memory.md` was: **10+ non-subscriber leads/week for 2 consecutive weeks.** Gut-check before proceeding:

- Open HubSpot → Contacts → filter by "Create date is in the last 7 days" AND not in list 14 (subscribers).
- Count them.

**If under ~10/week:** the agent is overkill — manually emailing each lead as the founder converts higher and is faster than configuring + monitoring the agent. Bookmark this guide and come back when volume justifies it.

**If 10+/week:** proceed. The 48h dry-run (§ 6) is the safety net — the agent drafts but doesn't send until you've reviewed the output.

You chose to proceed, so the rest of this assumes go.

---

## § 1. Architecture — who does what

```
┌─────────────┐   new contact / status change   ┌──────────────────┐
│  HubSpot    │ ───────────────────────────────▶ │  Cowork           │
│  (state)    │ ◀─────────────────────────────── │  Lifecycle agent  │
│             │   enroll / tag / update           │  (the brain)      │
└─────────────┘                                    └──────────────────┘
      ▲                                                  │
      │ contacts pushed by store_api.py                  │ draft email
      │ (calculators, modal, lead magnets,               ▼
      │  contact form, Stripe webhook)            ┌──────────────────┐
      │                                            │  Approval queue   │
      │                                            │  (you, via email  │
      │                                            │   or Slack)       │
      │                                            └──────────────────┘
      │                                                  │ approved
      │                                                  ▼
      │                                            ┌──────────────────┐
      └────────────────────────────────────────── │  Resend (send)   │
                  email sent, logged back           └──────────────────┘
```

**Key design decisions:**
- **Trigger source is HubSpot, not GA4.** Anonymous `video_play` events have no email — can't act on them. The agent acts on HubSpot contacts, which are real, identified people (calculator leads, modal captures, lead-magnet downloads, subscribers).
- **Resend is the send transport.** Already wired (`RESEND_API_KEY`), no new vendor, no new cost. The agent orchestrates sequencing/timing; Resend just sends.
- **HubSpot is the state store.** Enrollment status, which sequence a contact is in, what's been sent — all tracked as HubSpot contact properties.

---

## § 2. ESP decision

**Recommended for v1: Resend** (already wired). The Cowork agent calls Resend's send API for each sequence email; the agent itself handles scheduling, dedup, and stop-on-reply logic.

| Option | Cost | When to pick |
|---|---|---|
| **Resend** (recommended) | $0 (already set up) | v1, low volume. Agent drives sequencing. Resend handles deliverability + the send. |
| Loops | ~$49/mo | If you want native visual sequence builders + better deliverability analytics at scale |
| Customer.io | $$$ | Overkill until thousands of contacts |
| HubSpot Marketing email | Free tier limited | Workflow automation gated on free tier — not reliable for sequences yet |

Stick with Resend unless deliverability becomes a measurable problem. Revisit at 500+ active contacts.

---

## § 3. Prerequisite confirmation

Before configuring the agent, confirm all of these (most already done):

- [x] HubSpot live, contacts flowing (lists 12/13/14) — confirmed
- [x] Resend wired (`RESEND_API_KEY` in `/opt/bridgr/.env`) — confirmed
- [x] Stripe webhooks firing — confirmed
- [x] `video_play`, `subscribe_modal_open`, `checkout_started`, `purchase` events live — confirmed
- [ ] **A Resend "from" domain verified** for marketing sends (e.g., `hello@plainspokenfoundrynine.com`). Transactional uses `welcome@`; consider a separate `hello@` or `kennedy@` for lifecycle so a spam complaint on marketing doesn't poison transactional deliverability. Set up in Resend → Domains.
- [ ] **Decide the approval-queue destination** — your email (`mark.pierce@outlook.com`) or a Slack channel.

---

## § 4. Create the agent in Cowork

### 4a. System prompt

Copy the entire **"Agent 4 — Lifecycle Agent"** section from `AGENTS.md` (between the `---` delimiters) into Cowork's system-prompt field.

### 4b. Knowledge base — attach these files

- `PLAYBOOK_LIFECYCLE.md` (primary — the 7 sequences L1–L7)
- `SALES_PLAN.md` (§4 messaging guardrails, §6 sales motion)
- `MARKETING.md` (voice/tone reference + copy bank)

Use GitHub raw URLs if Cowork pulls from links, or paste contents directly.

### 4c. Tool connections

| Tool | Permission | Used for |
|---|---|---|
| **HubSpot** | Read + write contacts, read/write lists, read/write contact properties | Enroll contacts, track sequence state, stop on reply |
| **Resend** | Send | Transport for sequence emails |
| **Stripe** | Read-only | Detect new subscriptions (L3 trigger) and cancellations (L6/L7) |
| **Approval queue** | — | Route drafts to your email/Slack |

### 4d. Approval-queue rules (critical)

Set these in the agent config so it doesn't blast contacts:

- **First-time sequence launch:** all emails in the sequence reviewed together before any send.
- **Established sequence, new enrollee:** auto-send per the approved template (per-contact approval doesn't scale).
- **Template edit:** re-approval required; freeze the sequence for new enrollees until approved.
- **Any send to >50 recipients in one trigger:** flag for human approval regardless.

---

## § 5. HubSpot contact-property setup (10 min)

The agent needs custom properties to track sequence state. Create these in HubSpot → Settings → Properties → Create property (object type: Contact):

| Property name | Type | Purpose |
|---|---|---|
| `pf9_sequence` | Single-line text | Which sequence the contact is in (L1, L3, etc.) |
| `pf9_sequence_step` | Number | Which email in the sequence was last sent (0, 1, 2...) |
| `pf9_last_email_at` | Date picker | Timestamp of last lifecycle email |
| `pf9_sequence_status` | Dropdown (active / completed / stopped / replied) | Enrollment status |

The agent reads/writes these to know who's where in which sequence and to stop on reply.

---

## § 6. Dry-run protocol (48 hours)

**Do NOT enable sending yet.** Configure the agent in draft-only mode:

1. Set Resend tool to **draft-only** (or disable the send permission temporarily — the agent will compose but not send).
2. Let the agent run against real HubSpot contacts for 48 hours.
3. Review every draft it produces in the approval queue:
   - Is the right contact getting the right sequence? (lead → L1, subscriber → L3)
   - Is the copy correct, in founder voice, no broken merge fields?
   - Are stop-on-reply and dedup working? (no contact getting two emails for the same step)
4. If drafts look right after 48h → proceed to § 7. If not → fix config, restart the 48h clock.

---

## § 7. Go live — L3 first, then L1

**Start with L3 (onboarding), not L1.** L3 only fires on real new subscribers — the lowest-risk, highest-value sequence. A botched onboarding email to a paying customer is recoverable; a botched blast to 200 cold leads is not.

1. Enable Resend send for **L3 only** (onboarding sequence from `PLAYBOOK_LIFECYCLE.md`).
2. Approve the L3 template set (4 emails: immediate welcome, day-3 activation, day-7 check-in, day-14 expansion).
3. Watch the next real subscription flow through. Confirm the welcome email from the agent doesn't collide with the existing `store_api.py` transactional welcome email — **coordinate these.** If `store_api.py` already sends a welcome, the agent's L3-E1 should be a *different* email (e.g., the day-3 activation nudge becomes L3's first send, and store_api keeps the immediate welcome).
4. Once L3 is clean for ~1 week, enable **L1** (video-viewer / lead nurture). This is the higher-volume, higher-risk sequence — only turn it on after L3 has proven the plumbing.

**Important collision check:** `store_api.py` `_send_welcome_email()` already fires on `checkout.session.completed`. Don't duplicate it. Either:
- (a) Let store_api keep the immediate welcome, and have the agent's L3 start at day 3, OR
- (b) Disable store_api's welcome and let the agent own the entire L3 sequence including the immediate welcome.

Option (a) is safer — the transactional welcome (with login credentials) should stay in store_api where it's reliable. The agent handles the *marketing* follow-ups.

---

## § 8. What to watch (first 2 weeks)

Per-sequence KPIs from `PLAYBOOK_LIFECYCLE.md`:

| Sequence | Watch | Kill/fix threshold |
|---|---|---|
| L3 onboarding | Open rate, day-7 activation % | Open <30% after 20 sends → rewrite |
| L1 nurture | Open rate, click rate, subscribe conversion | Open <30% or unsub >1% after 500 sends → halt |

Also watch:
- **Resend deliverability** (bounce rate, spam complaints) in the Resend dashboard. Spam rate >0.1% → pause and investigate.
- **Approval queue latency** — if you're not reviewing drafts within a day, the agent backs up.

---

## § 9. Escalate to a human (the agent should never auto-handle)

Per `AGENTS.md` § Human checkpoints — these route to you, no auto-action:
- Any reply mentioning refund, legal, dispute, chargeback
- Any reply from a >$399/mo prospect (bundle deal — founder-assisted)
- Any cancellation reply
- Any press/analyst/partnership inquiry

---

## § 10. Rollout sequence reminder

Per `AGENTS.md` § Rollout order, after Lifecycle is stable:
1. **Orchestrator** (Agent 1) — weekly report, ~1 week after Lifecycle is clean
2. **SDR** (Agent 2) — when you commit to paid outbound
3. **Creative** (Agent 5) — when asset request volume justifies
4. **Growth** (Agent 3) — after 2+ weeks of paid traffic data

Don't stack them. One agent live and stable before the next.

---

## What I (the agent in this session) can help with

- Adjust the L3/L1 email copy in `PLAYBOOK_LIFECYCLE.md` if the dry-run reveals tone issues
- Resolve the store_api welcome-email collision by editing `_send_welcome_email()` if you pick option (b)
- Write the HubSpot custom-property import CSV if you'd rather bulk-create them
- Add a Resend marketing-domain DNS guide if domain verification trips you up

## What I cannot do

- Operate the Cowork UI (your access)
- Send test emails through Resend (your API key, your account)
- Verify the Resend marketing domain (your DNS)
