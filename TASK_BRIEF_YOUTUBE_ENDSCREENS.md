# Task Brief — YouTube End Screens + Pinned Comments (delegable)

**For:** an assistant or VA with access to the PF9 YouTube channel (`@plainspokenfoundrynine`).
**Goal:** add an end screen + a pinned comment to all 14 product videos so viewers get routed back to the storefront instead of dead-ending.
**Time:** ~70 min for end screens + ~15 min for pinned comments. Can be done in batches.
**Judgment required:** none — every decision is pre-made below. This is repetitive execution.

---

## Access needed (do this the SAFE way)

Do **not** share the Google account password. Instead, the channel owner grants delegated access:
- YouTube Studio → **Settings → Permissions → Invite** → add the assistant's Google account as **Editor** (or Manager).
- Editor access is enough to add end screens and post/pin comments, and can be revoked anytime.

Everything below is done at **studio.youtube.com** on a **desktop browser** (the end-screen editor barely works on mobile).

---

## Part A — End screens (~5 min × 14 = ~70 min)

For **each** of the 14 videos:

1. YouTube Studio → **Content** → click the video's title.
2. In the video's left menu, click **Editor** (or find **End screen** in the right rail of the detail page).
3. Click **End screen** → start blank (skip templates for control).
4. Add these elements via **+ Element**:
   - **Subscribe** → place **top-left**, set to run the **full duration** of the end screen.
   - **Video → "Choose a specific video"** → select the **paired video** from the table below → place **bottom-center**.
   - *(optional)* **Video → "Best for viewer"** → place **top-right** (YouTube auto-selects).
5. Drag the timeline so the end screen covers the **last ~10 seconds** of the video. If the elements overlap, nudge them apart (YouTube blocks saving overlaps).
6. Click **Save**. Next video.

### Pairing table — which "watch next" video to select

Each video points to the next in its group, looping so none dead-ends.

**Manufacturing Suite**
| Video (open this one) | URL | Watch-next → select this |
|---|---|---|
| SHIFTLOG | https://youtu.be/AZA8wj916Sc | FLOWTRACK |
| FLOWTRACK | https://youtu.be/VA_TKydOxuQ | QUALIFI |
| QUALIFI | https://youtu.be/42TdtdcaUnk | REPORTR |
| REPORTR | https://youtu.be/YLrNw3ZMLXc | INSPECTR |
| INSPECTR | https://youtu.be/_1SQDCRjhf0 | SHIFTLOG (loop) |

**Property Suite**
| Video (open this one) | URL | Watch-next → select this |
|---|---|---|
| LANDLORDR | https://youtu.be/lpA0qVSOyBY | TENANTLINK |
| TENANTLINK | https://youtu.be/w_02sqH1n3s | PROPERTY_BUNDLE |
| PROPERTY_BUNDLE | https://youtu.be/63TRUxSKeho | LANDLORDR (loop) |

**Operations & Compliance**
| Video (open this one) | URL | Watch-next → select this |
|---|---|---|
| COMPLI | https://youtu.be/Y-gxxXJ-EkQ | EXTRACTR |
| EXTRACTR | https://youtu.be/0rpvA708nFI | MAINTAINR |
| MAINTAINR | https://youtu.be/eHUC-CvuQig | SUPPORTR |
| SUPPORTR | https://youtu.be/jVm4NyP_Ssk | PERMITR |
| PERMITR | https://youtu.be/RzKqlyjprMM | TASKFLOW |
| TASKFLOW | https://youtu.be/O2lUhXMeA34 | COMPLI (loop) |

**Gotchas:**
- If a video still shows "processing," end-screen options may be greyed out — come back once it finishes.
- The Subscribe element shows as the channel icon on the live video (no thumbnail preview) — that's normal.

---

## Part B — Pinned comments (~1 min × 14 = ~15 min)

For **each** of the 14 videos, open the video's public watch page (while signed into the channel), post this exact comment, then click the **⋮ (three dots) → Pin**:

```
Subscribe in 60 seconds at store.plainspokenfoundrynine.com — no demo to book, no sales call, 14-day money-back guarantee.

Cost math vs per-seat competitors: store.plainspokenfoundrynine.com/comparisons/
```

(The comment must be posted from the channel account so it shows the channel's name and can be pinned.)

---

## Definition of done

- [ ] All 14 videos have an end screen with a Subscribe element + a "watch next" video per the pairing table.
- [ ] All 14 videos have the pinned comment above.
- [ ] Spot-check 2–3 videos on the live watch page to confirm the end screen renders in the final seconds and the comment is pinned to the top.

---

## Why this matters (context for whoever does it)

When the storefront gets a traffic spike (e.g. a Hacker News launch), a chunk of visitors click through to a demo video. Without an end screen or pinned comment, the video ends and they leave. These two additions give every video two routes back to the storefront — turning video-watchers into potential customers instead of dead-ending them.
