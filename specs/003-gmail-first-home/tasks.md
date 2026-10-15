# 003: Tasks (Gmail-first home)

Ordered. Each task is one small PR. Spec criteria in brackets.

## T1. Write guard for modify scope [7]
Done when:
1. `SCOPES` is `gmail.modify` only; send, compose, insert, settings still forbidden.
2. Allowlist covers messages list/get/modify and labels list/create only.
3. `modify` accepts only `addLabelIds=[our id]` and an empty remove list.
Tests: send, delete, trash, batchDelete, untrash, removing INBOX, adding TRASH or SPAM all raise `GmailError`.

## T2. Label setup [3]
Done when:
1. Existing "Likely scam" label is reused, else created red and shown in message list.
2. Running twice creates one label.
Tests: fake Gmail service, label present and absent.

## T3. Storage [6]
Done when:
1. SQLite holds encrypted refresh token, label id, `historyId`, checked ids.
2. No body text is written.
3. Disconnect deletes the account row.
Tests: round trip, missing key fails closed, schema has no body column.

## T4. Label decision [3, 4]
Done when:
1. Only `likely_scam` returns "label".
2. `suspicious`, `ok`, exceptions and timeouts return "skip".
Tests: one per verdict, plus an exception case.

## T5. Watcher loop [3, 6]
Done when:
1. Each tick reads new inbox ids since `historyId`, checks each once, labels per T4.
2. Labeled mail keeps INBOX.
3. Expired token marks the account "reconnect needed" and stops.
4. Disconnected accounts are skipped.
Tests: fake service with scam, safe, suspicious mail; restart resumes; expired token.

## T6. Home screen [1, 2]
Done when:
1. Not connected: one **Connect Gmail** button.
2. Connected: "Kill Scam is watching your inbox." and nothing else to do.
3. Paste lives under **Check something else**.
4. Home copy no longer says it never writes to the mailbox.
Tests: Streamlit AppTest for both states; existing paste tests pass.

## T7. Open labeled mail [5]
Done when:
1. A labeled mail in Kill Scam opens the PR #20 warning.
2. Copy summary never contains the full body.
Tests: summary from a long body excludes the body.

## T8. Evals gate [4]
Done when:
1. `evals` reports label decisions on fixtures.
2. Zero labels on safe and suspicious fixtures; CI fails otherwise.
Tests: CLI test on fixtures.

## T9. Render worker [3, 6]
Done when:
1. `render.yaml` adds a worker and persistent disk; secrets via dashboard only.
2. Docs cover "In production" publishing and the 7-day Testing cutoff.
Tests: config test parses `render.yaml`.

## T10. Manual check (human gate)
Done when:
1. A test scam in a test inbox gets one label within 10 minutes and stays in the inbox.
2. Label checked in Gmail web, Gmail iOS, Gmail Android and Apple Mail, with screenshots.
3. Disconnect, send a new scam, no label.
