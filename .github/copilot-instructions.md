# Instructions for GitHub Copilot

Read `AGENTS.md` at the repository root and follow it. It is the single source of the
conventions for this repository: response shapes, the error contract, how to call the
model, and how tests are named.

When writing or revising a feature specification, also read
`.claude/skills/how-to-write-a-spec/SKILL.md` — it lists the eight sections and the
unhappy paths this repository actually has.

During a blind handoff (implementing from a file in `specs/`), do not ask the user
clarifying questions. Implement the specification on your best reading and list every
assumption you had to make in your final message.
