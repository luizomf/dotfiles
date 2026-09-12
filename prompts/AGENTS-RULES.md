# AGENTS.md

Repository-specific map and engineering contract for humans and coding agents.
Keep only facts, constraints, commands, and decisions that materially affect
work in this repository. Replace every placeholder when adopting this template,
remove inapplicable entries, and do not present aspirational tooling as if it
already exists.

## Simplicity and change boundaries

Prefer solving the current requirement by removing or simplifying existing code
before adding new structures. When adding code, write the minimum clear code
needed. Reduce what must be understood and maintained, not just the line count.
Preserve required behavior, security, and applicable checks; keep cleanup scoped
to the task.

- Prefer the shorter solution when both are equally clear and reliable. Add lines
  for a concrete gain in readability, explicit control flow, removal of duplication,
  or isolation of an actual dependency. Do not shorten by hiding behavior in dense
  expressions or compressing formatting.
- Use patterns and architecture to simplify a present difficulty in use or
  maintenance. Each new layer must identify the difficulty it removes. Prefer
  direct code over layers that only forward calls or rename concepts without
  simplifying a real boundary. No framework or directory layout is prescribed.
- Keep values the product already allows operators to change—such as contact
  addresses or selected targets—in configuration, not scattered implementation
  constants. Updating these values may edit configuration files, but should not
  require implementation or schema changes. Do not make every literal configurable.
  Preserve validation, authorization, and identity checks.
- Keep domain and workflow rules independent of infrastructure details. Adapters
  own external services, command execution, and storage mechanics; internal rules
  own behavior and decisions. Persist required state without spreading database
  layout or transport formats throughout the application.
- Connect these responsibilities through small explicit interfaces at real change
  boundaries. A function or concrete module may be enough. Do not give every class
  an interface or introduce extension points for hypothetical features.
- Test observable behavior with synthetic data and configuration. Verify external
  service and persistence contracts at their boundaries; ordinary rule tests
  should not require live infrastructure or mirror production configuration.
- Make the smallest coherent change. Avoid parallel implementations, speculative
  extension points, unrelated cleanup, and new tooling without a concrete need.
  Simplicity does not mean weakening correctness, security, or applicable checks.
- When a small feature requires changes across unrelated layers, identify the
  coupling and fix the narrow boundary when practical. Record larger cleanup
  separately rather than turning feature delivery into a system rewrite.

## Authority and scope

- This file applies repository-wide. Use the most specific applicable `AGENTS.md`
  for subtree details. Surface conflicts with repository-wide invariants or
  higher-priority instructions rather than silently treating specificity as
  permission to override them.
- Identify the canonical sources for product behavior, domain language,
  architecture decisions, schemas, generated artifacts, and operations below.
  These sources have distinct roles; surface conflicts instead of silently
  choosing one.
- Repository instructions define local policy and constraints. Invoked skills
  own their procedures; link them rather than duplicating their instructions.
- Do not change this contract during unrelated work.

## Project map

> Replace or remove every italicized prompt. Record repository evidence, not
> assumptions.

- **Purpose and non-goals:** _What the system does, for whom, and what it
  intentionally excludes._
- **Architecture and invariants:** _Major boundaries and properties that must
  remain true._
- **Canonical domain and product docs:** _Paths to source-of-truth terminology,
  behavior, specifications, and architecture decisions._
- **Supported environments:** _Runtimes, platforms, versions, and compatibility
  policy._
- **External systems and trust boundaries:** _Services, protocols, schemas,
  sensitive boundaries, and ownership._
- **Generated artifacts:** _Generated paths, their source inputs, and the
  command that regenerates them._

## Canonical commands

Record the primary supported commands that work from the repository root.
Commands may delegate to package- or platform-specific scripts. Add rows for
real test layers or workspaces; mark an unsupported action `N/A` with a reason
rather than leaving a placeholder in an adopted file.

```text
Bootstrap:       <command>
Run:             <command>
Focused test:    <command>
Test:            <command>
Lint / smells:   <command>
Type-check:      <command>
Complexity:      <command>
Format check:    <command>
Format write:    <command>
Docs check:      <command>
Build:           <command>
```

