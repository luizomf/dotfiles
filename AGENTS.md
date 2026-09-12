# Dotfiles Guidelines

## Required checklist for every change

Before editing and again before handing off, review this checklist—even when
arriving from another project. These dotfiles are shared infrastructure: deployed
symlinks can make edits affect the live environment immediately, without running
the installer. Do not assume a change is isolated to this repository.

- [ ] **Scope and consumers:** identify affected configs, scripts, symlink targets,
  and downstream commands or projects. Check callers before changing paths,
  arguments, defaults, output formats, or environment-variable contracts.
- [ ] **Public-data safety:** review changed and newly added files for secrets,
  `.env` files, credentials, private host details, logs, and local state. Keep
  machine-specific values local; document variable names and safe placeholders
  only. Never print secret values as part of verification.
- [ ] **Dependencies and startup:** when changing packages, runtimes, images,
  assets, or external tools, check their references and consumers. Preserve
  applicable macOS/Ubuntu/Fedora behavior, executable permissions, quoting, and shared
  path overrides. For unattended commands, check explicit PATH, environment,
  working directory, and non-interactive execution assumptions.
- [ ] **Safe validation:** choose focused syntax and regression checks for the
  affected behavior (see Engineering and verification below). Do not run the
  installer, reload live configuration, or trigger remote, publishing, sync, or
  queue operations just to validate a change. Obtain explicit authorization for
  checks with those side effects; use isolated environments where practical.
- [ ] **Next-use readiness:** consider a fresh login shell, a new terminal/editor
  session, and the next unattended run, as applicable—not just the current shell.
  Identify any required restart, reload, local migration, or downstream update;
  document it rather than applying it silently.
- [ ] **Documentation consistency:** after every change, check that affected
  README sections, agent instructions, examples, and comments still match the
  implementation and tests. Correct verified discrepancies in the same change;
  prefer links to a source of truth over duplicated facts. If intent or evidence
  is unclear, report the conflict rather than inventing behavior or test results.
