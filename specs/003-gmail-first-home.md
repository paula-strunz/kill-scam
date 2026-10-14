# 003: Gmail-first home

Draft for Paula. Builds on the PRD, `specs/002-gmail-connect-v0` and the PR #20 warning screen.

## Intent

A retired parent will never paste an email. A family helper connects their Gmail once, then Kill Scam checks new mail by itself. Paste stays under **Check something else** as a demo fallback.

## How the parent gets warned

Kill Scam adds one red Gmail label, **Likely scam**, to the scam itself.

Why: they already open Gmail every day, so the warning sits on the scam with no new app to learn.

Tapping that mail inside Kill Scam opens the PR #20 warning (one headline, one harm line, **Don't reply**).

## First visit

1. The helper opens Kill Scam on the parent's device.
2. One button: **Connect Gmail**. The helper clicks through Google's screens with the parent.
3. Home becomes one line: "Kill Scam is watching your inbox."

## When a scam arrives

1. Every few minutes, the watcher runs the same five checks on new inbox mail.
2. Only a likely scam gets the label.
3. The parent opens Gmail, sees **Likely scam** next to the subject, and leaves it alone.

Safe default: when the checks are unsure, do nothing. A parent who sees the label on normal mail learns to ignore it.

## Out

- Sending any email, including alerts to the parent
- Deleting, archiving, or moving mail
- The message body on the warning screen
- Paste as the main door
- Public sign-in (V0 stays invited testers)

## Setup

Paula creates the Google OAuth client and publishes it as "In production" (unverified is fine). In "Testing", Google cuts access after 7 days. The helper clicks past "Google hasn't verified this app" once.

## Done when

1. First visit shows **Connect Gmail** as the only button.
2. After connect, home shows the watching line and nothing else to do.
3. A likely scam in a test inbox gets one **Likely scam** label within 10 minutes and stays in the inbox.
4. Unsure and safe mail get no label.
5. A labeled mail opens the PR #20 warning. The warning names the email by sender and subject, never the body.
6. Disconnect stops labeling.
7. Tests prove send, delete, and trash calls are refused, and paste still works.

## Decision

Paula approved Gmail's "modify" permission on 9 Oct 2026, used only to add the **Likely scam** label. Google's consent screen will say "read, compose, and send emails". Kill Scam still never sends, deletes, archives, or moves mail.
