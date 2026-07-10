# Agent Instructions

## Skill Optimization

When the user asks to optimize, benchmark, evaluate, or improve a Markdown-based agent skill, use the repo-local `skill-optimizer` skill in `.agents/skills/skill-optimizer/`.

Do not rewrite a skill from intuition alone.

For optimization work:

1. Preserve the original `SKILL.md`.
2. Establish a baseline before edits.
3. Use separate train, validation, and test splits.
4. Keep edits bounded and traceable.
5. Accept changes only after held-out validation.
6. Record rejected edits and regressions.
7. Keep the test split isolated until final evaluation.

Store optimization artifacts under `runs/`.
