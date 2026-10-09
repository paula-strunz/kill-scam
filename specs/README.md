# Specs

Living specs are the source of truth for the **next** Kill Scam work. [docs/PRD.md](../docs/PRD.md) stays the product brief. Do not delete it. Feature work lives here, under `specs/`.

```text
Spec  -->  Plan  -->  Tasks  -->  Implement
  |         |          |            |
  v         v          v            v
Paula     Paula      Paula        Paula
says yes  says yes   says yes     says yes to merge
```

Paula (human) gates each phase. Agents do not skip ahead and do not merge without her explicit yes.

| Phase | What it answers | Gate |
| --- | --- | --- |
| Spec | What we are building, for whom, and how we will know it works | Paula accepts the spec |
| Plan | How we will do it with the code we already have | Paula accepts the plan |
| Tasks | Ordered checklist, including what is blocked on a person | Paula accepts the task list |
| Implement | Code or deploy only after the three files above exist | Paula says yes before merge |

## Features

| ID | Name | Status |
| --- | --- | --- |
| [001](001-paste-check-live/spec.md) | Live paste-check hosting (Path B) | Spec / plan / tasks written. Deploy blocked on Render sign-in. |
| [002](002-gmail-connect-v0/spec.md) | Gmail Connect V0 | Spec stub only. Blocked on Google OAuth. Do not implement yet. |
| [004](004-warning-screen.md) | Warning screen (Path B paste-check) | Spec written. One centered warning after a paste. Do not merge without Paula. |

Path B means: put the **already built** paste-check on a public URL. It does not need new feature code and it does not need Gmail.
