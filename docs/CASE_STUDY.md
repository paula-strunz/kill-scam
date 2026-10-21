# Kill Scam: portfolio case study

**A helper connects Gmail once. Kill Scam puts one red "Likely scam" label on the scams.**

Kill Scam helps non-tech family. I'm Paula Struncova, an AI product manager. Repo: [paula-strunz/kill-scam](https://github.com/paula-strunz/kill-scam).

## Problem

Scam mail still lands in the inbox, with clean grammar and real-looking logos. My parents open Gmail every day. They will not learn a new app or read a risk score.

## The pivot

The first version asked people to paste a message. On 8 Oct 2026 I saw that nobody will paste. The product brief already said paste was a fallback. Paste now stays as a demo under **Check something else**.

## The new direction

Spec 003, merged in [#21](https://github.com/paula-strunz/kill-scam/pull/21):

1. A helper clicks **Connect Gmail** once on the parent's device.
2. The watcher will run five checks on new inbox mail. It is not live.
3. A likely scam gets one red **Likely scam** label and stays in the inbox.
4. Unsure checks add no label.

Kill Scam never sends, deletes, archives, or moves mail. On 9 Oct 2026 I approved Gmail's modify permission only to add that label. Tests must refuse send, delete, and trash.

## Warning screen

Spec 004, merged in [#20](https://github.com/paula-strunz/kill-scam/pull/20), is one calm page, like a browser "Dangerous site" warning. Headline: **Looks okay**, **Not sure**, or **Likely scam**. One sentence names the sender, for example "The email from 'La Banque Postale' may be trying to take your password." One **Don't reply** button. A quiet **This is wrong** link. No score, and the message body stays off the screen. It opens after a paste today, and from a labeled email later.

## The five checks

What it wants, who it claims to be (the real address), web addresses as text only, known scam patterns, then the verdict above.

## How I evaluate it

21 made-up messages ([#14](https://github.com/paula-strunz/kill-scam/pull/14)): 11 scams, 10 normal. `python -m kill_scam.evals` counts missed scams and false alarms, with no API keys. CI runs Ruff and pytest. 66 tests pass.

## Status

| Piece | Status |
| --- | --- |
| Five checks, paste demo, warning screen | On `main` |
| Spec 003, plan, and tasks | On `main` ([#22](https://github.com/paula-strunz/kill-scam/pull/22)) |
| Gmail watcher and labeling | Not live. It waits on Google sign-in |

## Lessons

I approve each spec, plan, and task list before code. Agents do not merge without my yes.

## Links

- [`PRD.md`](PRD.md) · [`../specs/003-gmail-first-home.md`](../specs/003-gmail-first-home.md) · [`../specs/004-warning-screen.md`](../specs/004-warning-screen.md) · [`../evals/fixtures.json`](../evals/fixtures.json)

*Paula Struncova · AI Product Manager · Bordeaux*
