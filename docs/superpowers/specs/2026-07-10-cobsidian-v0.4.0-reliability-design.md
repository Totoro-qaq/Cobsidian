# Cobsidian v0.4.0 Reliability Design

## Status

Approved for implementation on 2026-07-10.

## Goal

Make the public Cobsidian skill reliably discoverable, consistent across CLI and MCP entry points, honest about enforced configuration, and safe to use with larger Markdown vaults.

## Scope

The release fixes five verified issues:

1. Invalid YAML frontmatter in `skills/cobsidian/SKILL.md` and missing CI coverage for skill metadata.
2. Different backlink results between dry-run, CLI, and MCP, plus weak matching for Chinese text.
3. Example configuration fields that look enforced but are only advisory or unused.
4. Unbounded MCP scan responses and expensive duplicate-title comparison on large vaults.
5. A personal `superpowers` instruction in the public Claude/OpenCode adapter.

## Chosen Approach

Use a dependency-light reliability release rather than introducing semantic-vector infrastructure or a write engine.

- Keep Python 3.11 and the existing standard-library-first script design.
- Add PyYAML only as a development validation dependency, not a runtime requirement.
- Share lexical retrieval code across CLI, dry-run, and MCP.
- Improve Chinese matching with deterministic overlapping CJK bigrams and trigrams.
- Page MCP scan responses and cap similar-title candidate evaluation with explicit truncation metadata.
- Remove unsupported configuration fields from the public example instead of pretending they are enforced.

## Alternatives Considered

### External Chinese tokenizer

Using `jieba` would improve word segmentation in some cases but would add a runtime dependency and language-specific dictionary behavior. CJK n-grams are less linguistically precise but deterministic, portable, and sufficient for backlink candidate discovery.

### Embedding or vector search

Semantic embeddings would improve recall, but they require model selection, caching, storage, and privacy decisions. That is disproportionate for a small local skill and remains outside `v0.4.0`.

### Implement every example config option

Implementing naming engines, token redaction, rewrite approval, and full report customization would require a deterministic write layer that Cobsidian does not yet expose. The safer fix is to publish only settings currently enforced by scripts and MCP tools.

## Architecture

### Skill metadata validation

Quote or fold the `description` value so it is valid YAML and remains trigger-focused. Add a repository validation script that parses the frontmatter with PyYAML, validates the required fields, and checks the skill directory name. Run it in unit tests and GitHub Actions.

### Shared retrieval module

Create `skills/cobsidian/scripts/retrieval.py` as the single owner of:

- English and technical-token normalization.
- CJK bigram/trigram generation.
- Note search-document construction from title, tags, wiki links, and body text.
- Backlink ranking and deterministic tie-breaking.

`suggest_backlinks.py`, `dry_run.py`, and `mcp_server.py` must all call this module. Dry-run must read note bodies through the resolved vault path so all three entry points rank the same corpus.

### Configuration contract

The example config will contain only settings consumed by `CobsidianConfig`:

- `vault.path`
- `defaults.mode`
- `notes.directories`
- `linking.max_suggested_backlinks`
- `duplicates.similar_title_threshold`
- `duplicates.prefer_append_over_duplicate`
- `validation.run_after_write`
- `validation.strict`

Documentation will explicitly call this the supported `v0.4.0` configuration surface. Naming, redaction, templates, and write-policy customization stay in the roadmap.

### Large-vault boundaries

MCP `cobsidian_scan_vault` will accept `offset` and `limit`, return `total_note_count`, and include page metadata. The default page size will be bounded, with input validation for negative or excessive values.

Similar-title discovery will use a configurable maximum number of candidate comparisons. Results will include `truncated` and `comparisons` metadata when the cap is reached. Exact-title detection remains complete and linear.

The dry-run path remains a full vault scan because it needs a global create/append decision, but it returns only bounded backlink and duplicate results. Persistent indexes and caches are non-goals for this release.

### Public adapter cleanup

Remove project-owner-specific workflow instructions from `agents/claude.md`. The adapter will only describe how Claude Code/OpenCode discovers Cobsidian and how to invoke its MCP server.

## Data Flow

1. Resolve vault and supported config.
2. Scan Markdown metadata.
3. Select or infer the note mode.
4. Detect exact and bounded similar-title risks.
5. Build one shared retrieval query from topic and material.
6. Rank existing notes from title, metadata, and body text.
7. Return a dry-run plan with no writes.
8. After an external host writes, run validation and report results.

## Error Handling

- Invalid skill frontmatter fails CI with a clear file and parser message.
- Invalid pagination values raise `ValueError` in MCP functions and non-zero CLI errors where applicable.
- Candidate truncation is reported, not silently hidden.
- Missing or invalid vault/config paths retain the current explicit errors.
- Unreadable UTF-8 Markdown retains replacement-character fallback behavior.

## Testing Strategy

Follow RED-GREEN-REFACTOR for every behavior change.

- Frontmatter test must fail against the current unquoted description.
- Retrieval tests must prove CJK phrase overlap and identical CLI/dry-run/MCP backlink ordering.
- Dry-run regression test must find a backlink whose signal exists only in note body text.
- Config contract test must reject unsupported example keys.
- MCP tests must cover pagination bounds, total counts, deterministic pages, and duplicate truncation metadata.
- Adapter hygiene test must reject the personal `superpowers` instruction.
- Run the full unit suite, compileall, example scripts, skill validator, and `git diff --check` before release.
- Forward-test the revised skill with a fresh agent using a read-only demo vault.

## Release Process

1. Implement on `release/v0.4.0` with focused commits.
2. Update English and Chinese documentation plus `CHANGELOG.md`.
3. Open a pull request to `main` and wait for validation and CodeQL.
4. Squash-merge after checks pass.
5. Tag the merged commit as `v0.4.0` and create a GitHub release.
6. Replace the locally installed `v0.3.0` skill with the released `v0.4.0` copy and validate it.

## Non-Goals

- MCP write tools.
- Embedding models or vector databases.
- Persistent indexes or background daemons.
- Full Obsidian YAML frontmatter parsing.
- A general secret-scanning or redaction engine.
- A configurable Markdown naming/template engine.

## Acceptance Criteria

- The skill passes YAML/frontmatter validation on Windows and Linux.
- CLI, dry-run, and MCP produce the same ranked backlinks for the same input and vault.
- Chinese related phrases produce overlapping retrieval tokens.
- The example config contains no unenforced options.
- MCP scan output is paginated and duplicate comparison caps are observable.
- Public adapter instructions contain no personal workflow rules.
- All tests and GitHub checks pass.
- `v0.4.0` is published and the local Codex installation validates successfully.