Use the repository's established toolchain. Do not introduce overlapping tools
or a second command path without a concrete gap the existing setup cannot fill.

## Mechanical quality gates

For production and other long-lived projects, establish automated feedback
before substantial implementation accumulates. During authorized project or
quality-tooling setup, use tools appropriate to the language and stack and check
their settings into the repository. Adopting this template documents the contract;
it does not itself authorize installing missing tools during unrelated maintenance.

Configure every applicable category:

- tests for observable behavior and important failure paths;
- strict static type checking where the language and ecosystem support it;
- formatting checked without mutation in verification workflows;
- linting that covers correctness risks, suspicious constructs, and maintainable
  style rather than cosmetics already owned by the formatter;
- a measurable complexity rule, including cyclomatic complexity where supported;
- documentation checks or builds when documentation has executable structure,
  links, schemas, generated references, or examples that can drift; and
- build or packaging validation for delivered artifacts.

Gates must return a failing status for violations they own. New projects should
start with strict settings instead of accumulating an avoidable cleanup backlog.
Use narrow, documented exceptions only when the rule is unsuitable for the code;
do not use broad disables, blanket ignores, or warning suppression merely to
make a gate pass.

Behavior changes, including bug fixes, require caller-visible tests covering the
changed outcome and important failure paths. Report concrete obstacles to these
checks without claiming unverified behavior is verified. Keep affected source-of-truth
documentation, schemas, examples, generated references, and operational guidance
synchronized with the same change.

### Existing-project ratchet

When strict repository-wide adoption would fail on legacy code:

- do not weaken or remove a gate that already passes;
- require new and materially changed code to meet the target standard;
- use the tool's narrowest practical baseline, scoped configuration, or changed-
  code enforcement to isolate pre-existing violations without exempting new
  debt;
- record broad cleanup as separate work instead of absorbing it into an
  unrelated change; and
- tighten or remove temporary baselines and exclusions as the affected legacy
  code is intentionally migrated.

Do not build a production-grade toolchain for a throwaway experiment. Match
prototype checks to its lifetime and risk, and establish the applicable
production baseline before promoted code becomes maintained product code.

## Working agreement

- Before editing, read applicable instructions, canonical docs, configuration,
  relevant code and tests, and current worktree state. Preserve unrelated work.
- Before reviewing, updating, or commenting on a pull request, verify its current
  state. Treat merged or closed pull requests as read-only historical records:
  do not modify or comment on them unless explicitly requested. Record follow-up
  work in a new issue or pull request.
- Establish current behavior and the applicable verification path before making
  a behavior change. Reproduce reported defects when practical.
- Prefer test-driven development for code changes: write a caller-visible test
  first, confirm it fails for the intended reason, implement only enough to make
  it pass, and then refactor while keeping the tests green. When this workflow
  is impractical, explain why and still add the applicable tests.
- Make the smallest coherent change. Exclude unrelated cleanup, formatting,
  upgrades, renames, and redesign.
- Run focused checks during development, then every applicable canonical gate
  before handoff. Never claim a check passed unless it was executed.
- If an expected gate is absent, do not invent success or silently expand the
  current task. Report the gap and recommend separate setup work when warranted.
- Inspect the final diff and report changes, exact verification, skipped checks,
  documented exceptions, and remaining risk.

## Project-specific constraints

> Replace these prompts with constraints supported by this repository. Delete
> the section if no additional constraints remain.

- **Compatibility:** _Public API, schema, data, migration, rollout, and rollback
  commitments._
- **Data and error semantics:** _Required units, precision, ordering, encoding,
  nullability, error propagation, and partial-failure behavior._
- **Security and privacy:** _Actual untrusted boundaries, sensitive data,
  prohibited artifacts, and destructive operations requiring authorization._
- **Documentation language and format:** _Language, style, generated-doc rules,
  and documents that must change with affected behavior._

## Scratch

Use `./.scratch/*` for internal notes, working documents, and memory that need
to persist across sessions for days while work is ongoing. Unlike `/tmp` or
ephemeral handoffs, these files should remain available while useful. They are
local-only, not repository deliverables: never commit them, and remove them only
when no longer needed. MUST BE IGNORED BY `.gitignore`.
