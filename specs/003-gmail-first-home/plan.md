# 003: Plan (Gmail-first home)

Status: draft for Paula. Spec: `003-gmail-first-home.md` (PR #21).

## Approach

1. **Scope change.** Paula approved `gmail.modify` on 9 Oct 2026. Swap `gmail.readonly` for `gmail.modify` in `gmail.py`. Keep a hard allowlist of API calls: `messages.list`, `messages.get`, `messages.modify` (add our label id only), `labels.list`, `labels.create`. Anything else raises `GmailError`. A `modify` call that removes any label, or adds INBOX, TRASH, SPAM or any label other than ours, is refused. Update the home copy "It never writes to your mailbox" to match.
2. **Polling first, no push.** Gmail push needs a Google Cloud Pub/Sub topic, a public webhook and a `watch` renewal every 7 days. Polling `history.list` (fall back to `messages.list q=in:inbox newer_than:1d`) every 5 minutes meets the 10 minute target with fewer moving parts. Revisit push only if testers grow past a handful.
3. **Label.** On first run, find "Likely scam" via `labels.list`, else create it with a red color and `messageListVisibility: show`. Store its id.
4. **Same five checks.** The watcher builds `as_check_text()` and calls `classify_message`. No new classifier.
5. **Unsure means no label.** Label only when verdict is `likely_scam`. `suspicious`, `ok`, errors, timeouts and missing API keys all mean no label. Each message is checked once.
6. **Storage.** Per account: refresh token (encrypted with a key from env), label id, last `historyId`, set of checked message ids, connected flag. Small SQLite file on a Render persistent disk. Never store bodies.
7. **Hosting on Render.** Existing `render.yaml` web service plus one background worker running the poll loop, sharing the disk. Disconnect clears the token and stops the loop for that account.
8. **Google client.** Must be "In production" (unverified). In "Testing", refresh tokens expire after 7 days and labeling stops silently. The watcher logs and shows "Reconnect Gmail" when a token fails, instead of failing quietly.
9. **Evals.** Run `evals/fixtures.json` through the label decision. Gate: zero labels on safe fixtures, zero labels on suspicious fixtures, and report scam recall. A labeled false alarm blocks merge.

## Risks and open questions

1. **Apple Mail shows labels as folders.** Over IMAP, Gmail labels become mailboxes, so a parent on Apple Mail sees a "Likely scam" folder, and the mail in both Inbox and that folder, with no tag on the row. The warning is easy to miss. Ask helpers which app the parent uses; Apple Mail users may need another warning path.
2. **Gmail mobile list view.** Google's help pages describe "Show in message list" on desktop web, and mobile apps showing label colors, but they do not state whether custom labels appear on rows in the iOS or Android inbox list. Not confirmed. Test on a real phone before promising it.
3. **Modify scope is broad.** The consent screen reads like full mailbox access. Our code allowlist is the only guard.
4. **Unverified app warning** may scare helpers. Google can also cap unverified apps at 100 users.
5. **Render disk** is single instance; a worker restart must resume from the stored `historyId`.
6. **LLM cost** grows with every new mail, not only pasted ones. Skip mail from the parent's contacts? Paula decides.
