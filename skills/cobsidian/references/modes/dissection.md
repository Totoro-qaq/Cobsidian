# Dissection Mode

## When to Use

Use `dissection` when the durable value comes from explaining why a specific product, technology, repository, framework, skill, prompt system, or workflow exists; how its internals turn design choices into outcomes; what changed after adoption; and where its advantages and limits come from. An ordinary explanation remains `learning` unless a specific object's causal chain and internals are central. If the main goal is choosing among options against the user's Requirements, use `comparison`; in dissection, horizontal and vertical comparisons are evidence supporting the analysis of one primary object.

## Required Inputs

Identify the Object and Scope, relevant version or time window, the user's main question, accessible source or artifacts, desired depth, and the mechanisms worth reusing. Also identify the Problem and Prior State, available before/after evidence, meaningful horizontal peers, the vertical baseline such as a predecessor or earlier version, and shared Evaluation Dimensions. Missing comparison candidates or evidence do not justify invented conclusions: record the gap, ask only when it changes the scope materially, and otherwise proceed with explicit unknowns.

## Default Knowledge Read

- Default depth: `deep`
- Default granularity: `multi-note`

Keep the default evidence at `conversation`; selecting a source-oriented mode never proves that source material, competitor evidence, historical versions, or outcome measurements were actually read.

## Recommended Note Shape

Use an overview with `Object and Scope`, `Problem and Prior State`, `Solution Thesis`, `Mechanism Chain`, `Adoption Effects`, `Horizontal Comparison`, `Vertical Evolution`, `Distinctive Advantages`, `Trade-offs and Limits`, `Reusable Patterns`, `Evidence and Open Questions`, and `Related Notes`.

Build the `Mechanism Chain` as `problem -> design choice -> mechanism -> outcome -> evidence`. Assess only applicable `Adoption Effects` such as capability, quality, cost, latency, user experience, operations, and risk, including new costs or regressions. `Horizontal Comparison` compares contemporary peers through the same dimensions. `Vertical Evolution` compares the prior approach, predecessor, or earlier version through time. Express each `Distinctive Advantage` as `differentiator -> causal mechanism -> conditions -> evidence` rather than repeating positioning copy. Child notes should each own one independently reusable mechanism, comparison, or evolution thread while the overview preserves the causal chain.

## Append, Single-Note, and Split Criteria

- **Append** when an existing dissection owns the same primary object and compatible version scope, and the new material extends a documented mechanism, comparison, evolution step, or outcome claim.
- **Single-note** when the object's problem, solution, mechanism chain, before/after effects, and comparisons remain coherent and maintainable together.
- **Split** when mechanisms, components, competitors, versions, or adoption evidence have independent source trails or reuse value; keep an overview that links every child note and states the conclusions that survive across them.

## Evidence Rules

Start at `conversation`. Upgrade to `source-grounded` only after reading relevant source code, prompts, configuration, traces, documentation, benchmarks, case studies, release history, or primary competitor material. Use `verified` only after tests, execution traces, reproducible benchmarks, or equivalent checks confirm the described mechanism or outcome. These are host-completed facts: submit `source_read_completed=true` for source grounding and both `source_read_completed=true` and `verification_completed=true` for verified evidence; mode choice or a user claim cannot set them.

Treat problem statements, prior-state descriptions, adoption effects, and competitive claims as separate evidence-bearing claims. Label each material claim as observed, claimed, inferred, or unknown when the distinction matters. Compare peers at compatible versions, scopes, deployment models, and Evaluation Dimensions; anchor vertical comparisons to named versions, dates, or prior approaches. Never turn missing measurements into a benefit, a marketing statement into a verified advantage, or an unmatched feature list into a fair comparison.

## Mode-Specific Validation

Verify the Object and Scope, problem and prior state, entry points, causal Mechanism Chain, component names, source locations, version assumptions, and every claimed Adoption Effect. Check that Horizontal Comparison applies shared Evaluation Dimensions, Vertical Evolution has a real time or version baseline, Distinctive Advantages follow from evidence, trade-offs remain visible, unsupported claims are labeled, and all emitted wiki links resolve to existing notes.

## Completion Report Additions

Report the studied object and version scope, sources and entry points examined, Problem and Prior State, mechanisms extracted, Adoption Effects, horizontal peers, vertical baseline, supported advantages, trade-offs, overview and child-note decisions, evidence level, verification performed, and every unresolved or unsupported claim.
