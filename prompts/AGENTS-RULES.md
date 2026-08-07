# AGENTS.md

Repository map and engineering contract for humans and coding agents. Keep only
facts, constraints, commands, and decisions that change implementation. Put
branch-specific procedure in the skill that owns it and link canonical docs
instead of duplicating them here.

## Authority and scope

- `AGENTS.md` is the repository-wide source of truth. Tool-specific files should
  link here rather than duplicate it.
- A nested `AGENTS.md` may refine these rules for its subtree; the closest file
  wins within its scope.
- Tests, public contracts, configuration, domain docs, and accepted ADRs remain
  authoritative. Surface conflicts instead of choosing silently.
- Repository instructions select policy and constraints; invoked skills own their
  detailed procedure. Do not restate a skill here.
- Do not change this contract during unrelated work.

## Project map

> Replace these placeholders when adopting the file. Derive facts from the
> repository; do not invent them.

- **Purpose / non-goals:** _What the system does, for whom, and what it excludes._
- **Architecture / invariants:** _Major boundaries and properties that must hold._
- **Supported environments:** _Runtimes, platforms, and compatibility policy._
- **External systems:** _Services, protocols, schemas, and ownership boundaries._

### Canonical commands

Commands must work from the repository root. Keep one supported path per action.

```text
Bootstrap:    <command>
Run:          <command>
Focused test: <command>
Test:         <command>
Lint:         <command>
Type-check:   <command>
Format:       <command>
Build:        <command>
```

Do not introduce a second toolchain when the repository already has one.

## Agent skills

`setup-omskills` owns this section and its configuration:

- **Issue tracker:** _Where Specs and Tickets live._ See
  `docs/agents/issue-tracker.md`.
- **Triage labels:** _Labels mapped to canonical roles._ See
  `docs/agents/triage-labels.md`.
- **Domain docs:** _Glossary and ADR layout._ See `docs/agents/domain.md`.

Run setup before tracker-backed work when configuration is missing. Skills own
their invocation, gates, procedure, and completion criteria.

## Tracked work

Use the configured Issue tracker and canonical omskills language:

- A **Spec** records the durable problem, behavior, constraints, and established
  decisions. It is planning authority, never an implementation unit.
- A **Ticket** is one independently verifiable implementation slice, normally
  small enough for one fresh agent context with room to understand, implement,
  and verify it.
- A Ticket records blocking and conflict relationships. Unblocked does not imply
  safe concurrency when work shares files, contracts, artifacts, or assumptions.

The tracked issue is durable context; the final Agent Brief is its execution
contract. Together with the governing Spec and recorded relations, it must let a
clean-context agent work without reconstructing decisions from chat. Keep the
contract behavioral, testable, explicit about non-goals, and free of unnecessary
implementation prescription. Update it when shared understanding changes; a
material change makes an earlier Prompt Audit status stale.

Split work that exceeds one context into vertical Tickets. For a broad or foggy
effort, use the planning skills rather than hiding a multi-stage project inside
one Ticket.

## Delivery workflow

Classify work by behavior, risk, and coordination cost—not line count.

### Substantial changes

Use the full lifecycle for features, behavior or public-contract changes,
migrations, dependency changes, cross-module refactors, and work needing isolated
review:

1. Create or select a Ticket. Create a Spec first when the change needs planning,
   then decompose it with `to-tickets`.
2. Run `triage` to verify and stabilize the Ticket, Agent Brief, category, state,
   and relationships.
3. Run `prompt-comprehension-audits`. Autonomous implementation requires a
   current `PASS` or explicit maintainer `BYPASS` and the `ready-for-agent` state.
4. Create a dedicated branch from the current default branch.
5. Use `implement` for one authorized Ticket or `orchestrate` for a fixed audited
   queue. Keep commits focused and do not absorb adjacent findings.
6. Run required verification and `code-review` under its own contract.
7. Open a PR linked to the Ticket, normally with `closes #N`; record the approach,
   evidence, compatibility or rollout impact, and meaningful risks.
8. Complete required checks and review, squash-merge, then delete the branch.

The Ticket preserves intent and scope; the PR preserves the delivered change and
review evidence. Commit history is not the sole record because squash merge
intentionally compresses it.

### Small changes

Small, low-risk, self-contained changes still receive a focused commit. The
maintainer decides whether they need a Ticket, branch, and PR. Untracked direct
work does not acquire tracker gates merely because the skills are installed;
`implement` and `orchestrate` apply only to authorized tracked Tickets.

Escalate to the full lifecycle when behavior is ambiguous, risk is meaningful,
ownership is shared, external contracts are affected, or independent review is
valuable. Repository-specific rules may require the full lifecycle more broadly.

## Working agreement

- Before editing, read applicable instructions, tracked contracts and relations,
  relevant code and tests, configuration, domain docs, and ADRs. Inspect the
  working tree and preserve unrelated work.
- Establish current behavior and required verification. Reproduce a defect or
  identify its failing contract before fixing it.
- Ask only when ambiguity materially affects behavior, safety, compatibility, or
  scope; otherwise state the assumption and proceed.
- Make the smallest coherent change. Exclude unrelated cleanup, renames,
  formatting, upgrades, and redesign; preserve compatibility unless explicitly
  changed by the contract.
- Update tracked contracts when shared understanding changes and rerun any gate
  made stale by that change.
- Run focused checks, then required project checks. Inspect the final diff and
  update affected contracts, docs, schemas, examples, and operational notes.
- Report changes, exact verification, checks not run, and remaining risk. Never
  claim a check passed unless it was executed.

## Engineering baseline

- Prefer simple designs with clear ownership and stable interfaces. Keep business
  rules independent from transport, storage, frameworks, and I/O. Abstract only
  when the shared concept and owner are clear.
- Validate untrusted input at boundaries, normalize once, and use precise public
  contracts. Preserve error causes; never swallow failures silently.
- Make units, precision, time zones, ordering, encoding, and nullability explicit
  where ambiguity can corrupt behavior or data.
- Define and bound timeout, retry, idempotency, cancellation, concurrency,
  partial-failure, and resource behavior where applicable.
- Test observable contracts and failures, not private control flow. New behavior
  needs coverage; defects should get a regression test when practical. Keep unit
  tests deterministic and free of real external services.
- Preserve API, schema, and data compatibility by default. Migrations need rollout
  and rollback plans proportional to risk.
- Do not edit generated files manually. Explain non-obvious intent and constraints,
  not syntax.

## Safety

- Treat external data, paths, URLs, files, environment values, database rows,
  serialized data, and shell arguments as untrusted.
- Use parameterization and context-appropriate validation or escaping. Prefer
  direct APIs over shell execution; never concatenate untrusted commands or queries.
- Apply least privilege. Never commit or log secrets, tokens, sessions, real
  credentials, unnecessary personal data, or `.env` files with real values.
- Destructive filesystem, database, deployment, or Git actions require explicit
  authorization and a recovery path.
- Never discard unrelated work, rewrite shared history, bypass required checks, or
  force-push the default branch.

## Communication

- Match the user's language in chat. Use English for code, documentation, commits,
  and tracker artifacts unless the project requires another language.
- Be direct and concise. Separate facts, assumptions, and recommendations.
- Surface blockers and tradeoffs early; challenge avoidable risk with a simpler
  safe alternative.
