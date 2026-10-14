# Kill Scam — PRD

Status: V0 spec  
Audience: everybody who gets email, especially non-technical family  
Owner: Paula  
Repo: [paula-strunz/kill-scam](https://github.com/paula-strunz/kill-scam)

This document is the source of truth. Code follows it. We do not ship a new version without updating this file.

## Problem

People still get scam email in the inbox Gmail already “filtered.” The old tells (bad grammar, clumsy logos, obvious spam folders) are dying because fraudsters now use AI to write fluent, official-looking mail.

A 2025 study of 63 GPT-4o phishing emails found Gmail let 86% to 100% through, depending on the sending account ([Heiding et al. / Expert Systems with Applications](https://doi.org/10.1016/j.eswa.2025.127044)). Cofense’s 2026 report describes the same shift for business-email-compromise: AI removed the awkward phrasing that used to give scams away. Filters hunt junk. These messages look like mail.

Paula’s own observation: spam still lands in the official inbox. Copy-paste into a checker is not how family will use a product in 2026.

## Who it is for

- Primary: non-technical people (family, anyone who is not going to inspect headers).
- Secondary: Paula, as an AI PM, shipping a public GitHub project with real Arize evals.
- Not: security engineers, SOC tools, enterprise DLP.

## V0 (this version)

**First function: a Gmail-connected agent.**

1. Person opens Kill Scam.
2. They connect Gmail once. The **Likely scam** label needs Gmail's modify permission (see [specs/003-gmail-first-home.md](../specs/003-gmail-first-home.md)).
3. The agent runs: it looks at new / recent mail and says whether each flagged message looks like a scam, with a visible why.
4. It only adds a **Likely scam** label. It never sends or deletes mail.

Install for V0 means a small hosted app, not `pip` and not “paste the email body.”

Google will not let an unverified app read everyone’s Gmail. V0 is therefore **Paula + invited family/test users** on a Google Cloud OAuth consent screen in testing mode. Public “everybody on earth” is a later Google verification track, not a V0 lie.

Paste-a-message is a fallback for V1 (SMS / WhatsApp / a mail forwarded from someone who did not connect). It is not the main door.

SMS, letters, and phone scams are out of V0.

## What fraudsters are actually doing

Psychological hooks (not only urgency). The agent must name which hook is firing, then still verify domain and campaign. A polished mail with no typos is a reason to check harder, not to relax.

| Hook | What it looks like | Why it works |
| --- | --- | --- |
| Authority | Impôts, banque, La Poste, DGFiP, Microsoft | People defer to official power |
| Fear / loss | Unpaid bill, account will close, “you were charged €200” | Loss hurts more than a promised gain |
| Fake confirmation | “You already bought this, click to cancel” | Feels like undoing a real mistake |
| Reward | Precise trop-perçu / refund | Plausible amount, official tone |
| Urgency / scarcity | Act now, 24h, last warning | Stops people thinking (overused, still everywhere) |
| Liking / familiarity | Looks like a brand you already trust | Strong predictor of people actually complying |
| Reciprocity | “We’ll help you undo this” | They appear to be doing you a favour |
| Curiosity | Invoice / document to open | The click is the payload |

France-facing example: [cybermalveillance.gouv.fr on fake tax refunds](https://www.cybermalveillance.gouv.fr/tous-nos-contenus/actualites/remboursement-impot-hameconnage) (precise amount, official look, urgency, fake site). DGFiP never asks for a RIB by email. Real refunds go to the account already on file.

Sources: CISA / FTC phishing guidance; Cialdini’s influence principles as used in phishing research (scarcity is common; authority and liking predict compromise more); Cofense 2026; the 2025 Gmail/Outlook bypass study above.

## How it decides (the product)

Kill Scam is a visible checklist agent, not a magic “feels sketchy” guess.

1. **Ask** — What do they want you to do? Click, pay, give a code, install, stay silent. Which hook is in the text.
2. **Identity** — Who they claim to be vs the real address. Official domain from a known list / lookup. Never trust the display name.
3. **Links** — Inspect the registered domain only (lookalikes, extra words). Do **not** open the destination page.
4. **Campaigns** — Check current official warnings (cybermalveillance.gouv.fr, service-public, CISA, FTC). If search is down, continue and lower confidence.
5. **Verdict** — Looks OK / Be careful / Likely a scam, with evidence, plus what to do (don’t click; open the real app yourself; report email via signal-spam.fr).

Arize traces each step. Evals score: missed scam, false alarm, and whether the steps actually ran. Golden set must include lookalike domains and a legitimate school/admin mail.

## Not in V0

- SMS carrier integration, letters, phone
- Auto-delete, auto-report, auto-reply
- Visiting the phishing page
- A training course
- Unverified public OAuth for the whole internet
- Replacing Gmail’s spam folder (we check what already landed)

## Success

- Paula can connect her Gmail and see recent mail classified without pasting.
- A lookalike impôts / parcel / unpaid-bill mail is caught.
- A normal school or newsletter mail is not called a scam.
- Family can be added as Google test users and complete Connect Gmail with help once.
- Arize shows traces for a real check.

## Open

- Hosting: where the always-on process lives (must run when the laptop is closed).
- How we tell the person (in-app list vs a daily digest vs a ping only on likely_scam).
- When to start Google’s restricted-scope verification for a public audience.
