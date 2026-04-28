# Rules

AI context for this repository. Read this before doing anything.

---

## Agent Entry Points

`CLAUDE.md` is the source of truth for agent instructions in this project.

Other agent files like `AGENTS.md`, `GEMINI.md`, `CODEX.md` are all links to
`CLAUDE.md`.

---

## Who / Environment

- **Owner Name:** Otávio Miranda
- **Tone:** teammate, direct, no corporate fluff.
- **Language:** English everywhere related to code, git, GitHub, documentation,
  `README.md`. For chat, use the user's language (detected by the message).

---

## Repository Context

**IF THIS TEXT IS STILL HERE, THIS PROJECT IS STARTING RIGHT NOW. AGENT, PLEASE
FIND OUT WHAT THIS PROJECT IS ABOUT AND REPLACE THIS MESSAGE WITH A PROPER
DESCRIPTION FOR THE PROJECT.**

---

## Workflow

**DEFAULT FLOW: issue -> branch -> PR -> merge**.

Before starting new feature work, check open issues and confirm whether the
request already maps to an open issue, was intentionally deferred, or was
already delivered locally but not cleaned up in the tracker. Keep the issue list
accurate as part of the workflow.

1. Pick or create the issue. If no issue template exists, warn the user and
   create one.
2. Create a branch for that issue.
3. Work in small conventional commits: `feat`, `fix`, `refactor`, `chore`,
   `docs`, `ci`, etc.
4. Open a PR using the PR template and reference the issue with `closes #N`. If
   no PR template exists, warn the owner and create one.
5. Merge according to the repository convention. If no convention is documented,
   ask the owner before merging (squash, merge commit, or rebase).
6. Delete the branch after merge (merge, squash and delete).

Since Git and GitHub are the main project context, be explicit, precise, and
concise about every change. Always describe what matters for project
understanding in commits, issues, PRs, and handoffs.

### Commit Style

```text
type(scope): short imperative description

Optional body explaining what changed and why.

Co-Authored-By: <agent-name> <noreply@example.com>
```

`Co-Authored-By` is optional, but useful when more than one agent worked on the
change. Replace `<agent-name>` with the actual agent (Claude, Codex, Gemini,
etc.) instead of leaving a placeholder.

If a task is explicitly about a release, use semantic versioning and annotated
git tags unless the repository documents another process.

Keep sessions focused. One issue per session is the default. Leave a clear
handoff when you finish.

---

## Project Coding Rules

These rules define the default engineering baseline for this project.

They are not decorative. Follow them unless there is a clear technical reason
not to. When breaking a rule, keep the code simple and make the reason obvious.

### Core principles

- Prefer boring, explicit, maintainable code.
- Do not over-engineer.
- Do not create abstractions before there is a real need (they are welcome, but
  start simple first).
- Do not hide complexity behind vague names.
- Do not rewrite working code just to make it look different.
- Follow the conventions of the framework, language, and ecosystem.
- Optimize for maintainability, readability, testability, and safe future
  changes.

### Code style

The code style is our objective, not a law. Whenever possible, follow the rules
below.

- Functions should usually be small and focused.
  - Aim for up to 40 lines.
  - Keep Cyclomatic Complexity as low as possible.
  - Longer functions are acceptable when the flow is simple, linear, and easier
    to read in one place.
  - Split functions when they mix responsibilities, contain repeated blocks, or
    require deep nesting.

- Files should stay focused.
  - Aim to keep files under 500 lines (this helps humans and agents).
  - Larger files are acceptable for generated code, schemas, constants,
    mappings, fixtures, or framework-required structure.
  - Split files by responsibility, not just by line count.

- Each function should do one clear thing.
- Each module should own one clear responsibility.
- Prefer clear domain names over generic names.

Avoid vague names such as (unless for libs and framework conventions):

- `data`
- `handler`
- `manager`
- `processor`
- `service`
- `utils`
- `helper`
- `thing`
- `item`

Use names that describe the domain, behavior, or returned value.

Bad:

```ts
function handle(data: any) {} // handle what? which data? what type is the data?
```

Better:

```ts
function createUserSession(credentials: LoginCredentials) {} // The same function, way easier to read, find and understand
```

- Avoid names that are impossible to search in the codebase.
- Generic names like `request`, `response`, `payload`, `config`, `logger`, or
  `client` are allowed when the context makes them obvious.
- Prefer early returns over deeply nested conditionals.
- Prefer shallow nesting. Reconsider the design when nesting goes beyond two or
  three levels — usually a guard clause, an early return, or a small extracted
  function fixes it.
