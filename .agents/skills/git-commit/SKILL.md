---
name: git-commit
description: Create well-formatted conventional commits with auto-detected type and scope
---

## What I do
- Analyze staged changes to determine commit type and scope
- Generate conventional commit messages in standard format
- Auto-commit without prompting

## When to use me
Run when you have staged changes ready to commit. I'll auto-detect the appropriate type and scope based on the changes and your prompt context.

## Workflow
1. Check for staged changes (`git diff --staged --name-only`)
2. If empty: error with `git add <files>` suggestion and exit
3. Auto-detect type using prompt context and file analysis:
   - CI configs (`.github/`, `.gitlab-ci.yml`) → `ci`
   - Build configs (`pyproject.toml`, `uv.lock`) → `build`
   - Performance improvements → `perf` (when mentioned in prompt)
   - Test files → `test`, Documentation → `docs`
   - Source code: infer from changes (new API → `feat`, bug fix → `fix`, restructuring → `refactor`)
   - Config/maintenance → `chore`
   - If unclear: default to `feat` for new, `fix` for modified
4. Auto-detect scope from `src/yams/<folder>` (tools, transport, config, server)
5. Generate message:
   - Subject: imperative, ≤50 chars, no period
   - Body: 1-3 bullet points explaining key changes
   - Check for `BREAKING CHANGE` marker in diff
6. Execute: `git commit -m "<message>"`

## Example output
```
feat(tools): add git-commit skill for conventional commits

- Create SKILL.md with frontmatter and workflow
- Implement auto-detection for type and scope
```

## Edge cases
- No staged changes: error with `git add` suggestion
- Mixed file types: use primary type or `chore`
