# Google Ads Suspension Appeal — Account 731-567-9505

**Suspension date:** 2026-06-24 (discovered)
**Category cited by Google:** "Unacceptable business practices" (Phishing / Public figure impersonation / Other)
**Google account:** xfree143@gmail.com
**Status as of this doc:** Awaiting identity verification → appeal submission

This is the paste-ready appeal package. Three sections below. Use them when you reach the actual appeal form after completing Google's identity-verification flow.

---

## Section 1 — Short appeal text (paste into Google's main appeal field)

Use this version if the form has a short character limit (most have 1,000–2,000 chars):

```
We respectfully appeal the suspension of account 731-567-9505. Plainspoken Foundry Nine is a legitimate small B2B software company that sells flat-rate operational software to manufacturers and landlords through https://store.plainspokenfoundrynine.com.

We are not phishing, impersonating any person or brand, or engaged in any deceptive practice. Specifically:

- We collect no credentials. All purchases are processed via Stripe live checkout. Account login is for paying customers only.
- We do not impersonate any public figure or competitor. Our six comparison pages (e.g. /comparisons/buildium-vs-pf9.html) provide honest competitive analysis and each one explicitly includes a "What they do well" section naming where the competitor — Buildium, AppFolio, DoorLoop, MRPeasy, Katana, Fishbowl — is stronger than us. This is the opposite of impersonation.
- Bidding on competitor brand keywords with comparison landing pages is well-established as legal and policy-compliant competitive advertising. We do not use any competitor's trademark in our display URL, ad headlines, or descriptions in a way that suggests affiliation.

The account is a single-owner small business. Full privacy policy, terms of service, and refund policy are published at /privacy.html, /terms.html, /refund.html. We are happy to provide business registration and any additional verification needed.

We request reinstatement. Thank you for reviewing.
```

---

## Section 2 — Longer expanded statement (use if Google's form allows more, or for a follow-up)

```
APPEAL — Account 731-567-9505 (xfree143@gmail.com)

About the business:
Plainspoken Foundry Nine ("PF9") is a small B2B SaaS company offering operational software for two verticals: small manufacturers (20–250 employees) and small landlords (5–50 units). The storefront is at https://store.plainspokenfoundrynine.com. Pricing is flat-rate ($249/mo Manufacturing Suite, $119/mo Property Suite, $49–299/mo standalone apps). All payments are processed via Stripe in live mode. Full Privacy Policy, Terms of Service, and Refund Policy are published on-site and linked from every page.

Addressing the suspension categories:

1. Phishing — does not apply. The site collects only the information necessary to process a Stripe subscription (email, name, optional company name). No credential harvesting, no impersonation of any payment processor, bank, or service provider. Stripe is the payment provider and the Stripe-hosted checkout page is visibly Stripe-branded.

2. Public figure impersonation — does not apply. The site does not impersonate, reference, bid on, or attempt to associate with any public figure, celebrity, politician, or executive.

3. Other unacceptable business practices — we believe this is a false-positive from our competitive-comparison ad strategy. The campaign targeted keywords like "buildium alternative," "appfolio alternative," "doorloop alternative," "mrpeasy alternative," "katana alternative," "fishbowl alternative," with landing pages at /comparisons/[competitor]-vs-pf9.html. Each comparison page:
- Clearly identifies us (Plainspoken Foundry Nine) as the source, never as the competitor
- Includes a "What [competitor] does well" section explicitly naming the competitor's strengths
- Includes a footer disclaimer that all third-party trademarks belong to their respective owners
- Provides factual price and feature comparison sourced from publicly available competitor pricing pages

This style of competitive comparison advertising is industry-standard for B2B SaaS and is consistent with Google Ads policies on competitive advertising and trademark use.

Additional context that may be relevant:
- The Google Ads account was set up recently and an auto-created onboarding campaign briefly ran broad-match keywords before being identified and removed.
- We have since cleaned up the account, set up proper conversion tracking through GA4, and prepared a strict competitor-comparison-only campaign structure for relaunch.

We are a small, real, single-owner business operating in good faith. We respectfully request reinstatement and are happy to provide any additional documentation needed — business registration, identity verification, payment processing proof, prior storefront screenshots, or anything else that helps.

Thank you for the review.
```

---

## Section 3 — Evidence to gather BEFORE submitting

Have these ready in case the appeal flow lets you attach files, or in case Google replies asking for more:

- [ ] **Storefront screenshots** — homepage, one product card detail, the Subscribe modal, the Stripe checkout page (proves real payment processor + real product)
- [ ] **All six comparison pages**, specifically capturing the "What [competitor] does well" sections (proves not impersonation, proves honest comparison)
- [ ] **`/privacy.html`, `/terms.html`, `/refund.html`** loading correctly (proves transparency)
- [ ] **Business registration / DBA filing** if you have one (proves real business entity)
- [ ] **Bank or merchant statement showing Stripe payouts** — even one entry — if you have any paying customers (proves real commerce, not phishing)
- [ ] **Deleted ghost-campaign history page screenshot** if Google still shows it — actually demonstrates you caught and removed the auto-created campaign yourself

---

## Section 4 — Filing tips

- **Don't argue or lecture Google.** Reviewers see thousands of appeals; antagonistic ones get auto-denied.
- **Don't claim Google's automated systems are broken** in the appeal text — even though they often are. State facts and let the reviewer draw their own conclusion.
- **Be specific.** Phrases like "we collect no credentials" and "honest 'what they do well' sections naming competitors' strengths" are the kind of concrete factual claims a reviewer can verify in 30 seconds.
- **Submit once.** Don't file multiple appeals — that flags the account further. One clean, complete appeal is best.
- **Plan for 5–14 days.** Most automated suspensions get a human review within ~7 days. Don't panic if you don't hear back immediately.

---

## Section 5 — If the appeal is denied

If the first appeal gets rejected and you want to push back, the most effective second-pass move:

1. **Reply to the denial email** (not a new appeal).
2. **Ask explicitly:** "Can you tell me which specific ad, keyword, landing page, or business practice triggered the unacceptable-business-practices flag? We are willing to make any specific change requested."
3. That request for specifics forces a human review and is the only path to substantive engagement.

If the second-pass appeal also fails, **abandon this Google Ads account** rather than trying to open a new account under the same name/Stripe/legal entity — Google detects and re-suspends. Reallocate the ad budget to:
- Reddit Ads (r/landlord, r/smallbusiness, r/manufacturing)
- LinkedIn Ads (manufacturing ops managers — expensive but precise)
- Direct outbound (`PLAYBOOK_OUTBOUND.md`)
- Newsletter sponsorships (manufacturing or property-management newsletters)

---

## Lessons captured (for the project, regardless of appeal outcome)

1. **Google's automated systems flag competitor-keyword campaigns aggressively** when paired with comparison landing pages, even when the campaign is policy-compliant. New advertisers are at higher risk.
2. **The onboarding auto-create flow can accumulate trust signals against you** before you even import your real campaigns. Step 0 of `PLAYBOOK_GOOGLE_ADS_PROPERTY_TEST.md` warns about this; this incident validates that warning.
3. **Free distribution channels are now structurally more important** for the next 3–5 weeks (suspension resolution window) — HN, Indie Hackers, Reddit, directory submissions, personal network, YouTube SEO. None of those depend on Google.
4. **If the appeal succeeds**, relaunch the property campaign with these mitigations: start at $5/day for 48h, exact-match only (no phrase or broad), one ad group at a time, and add competitor brand names to the negative list initially so Google can't possibly interpret your bidding as impersonation. Then expand match types only after Google's trust signal recovers.
