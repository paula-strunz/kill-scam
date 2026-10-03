# 002 — Shareable result (Path B paste-check)

## Intent

A family member pastes a suspicious message and needs to understand the verdict in about 3 seconds on a phone. The screen is one calm warning, in the same family as a browser “dangerous site” page: a mark, a headline, what could go wrong, and one safe action. It is not a boxed report, not a score, and not a row of chips. It does not forward the raw scam text. Kill Scam never sends or deletes mail. This is a helper, not a guarantee.

## Design

This section replaces both the thick boxed result card and the later chip layout.

The structure follows real scam-warning pages (one centered screen, one primary safe action, one quiet “this may be wrong” link). It does not copy another product’s name, logo, colors, or wording. It does not look like a scan report: no score, no vendor table, no long list of signals.

```text
            ( ! )

        Likely scam

   One short paragraph of the harm.

        Two short reasons at most

          [ Don't reply ]

           Copy summary
           This is wrong
```

Light page: off-white background, near-black type, lots of whitespace. The verdict fills the screen. The safe action is the only button.

### Design rules (pass/fail)

1. THE result SHALL be one centered screen: a warning mark, one large headline (**Likely scam** / **Not sure** / **Looks okay**), and one short paragraph of the harm.
2. THE screen SHALL show at most two short reasons under that paragraph. No chip row, no score, no vendor table, and no dump of the five checks.
3. THE screen SHALL offer one primary action. For a likely scam that action is **Don't reply**. It is the only button. It does not send or delete mail.
4. **Copy summary** and **This is wrong** SHALL be quiet text links under the action, not a second hero and not a boxed report.
5. THE layout SHALL be light (off-white), high contrast, large type, and open. No thick boxed card. No pasted message body.
6. Mobile-first: the headline and the primary action fit on a phone-width viewport without scrolling past the verdict.
7. Checklist logic stays the same except presentation. The shareable summary never includes the full scam body.

## Acceptance criteria

1. After **Check this message**, the paste result matches the design rules above. The rest of the home screen is not shown behind it.
2. Labels map as **likely_scam → Likely scam**, **suspicious → Not sure**, **ok → Looks okay**.
3. Reasons are at most two short phrases. The likely-scam primary action is exactly `Don't reply`.
4. The summary is built by pure functions with no Streamlit, Gmail, or OpenAI key. Text placed in the HTML is escaped. Web addresses in the summary are defanged (no `http://` or `https://`).
5. The full pasted message is not on the warning screen or in the copy summary.

## Out of scope

- Gmail connect, reading an inbox, or any mailbox change
- Sending mail
- A Chrome extension
- Auto-posting to social networks
- Live hosting, Render, or other deploy changes
- A new design-system dependency
- Copying another product’s branding, colors, logo, or wording

## Human gate

Do not merge without Paula.