- Keep control flow obvious.
- Avoid clever code.
- Avoid hidden side effects.
- Avoid mutation unless it makes the code simpler and safer.
- Keep domain and business logic decoupled from infrastructure (databases,
  filesystems, external binaries, network calls, system clocks). Inject these as
  dependencies at the boundary instead of importing them directly inside domain
  code.
- Do not hardcode magic numbers, magic strings, secrets, passwords, tokens and
  other values known to be tied to the environment.

### Types

- Use explicit types at public boundaries.
- Do not use `any` unless there is no safer option.
- When `any` is unavoidable, isolate it and explain why.
- Avoid untyped functions.
- Prefer domain-specific types over loose dictionaries/objects.
- Avoid broad generic types like `Dict`, `object`, `Record<string, unknown>`, or
  `{}` when the expected shape is known.
- Validate external input at the boundary.
- Do not trust API input, CLI input, environment variables, database rows, or
  user-controlled data without validation.
- Use type checkers and linters, for instance: `biome`, `eslint`, `ruff`,
  `pyright`, `prettier`, `editorconfig`, etc (these are just examples for
  clarity).

### Duplication

- Do not duplicate business rules.
- Do not duplicate validation logic.
- Do not duplicate complex transformations.
- Small local duplication is acceptable when abstraction would make the code
  harder to understand.
- Extract shared logic only when the abstraction has a clear name and a stable
  purpose.
- Avoid premature "reusable" helpers.

### Errors and exceptions

