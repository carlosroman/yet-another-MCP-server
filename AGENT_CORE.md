# Agent Core Configuration

## Engineering Principles
- SOLID: Apply when designing new modules or refactoring boundaries. Avoid forcing patterns into simple utilities.
- DRY: Extract shared logic only when duplication causes maintenance risk or divergent bugs.
- KISS: Prefer explicit, readable code over clever abstractions. If it takes >2 minutes to explain, simplify.
- Fail Fast: Validate inputs early, throw descriptive errors, never swallow exceptions.
- Test-Driven Mindset: Write tests alongside implementation. Cover happy paths, edges, and failures.

## Quality Guardrails
- Maintain or improve existing test coverage; never delete tests to unblock progress
- Run linter/type-checker before committing; fix all warnings
- Commit atomic, reversible changes with conventional messages
- Document non-obvious decisions; assume the next reader knows the language but not the context

## Flexibility Clause
Principles are guidelines, not dogma. Prioritize project context, performance constraints, and team conventions. If a principle conflicts with a clear technical requirement, document the trade-off and proceed.

## Output Expectations
- Always verify tests pass and linter is clean before committing
- Report test results, coverage impact, and commit hash
- Flag ambiguities in plans before implementing
- Never skip tests, suppress errors, or introduce scope creep
