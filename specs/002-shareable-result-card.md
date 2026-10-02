# 002 — Shareable result card (Path B paste-check)

## Intent

After someone finishes **Check this message**, family who are not technical need a clear snapshot of the verdict. They should be able to screenshot that snapshot or copy a short summary without forwarding the raw scam text. Sharing the original message can spread the scam, so the card leaves the full pasted body out. The card uses the same calm words as the five checks. It is a helper for a conversation, not a guarantee, and it never sends or deletes mail.

## Acceptance criteria

1. After a successful **Check this message** (the paste path behind **Check something else**), the page shows a **Result card** under the five-step verdict.
2. The card’s verdict label uses the existing on-screen words: **Looks OK**, **Be careful**, or **Likely a scam — do not click**.
3. The card lists all five check titles, in checklist order, each with one line. Each line is a single line of at most 120 characters.
4. The card says this is a helper, not a guarantee, and that Kill Scam never sends or deletes mail.
5. The card includes this hint, exactly: `Screenshot this card to share with family.`
6. The card states that the original message is not on the card.
7. The full pasted message body is not on the card, in the on-screen text, or in the copy text.
8. A plain-text copy of the same card is available. Web addresses in that text are defanged (no `http://` or `https://`).
9. The card text is built by pure functions that tests can run with no Streamlit, Gmail, or OpenAI key.
10. Text taken from the check is escaped before it is placed in the card’s HTML.

## Out of scope

- Gmail connect, reading an inbox, or any mailbox change
- Sending mail
- A Chrome extension
- Auto-posting to social networks
- Live hosting, Render, or other deploy changes

## Human gate

Do not merge without Paula.