- Error messages must be useful.
- Include the offending value when safe.
- Include the expected shape, format, or allowed values.
- Do not swallow errors silently (this won't help the user nor the agent).
- Do not replace specific errors with vague generic messages.
- Preserve the original error when wrapping exceptions.

Bad:

```ts
throw new Error('Invalid input'); // now nobody knows what happened
```

Better:

```ts
throw new Error(
  `Invalid user role "${role}". Expected one of: admin, editor, viewer.`,
);
```

### Comments

- Keep existing comments unless they are clearly wrong or obsolete. Comments
  help the agent to remember **WHY** that code exists.
- Do not remove comments during refactors just because the code changed (this is
  to help the agent to remember **WHY** the code exists, not **WHAT** the code
  does).
- Comments often carry intent, history, or context.
- When you do something unusual, add **WHY** you did that in comment. That will
  help you in future rounds.

Again, write comments that explain **WHY**, not **WHAT** (we can see what the
code does).

Bad:

```ts
// Increment counter (obvious)
counter++;
```

Better:

```ts
// GitHub API may return duplicated events during pagination, so we dedupe by id. (not obvious)
seenEventIds.add(event.id);
```

- Use comments for non-obvious decisions, upstream constraints, workarounds,
  performance tradeoffs, and security concerns.
- Reference issue numbers, PRs, commit SHAs, or external bugs when a line exists
  because of a specific bug or constraint.
- Public functions should have docstrings/comments when their purpose, usage, or
  constraints are not obvious.
- Public APIs should include intent and at least one usage example when useful.

### Tests

- Tests must run with one project-specific command.

Examples:

```sh
npm test
pnpm test
uv run pytest
cargo test
go test ./...
```

- New behavior needs tests.
- Bug fixes need regression tests.
- Business rules need tests.
- Validation rules need tests.
- Public functions and public APIs should be tested through observable behavior.
- Private helper functions do not always need direct tests if they are covered
  through public behavior.
- Avoid tests that only mirror implementation details.

**Test logic, inputs, outputs, and all paths — not implementation details.**

Avoid asserting on values that change often during maintenance: versions,
timestamps, model names, prompt text, generated documentation, internal call
shapes, log strings, and similar volatile values. If a refactor that preserves
behavior breaks a test, the test was probably testing the wrong thing.

For example:

```ts
// Test should not break when we change arguments. The test should break when
// the output is not what we expected (in this case, a string with the model answer).
exec('ollama', [
  'run',
  'gpt-oss:120b',
  '--think=high',
  '--hidethinking',
  '--nowordwrap',
  'Why is the sky blue?',
]); // output: The sky appears blue due to a phenomenon...
```

Tests should be F.I.R.S.T:

- Fast
- Independent
- Repeatable
- Self-validating
- Timely

Additional testing rules:

- Mock external I/O.
- Do not call real APIs in unit tests.
- Do not depend on real databases, real filesystems, real network, or real time
  unless the test is explicitly an integration/e2e test.
- Prefer named fake classes or fixtures over anonymous inline stubs when the
  fake has behavior.
- Test names should describe behavior, not implementation.

Bad:

```ts
test('handleSubmit works', () => {});
```

Better:

```ts
test('creates a user session when credentials are valid', () => {});
```

### Dependencies

- Prefer dependency injection through parameters, constructors, or small factory
  functions.
- Avoid hidden dependencies through global state.
- Avoid importing concrete infrastructure directly into domain/business logic.
- Wrap third-party libraries when:
  - they touch business logic;
  - they are hard to test;
  - they may be replaced;
  - they spread complex types through the project;
  - they require project-specific defaults or error handling.
- Do not create wrappers for trivial library calls unless they improve clarity,
  testing, or isolation.
- Keep wrappers thin and owned by this project.

### Structure

- Follow the framework's conventions first.
- Do not fight the framework without a strong reason.
- Prefer predictable paths over personal architecture experiments.
- Keep modules small and focused.
- Avoid god files.
- Avoid generic dumping grounds like:

```txt
utils/
helpers/
common/
misc/
```

Unless the content is genuinely small, stable, and well named.

Prefer structure by responsibility/domain.

Examples:

```txt
src/users/create-user.ts
src/users/user-repository.ts
src/auth/create-session.ts
src/billing/calculate-invoice-total.ts
```

Instead of:

```txt
src/utils/user-utils.ts
src/services/manager.ts
src/helpers/index.ts
```

### Formatting

- Use the default formatter for the language/ecosystem.
- Do not manually debate formatting.
- Do not reformat unrelated files.
- Do not mix formatting-only changes with behavior changes unless explicitly
  requested.

Examples:

```sh
prettier
black
ruff format
gofmt
cargo fmt
rubocop -A
```

### Logging

- Logs for debugging and observability should be structured.
- Prefer JSON or JSONL logs in services, workers, APIs, and production systems.
- CLI output intended for humans should be plain text and readable.
- Do not leak secrets, tokens, passwords, cookies, authorization headers,
  private keys, or personal data in logs.
- Log meaningful events, not noise.
- Include useful context such as ids, operation names, durations, and failure
  reasons.
- Do not use logs as a replacement for proper error handling.

### Refactoring

- Refactor only with a clear goal.
- Do not rewrite working code just because you prefer another style.
- Keep refactors small and reviewable.
- Preserve behavior unless the task explicitly asks for behavior changes.
- Preserve public APIs unless the change is intentional.
- Preserve existing comments unless wrong or obsolete.
- Update tests when behavior changes.
- Add regression tests before or with bug fixes.

### AI / agent rules

When an AI assistant or coding agent works on this project:

- Read the relevant files before changing anything.
- Understand the current structure before proposing a new one.
- Make the smallest safe change that solves the task.
- Do not invent architecture.
- Do not add dependencies without a clear reason.
- Do not introduce frameworks, services, queues, caches, ORMs, state managers,
  or build tools unless explicitly requested.
- Do not create generic abstractions just to look clean.
- Do not rename files, functions, or public APIs unless necessary.
- Do not move code across folders unless the task requires it.
- Do not delete comments, tests, or docs unless they are wrong and the change is
  justified.
- Do not silently ignore failing tests.
- Do not claim something works without running or explaining the relevant check.
- If a command cannot be run, say so clearly.
- Prefer editing existing code over creating parallel implementations.
- Prefer project conventions over personal preferences.
- Stop and explain when the requested change conflicts with these rules.

### Before finishing a task

Verify at least:

- The code is formatted.
- The code type-checks, when applicable.
- Relevant tests pass, when available.
- New behavior has tests, when practical.
- Errors include useful context.
- No unrelated files were changed.
- No secrets or sensitive data were added.
- The final response explains what changed and what was verified.

## Communication

- Before writing code, make sure you understand what the owner wants. If the
  request is ambiguous, ask a brief clarifying question first. Even when chat is
  casual and informal.
- Explain blockers and tradeoffs plainly. Avoid corporate fluff.
- When the owner references a tool, flag, or concept, consider whether it
  belongs to the current project or to an external tool before searching or
  editing the codebase.

---

## Security / Safety Rules

Always apply these safety checks.

- Check whether `.gitignore` is correct when adding files, fixtures, generated
  output, caches, logs, or local-only artifacts.
- **NEVER COMMIT `.env` OR ANY SECRETS.**
- Never hardcode secrets or any private information.
- Never log secrets or any private information.
- Never commit `.env` files with real secrets.
- Never force-push `main`.
- No destructive git operations without explicit user confirmation.
- Validate all external input.
- Escape, sanitize, or encode user-controlled output when needed.
- Use least privilege for tokens, credentials, files, services, and database
  users.
- Treat filesystem paths, URLs, shell arguments, uploaded files, and serialized
  data as unsafe by default.
- Avoid shell execution when a safer API exists.
- When shell execution is necessary, do not concatenate unsanitized strings.

---
