# 001 — Tasks: live paste-check on Render

Status: **not started**  
Spec: [spec.md](spec.md) · Plan: [plan.md](plan.md)

Nothing below is done. Empty boxes mean not done. Deploy is blocked on a person, not on code.

```text
Paula accepts spec + plan
        |
        v
Paula signs in to Render     <-- blocked here
        |
        v
Deploy main (no new feature code)
        |
        v
Walk the acceptance checks on the live URL
```

## Human gate

- [ ] Paula has read `spec.md` and `plan.md` and said yes to Path B. *(blocked on Paula)*

## Deploy (blocked)

- [ ] Paula signs in to the Render account that will host Kill Scam. *(blocked on Render account sign-in — human)*
- [ ] Render service uses `main`, the existing `Dockerfile`, and `render.yaml`.
- [ ] `KILL_SCAM_HOSTED` and `PORT` match `render.yaml`. Google and OpenAI variables stay empty for Path B.
- [ ] Copy the public https URL into this file once it exists. Until then there is no URL to test.

## Checks (mapped to acceptance criteria)

Do these on the live URL after deploy. Do not mark them done from a laptop demo.

- [ ] **AC1.** URL loads and shows Kill Scam without a Google login.
- [ ] **AC2.** Paste sample email text, press **Check this message**, and see **Looks OK**, **Be careful**, or **Likely a scam**.
- [ ] **AC3.** The five steps are visible on that same check.
- [ ] **AC4.** The paste check completes with no mailbox connected and does not send, delete, or change mail.
- [ ] **AC5.** Google OAuth env vars are unset. Connect Gmail may show “isn’t set up yet”. Paste still returns a verdict.
- [ ] **AC6.** `OPENAI_API_KEY` is unset. The verdict still appears. (Offline tests and evals stay on synthetic fixtures; they are not a substitute for this live check.)
- [ ] **AC7.** Empty paste asks for a message and does not show a fake verdict.
- [ ] **AC8.** The page still says it is a helper, not a guarantee, and that it does not open links from the mail.

## After the URL works

- [ ] Paula tries the link herself and says whether Path B is accepted.
- [ ] Do not merge follow-up code, and do not start Gmail Connect, from this task list.
