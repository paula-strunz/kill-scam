# 002 — Shareable result (Path B paste-check)

## Intent

A family member pastes a suspicious message and needs to understand the verdict in about 3 seconds on a phone. The outcome is one calm, modern result: a short label, one sentence, a few signals, and one next step. It is not a dense boxed report, and it does not forward the raw scam text. Kill Scam never sends or deletes mail. This is a helper, not a guarantee.

## Design

This section replaces the earlier boxed result card (thick border, “Result card” heading, all five checks written out, and a screenshot hint as the hero).

```text
Likely scam
One plain sentence of why.

[ chip ] [ chip ] [ chip ]

One next step.

Copy summary
```

### Design rules (pass/fail)

1. THE result SHALL lead with the verdict only: a short label (**Likely scam** / **Not sure** / **Looks okay**) in large type, plus one plain sentence of why.
2. THE screen SHALL show at most three short signal chips, then one next step (what to do). No extra sections.
3. THE layout SHALL be light, high contrast, lots of whitespace, large type, thin or no heavy borders, no thick boxed card chrome, no dense report, and no dump of the pasted message.
4. Copy-summary stays, but as a quiet text button under the result, not the visual hero.
5. Mobile-first: the verdict is readable without scrolling past it on a phone-width viewport.
6. Behavior stays the same: never send or delete mail; never include the full scam body in the shareable summary; checklist logic is unchanged except presentation.

## Acceptance criteria

1. After **Check this message**, the paste result matches the design rules above.
2. Labels map as **likely_scam → Likely scam**, **suspicious → Not sure**, **ok → Looks okay**.
3. The why line is a single sentence. Chips are at most three, each a short phrase. The next step is one line.
4. The shareable summary is built by pure functions with no Streamlit, Gmail, or OpenAI key. Check text in the HTML is escaped. Web addresses in the summary are defanged (no `http://` or `https://`).
5. The full pasted message is not in the on-screen result or the copy summary.

## Out of scope

- Gmail connect, reading an inbox, or any mailbox change
- Sending mail
- A Chrome extension
- Auto-posting to social networks
- Live hosting, Render, or other deploy changes
- A new design-system dependency

## Human gate

Do not merge without Paula.
