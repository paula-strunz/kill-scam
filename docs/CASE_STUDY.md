# Kill Scam: portfolio case study

**A helper connects Gmail once. Kill Scam puts one red "Likely scam" label on the scams.**

Kill Scam is a home-use anti-scam helper for non-tech family members. I'm Paula Struncova, an AI product manager and not a developer. I built it with AI agents and spec-driven development. Repo: [paula-strunz/kill-scam](https://github.com/paula-strunz/kill-scam).

## Problem

Scam mail still lands in the inbox after Gmail filters it, with clean grammar and real-looking logos. My parents open Gmail every day. They will not learn a new app or read a risk score.

## The pivot

The first version was a paste-check: copy a suspicious message in, get a verdict. On 8 Oct 2026 I admitted the obvious: nobody will be pasting anything. My own PRD already said paste was a fallback and never the main door. Paste was a builder's assumption, and real users broke it.

Paste-check now stays as a demo only, under **Check something else**.

## The new direction

Spec 003 (Gmail-first home, merged in [#21](https://github.com/paula-strunz/kill-scam/pull/21)):

1. A family helper opens Kill Scam on the parent's device and clicks **Connect Gmail** once.
2. The watcher is spec'd to run the same five checks on new inbox mail. It is not live.
3. A likely scam gets one red **Likely scam** label in Gmail. The mail stays in the inbox.
4. When the checks are unsure, Kill Scam adds no label.

Kill Scam never sends, deletes, archives, or moves mail. On 9 Oct 2026 I approved Gmail's "modify" permission for one use: adding that label. The spec requires tests proving that send, delete, and trash calls get refused.

## Warning screen

Spec 004 (merged in [#20](https://github.com/paula-strunz/kill-scam/pull/20)) is one calm warning, like a browser "Dangerous site" page. One headline. One sentence that names the sender, such as "The email from 'La Banque Postale' may be trying to take your password." One **Don't reply** button. A quiet **This is wrong** link. It never shows a score, and the message body is never on the screen. Today it opens after a paste. Later it will open from a labeled email.

## The five checks

Each message goes through the same five checks: what it wants and which pressure trick it uses, who it claims to be (the real address, not the display name), web addresses read as text only, known scam patterns, then a verdict. The warning screen shows that verdict as Looks okay, Not sure, or Likely scam.

## How I evaluate it

France golden eval fixtures ([#14](https://github.com/paula-strunz/kill-scam/pull/14)): 21 made-up messages on `main`, 11 scams and 10 normal ones. `python -m kill_scam.evals` counts missed scams and false alarms with no API keys. CI runs Ruff and pytest on every pull request, with 65 tests passing.

## Status

| Piece | Status |
| --- | --- |
| Five checks, paste demo, warning screen | On `main` |
| Spec 003, plan, and tasks | On `main` ([#21](https://github.com/paula-strunz/kill-scam/pull/21), [#22](https://github.com/paula-strunz/kill-scam/pull/22)) |
| Gmail watcher and labeling | Spec'd and in progress, not live. Going live waits on the Google sign-in setup |

## Lessons

- **PRD first.** My PRD already said paste was not the main door. I should have built from it.
- **Users break builder assumptions.** Paste was easy to build and demo. My family would never use it.
- **Spec gates pay off.** I approve each spec, plan, and task list before any code, and agents never merge without my yes. That gate stopped a wrong batch merge.

## Links

- https://github.com/paula-strunz/kill-scam
- [`PRD.md`](PRD.md) · [`../specs/003-gmail-first-home.md`](../specs/003-gmail-first-home.md) · [`../specs/004-warning-screen.md`](../specs/004-warning-screen.md) · [`../evals/fixtures.json`](../evals/fixtures.json)

*Paula Struncova · AI Product Manager · Bordeaux*
