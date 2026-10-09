# 004: Warning screen (Path B paste-check)

Renamed from `002-shareable-result-card.md` so it no longer clashes with `specs/002-gmail-connect-v0`.

## Intent

A family member checks a suspicious email and needs the verdict in about 3 seconds on a phone. The screen is one calm warning, like a browser "dangerous site" page: a mark, a headline, one line on the harm, one safe button. The harm line names the email by sender and subject only, never the body. Kill Scam never sends or deletes mail. This is a helper, not a guarantee.

```text
            ( ! )

         Likely scam

 The email from 'La Banque Postale'
 may be trying to take your password.

        [ Don't reply ]

         This is wrong
```

Light page, near-black type, lots of whitespace. Today this screen opens after a paste. Once `specs/003-gmail-first-home.md` ships, it opens from a labeled Gmail message.

## Design rules (pass/fail)

1. One centered screen: a warning mark, one large headline (**Likely scam** / **Not sure** / **Looks okay**), one harm line.
2. The harm line names the email by sender display name (else sender address, else subject, else "This message") and what it is after. Example: "The email from 'La Banque Postale' may be trying to take your password." Names are capped at 40 characters.
3. No reasons, no chip row, no score, no five-check dump, no Copy summary.
4. One button. For a likely scam it is **Don't reply**. It leaves the warning and does not send or delete mail.
5. **This is wrong** is a quiet text link centered under the button at every width. Tapping it shows one short note under it.
6. Light, high contrast, large type. Headline and button fit on a 390px-wide screen without scrolling.

## Acceptance criteria

1. After **Check this message**, the paste result matches the design rules. The home screen is not shown behind it.
2. Labels map **likely_scam -> Likely scam**, **suspicious -> Not sure**, **ok -> Looks okay**. Likely-scam action is exactly `Don't reply`.
3. Only the From and Subject headers are read for the harm line. Tests prove a unique body string never reaches the harm line or the HTML.
4. All text placed in HTML is escaped. No web address appears on the screen.
5. `This is wrong` is horizontally centered under the button at 1280px and 390px.
6. The only controls on the screen are `Don't reply` and `This is wrong`.

## Out of scope

- Gmail labeling and the inbox watcher (spec 003)
- Sending, deleting, or moving mail
- Copy or share summaries
- Hosting or deploy changes
- New design dependencies

## Human gate

Do not merge without Paula.