- [ ] **Cleanup:** before final handoff, follow [Task cleanup](#task-cleanup) for
  task-owned temporary artifacts, worktrees, and local or remote branches.
- [ ] **Handoff:** review the final diff, update affected documentation, and report
  checks run, checks skipped or not applicable, and remaining risks. If a relevant
  consumer cannot be verified, say so; do not claim the next run is guaranteed.

## Purpose and scope

This public repository contains Otávio Miranda's personal dotfiles and bootstrap
automation for macOS, Ubuntu, and traditional Fedora/Asahi. Other people also use
it, so preserve personal preferences while keeping shared setup behavior safe and
understandable.

Treat this as a personal collection of dotfiles, setup automation, and standalone
utilities—not as a unified application, product, or framework. Work on the
specific config or script requested, following its existing conventions. Do not
impose repository-wide architecture, uniform layouts, or a shared toolchain just
to make the collection look like a software project. Shared helpers are justified
by concrete needs in existing consumers, not by a desire to standardize everything.
The safety requirements here protect the real environments these files affect;
they are not a mandate to turn personal dotfiles into a supported product.

- These instructions apply repository-wide. `pi/agent/AGENTS.md` adds stricter
  rules for `pi/agent/`; follow the closest applicable `AGENTS.md`.
- `README.md` is the user-facing source for supported setup and safety warnings.
  Do not claim broader platform support than the README documents.
- `config/paths.sh` is the documented source of truth for shared host paths.
  Preserve `OM_PATHS_FILE` overrides at callers that support them.
- When documentation, tests, comments, and implementation disagree, trace the
  intended behavior, correct verified discrepancies, and report unresolved
  conflicts instead of silently choosing one.

## Repository map and boundaries

- `install.sh` installs dependencies and replaces user configuration with links
  into this checkout. `homebrew/Brewfile` is the macOS package manifest.
- `zsh/`, `tmux/`, `nvim/`, `vim/`, `ghostty/`, `fastfetch/`, and `git/` contain
  deployed application and shell configuration.
- `scripts/` contains user commands, including utilities that contact remote
  machines, cloud services, and queues. Inspect dependencies and side effects
  before changing or running one.
- `pi/agent/` contains only static Pi configuration. Credentials, sessions,
  trust decisions, generated model state, and machine-specific model settings
  must remain local, as described in `README.md`.
- `prompts/` contains reusable prompt text. `tests/` covers selected high-risk or
  complex scripts; it is not intended to cover every command or configuration.

## Safety and public data

Treat every tracked file and Git commit as public.

- Never add secrets, credentials, tokens, private keys, `.env` files, session
  data, personal logs, or other sensitive information. Do not rely on
  `.gitignore` as the only protection.
- Do not add caches, generated output, runtime artifacts, or machine-local state
  unless explicitly requested and safe for publication.
- Never run `install.sh` as a check: it is interactive and intentionally
  destructive. Do not run synchronization, upload, SSH, queue, or remote-host
  helpers without explicit authorization for their side effects.
- Installation and setup changes require extra care because they can overwrite
  files, install software, and affect users beyond the repository owner.
- Preserve unrelated personal configuration. Do not generalize, reformat, or
  "clean up" preferences outside the requested scope.

## Maintainable code and change boundaries

These guidelines apply within the dotfiles constraints above and do not expand
scope, authorize side effects, or change the test policy below.

- Solve the current requirement by simplifying existing code when practical.
  Write the minimum clear code needed; reduce what a maintainer must understand,
  not just the line count. Do not hide behavior in dense expressions or compressed
  formatting. Preserve required behavior, safety checks, and platform support.
- Make the smallest coherent change. Avoid parallel implementations, speculative
  extension points, unrelated cleanup, and new dependencies or tooling without a
  concrete need in the task.
- Use abstractions only to remove a present difficulty in use or maintenance.
  Prefer direct code over layers that merely forward calls or rename concepts.
  A function or concrete module is often enough; do not impose an application
  architecture on a small script or configuration file.
- Where scripts mix substantial decision logic with command execution, remote
  access, or storage, separate those responsibilities at a useful boundary.
  Keep external formats and execution mechanics there rather than spreading them
  through internal decisions. Use small explicit inputs and results; do not
  introduce a wrapper for every command.
- Reuse the existing configuration source for values already intended to vary by
  host or operator, preserving supported overrides and validation. Do not scatter
  duplicate defaults through callers or make every literal configurable. Shared
  host paths remain governed by `config/paths.sh` as described above.
- When a small feature requires edits across unrelated parts of the repository,
  check for unnecessary coupling. Simplify the narrow boundary when it is within
  the task; report larger cleanup separately instead of turning the change into
  a rewrite.

## Engineering and verification

- Prefer simple, explicit changes in the existing language and style. Preserve
  Bash, Zsh, POSIX shell, Python, and Lua boundaries, including whether a shell
  file is executed or sourced.
- Quote paths and arguments, validate untrusted input at boundaries, preserve
  useful error context, and explain non-obvious intent rather than narrating
  syntax.
- Do not add tests by default. Add them only for observable behavior with complex
  logic or meaningful risk that review and a syntax check would not cover.
- Do not test one-liners, simple wrappers, static values, command lists, exact
  source text, implementation details, or scripts whose purpose is already to
  perform a manual test or smoke check.
- When substantial behavior genuinely needs automated tests, use TDD. Do not
  invent low-value tests merely to claim that TDD was used.
- Keep tests focused on outcomes and plausible regressions. Prefer a few durable
  cases over exhaustive mocks of incidental internals.
- There is no repository-wide build, lint, type-check, format, or CI workflow.
  Do not invent or claim gates that are not configured.
- For changes to `scripts/bq`, run from the repository root:
  `python3 -m unittest tests/test_bq.py`.
- For other changes, use focused interpreter-specific syntax or behavior checks
  that do not alter the host. Review the final diff and report exactly what ran,
  what was skipped, and any remaining risk.

## Task cleanup

When finishing a task, remove temporary artifacts, worktrees, and branches that
this agent created for that task and no longer needs. Apply this to the local
machine, authorized remote checkouts, and branches on Git remotes.

- Establish ownership from this task's recorded actions; a matching name, age,
  clean worktree, or merged status alone does not prove ownership.
- Before removing a worktree or branch, verify its work is preserved in the
  intended target branch or another agreed durable location. Check for untracked
  files, uncommitted changes, and commits that have not been preserved. Never
  force deletion to bypass these checks.
- Never remove another agent's or the user's worktrees, branches, changes, or
  local state. If ownership, preservation, or remote authorization is uncertain,
  leave the item intact and report it rather than guessing.
- Use explicit task-owned paths and branch names, not broad deletion or pruning
  commands. Do not delete the user's primary checkout or shared target branches.
- Stop task-owned temporary processes when no longer needed. Preserve useful
  investigation notes under the [Scratch](#scratch) policy, and report any
  deliberately retained artifacts or cleanup that could not safely complete.

## Scratch

Use `./.scratch/*` for internal notes, working documents, and memory that need to
persist across sessions for days while work is ongoing. Unlike `/tmp` or ephemeral
handoffs, these files should remain available while useful. They are local-only,
not repository deliverables: never commit them, and remove them only when no
longer needed.
