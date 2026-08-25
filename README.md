# Universal Project Template

## TL;DR

This is a **GitHub template repository** for starting any kind of project: TypeScript, Python, or another stack. Select **Use this template** on GitHub to create a new repository with these files and agent instructions.

## Create A Repository

1. Select **Use this template** at the top of the GitHub repository page.
2. Select **Create a new repository**.
3. Choose its owner, name, and visibility.
4. Select **Create repository**.

```text
This template
      |
      v
Use this template
      |
      v
Your new repository
```

The new repository is independent from this template. Keep shared agent instructions in `AGENTS.md`, reusable skills in `.agents/skills`, and reusable rules in `.agents/rules`.

## Development Flow

```text
Start a project
      |
      v
Choose the right stack for the use case
      |
      v
Follow its established industry practices
      |
      v
Build, test, explain, and verify
```

## How It Works

The template does not force a programming language or framework. The agent must first understand the use case, inspect the repository, and then apply the conventions and best practices of the selected ecosystem.

```text
                         .agents/
                       /          \
                  skills/          rules/
                 /      \          /     \
       .codex/skills  .claude/skills   tool rule links
```

`.agents` is the single source of truth. The `.codex` and `.claude` folders contain symbolic links, so both tools use the same skills and rules without duplicated files.

## Agent Behavior

The shared rules in `AGENTS.md` tell agents to:

- Use best practices and established industry patterns appropriate to the current use case.
- Detect and respect the project's language, framework, architecture, and existing conventions.
- Assume the user is non-technical unless they say otherwise.
- Start explanations with a short `TL;DR`.
- Use concise, ADHD-friendly sections, bullets, and clear next steps.
- Include a simple ASCII diagram when explaining a system, workflow, architecture, or non-trivial change.
- Explain jargon in plain language and make tradeoffs explicit.
- Validate work with the relevant formatter, linter, type checker, and tests.

## Structure

```text
.
|-- AGENTS.md             # Shared agent instructions
|-- AGENTS.local.md       # Optional project-specific additions
|-- CLAUDE.md             # Loads the shared instructions
|-- CLAUDE.local.md       # Loads local additions
|-- .env.example          # Safe environment-variable template
|-- .gitignore            # Common cross-language generated files
|-- .agents/
|   |-- skills/           # Canonical reusable skills
|   `-- rules/            # Canonical reusable rules
|-- .codex/
|   |-- skills -> ../.agents/skills
|   `-- rules  -> ../.agents/rules
`-- .claude/
    |-- skills -> ../.agents/skills
    `-- rules  -> ../.agents/rules
```

## Start A Project

1. Put project-specific context and exceptions in `AGENTS.local.md`.
2. Add reusable skills to `.agents/skills` and reusable rules to `.agents/rules`.
3. Add the application code and the standard tooling for its chosen ecosystem.
4. Ask the agent to implement the first feature; it should explain the plan clearly before making substantial changes.

Project-specific instructions override generic guidance when they conflict. Security, correctness, accessibility, and maintainability should remain default expectations.
