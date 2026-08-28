# AGENTS.md

Repository-specific map and engineering contract for humans and coding agents.
Keep only facts, constraints, commands, and decisions that materially affect
work in this repository. Replace every placeholder when adopting this template,
remove inapplicable entries, and do not present aspirational tooling as if it
already exists.

## Authority and scope

- This file applies repository-wide. A nested `AGENTS.md` may refine it for its
  subtree; the closest applicable file wins.
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
- **Generated artifacts:** _Generated paths, their source inputs, and the command
  that regenerates them._

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
before substantial implementation accumulates. Use tools appropriate to the
language and stack, and check their settings into the repository.

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

Behavior changes require tests at a caller-visible seam. Bug fixes should add a
regression test when a practical seam exists. Keep affected source-of-truth
documentation, schemas, examples, generated references, and operational guidance
synchronized with the same change.

### Existing-project ratchet

When strict repository-wide adoption would fail on legacy code:

- do not weaken or remove a gate that already passes;
- require new and materially changed code to meet the target standard;
- use the tool's narrowest practical baseline, scoped configuration, or changed-
  code enforcement to isolate pre-existing violations without exempting new debt;
- record broad cleanup as separate work instead of absorbing it into an unrelated
  change; and
- tighten or remove temporary baselines and exclusions as the affected legacy
  code is intentionally migrated.

Do not build a production-grade toolchain for a throwaway experiment. Match
prototype checks to its lifetime and risk, and establish the applicable
production baseline before promoted code becomes maintained product code.

## Working agreement

- Before editing, read applicable instructions, canonical docs, configuration,
  relevant code and tests, and current worktree state. Preserve unrelated work.
- Establish current behavior and the applicable verification path before making
  a behavior change. Reproduce reported defects when practical.
- Prefer test-driven development for code changes: write a caller-visible test
  first, confirm it fails for the intended reason, implement only enough to make
  it pass, and then refactor while keeping the tests green. When this workflow is
  impractical, explain why and still add the applicable tests.
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
