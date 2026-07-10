# Cobsidian v0.4.0 Reliability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship Cobsidian `v0.4.0` with valid skill metadata, consistent multilingual backlink retrieval, an honest configuration contract, bounded large-vault MCP behavior, and clean public adapters.

**Architecture:** Add small shared modules for skill validation, retrieval, and bounded duplicate discovery. Keep runtime behavior local and dependency-light; PyYAML is a development-only validator. Preserve the read-only MCP boundary and existing dry-run write contract.

**Tech Stack:** Python 3.11, `unittest`, PyYAML for development validation, FastMCP, GitHub Actions, GitHub CLI.

---

## File Map

- Create `requirements-dev.txt`: development-only validation dependency.
- Create `skills/cobsidian/scripts/validate_skill.py`: parse and validate Agent Skill frontmatter.
- Create `skills/cobsidian/scripts/retrieval.py`: shared multilingual tokenization and backlink ranking.
- Create `skills/cobsidian/scripts/duplicates.py`: bounded exact/similar-title discovery.
- Modify `skills/cobsidian/SKILL.md`: valid, trigger-focused YAML description.
- Modify `skills/cobsidian/scripts/dry_run.py`: use shared body-aware retrieval.
- Modify `skills/cobsidian/scripts/suggest_backlinks.py`: use shared retrieval.
- Modify `skills/cobsidian/scripts/find_duplicates.py`: use bounded duplicate discovery.
- Modify `skills/cobsidian/mcp_server.py`: shared retrieval, scan pagination, duplicate metadata.
- Modify `skills/cobsidian/scripts/cobsidian_config.py`: publish the supported config-key contract.
- Modify `cobsidian.config.example.yml`: contain only enforced settings.
- Modify `skills/cobsidian/agents/claude.md`: remove owner-specific workflow rules.
- Modify `.github/workflows/validate.yml`: install dev requirements and validate the skill.
- Modify tests under `tests/`: cover every new contract and regression.
- Modify English/Chinese docs and `CHANGELOG.md`: document `v0.4.0` behavior and limits.

### Task 1: Make Skill Metadata Valid and CI-Enforced

**Files:**
- Create: `requirements-dev.txt`
- Create: `skills/cobsidian/scripts/validate_skill.py`
- Create: `tests/test_skill_validation.py`
- Modify: `skills/cobsidian/SKILL.md:1-4`
- Modify: `.github/workflows/validate.yml:17-22`

- [ ] **Step 1: Write the failing frontmatter tests**

```python
from pathlib import Path
import unittest

from skills.cobsidian.scripts.validate_skill import validate_skill


REPO_ROOT = Path(__file__).resolve().parents[1]


class SkillValidationTests(unittest.TestCase):
    def test_cobsidian_skill_has_valid_frontmatter(self) -> None:
        result = validate_skill(REPO_ROOT / "skills" / "cobsidian")
        self.assertEqual([], result.errors)

    def test_description_is_trigger_focused(self) -> None:
        result = validate_skill(REPO_ROOT / "skills" / "cobsidian")
        self.assertTrue(result.description.startswith("Use when"))
        self.assertLessEqual(len(result.description), 500)
```

- [ ] **Step 2: Run the tests and verify RED**

Run: `python -m unittest tests.test_skill_validation -v`

Expected: FAIL because `validate_skill.py` does not exist; after adding only the validator, FAIL with the current YAML `mapping values are not allowed here` error.

- [ ] **Step 3: Add the development dependency and validator**

`requirements-dev.txt`:

```text
PyYAML>=6.0,<7
```

`validate_skill.py` must expose these exact types and functions:

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

import yaml


@dataclass(frozen=True)
class SkillValidationResult:
    name: str
    description: str
    errors: list[str]


def validate_skill(skill_dir: Path) -> SkillValidationResult:
    skill_path = skill_dir / "SKILL.md"
    text = skill_path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return SkillValidationResult("", "", ["SKILL.md must start with YAML frontmatter."])

    parts = text.split("---", 2)
    if len(parts) != 3:
        return SkillValidationResult("", "", ["SKILL.md frontmatter is not closed."])

    try:
        metadata = yaml.safe_load(parts[1])
    except yaml.YAMLError as exc:
        return SkillValidationResult("", "", [f"Invalid YAML frontmatter: {exc}"])

    if not isinstance(metadata, dict):
        return SkillValidationResult("", "", ["Frontmatter must be a mapping."])

    name = str(metadata.get("name", "")).strip()
    description = str(metadata.get("description", "")).strip()
    errors: list[str] = []
    if name != skill_dir.name:
        errors.append("Skill name must match its directory name.")
    if not description:
        errors.append("Skill description is required.")
    return SkillValidationResult(name, description, errors)


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: validate_skill.py <skill-directory>", file=sys.stderr)
        return 2
    result = validate_skill(Path(sys.argv[1]))
    if result.errors:
        for error in result.errors:
            print(error, file=sys.stderr)
        return 1
    print("Skill is valid!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Replace the frontmatter description with valid folded YAML**

```yaml
---
name: cobsidian
description: >-
  Use when a user asks to organize, save, compare, review, map, or dissect
  conversations and source material into an Obsidian vault or Markdown
  knowledge base, including Chinese requests about knowledge notes, wiki links,
  learning notes, project notes, reviews, comparisons, indexes, capture, or
  source dissection.
---
```

- [ ] **Step 5: Add validation to CI**

Change the dependency step to install both requirement files and add:

```yaml
      - name: Validate Agent Skill metadata
        run: python skills/cobsidian/scripts/validate_skill.py skills/cobsidian
```

- [ ] **Step 6: Verify GREEN and commit**

Run:

```powershell
python -m pip install -r requirements-dev.txt
python -m unittest tests.test_skill_validation -v
python skills/cobsidian/scripts/validate_skill.py skills/cobsidian
```

Expected: all tests pass and output includes `Skill is valid!`.

Commit: `fix: validate Cobsidian skill metadata`

### Task 2: Add Shared Multilingual Retrieval

**Files:**
- Create: `skills/cobsidian/scripts/retrieval.py`
- Create: `tests/test_retrieval.py`

- [ ] **Step 1: Write failing multilingual retrieval tests**

```python
from pathlib import Path
import tempfile
import unittest

from skills.cobsidian.scripts.retrieval import (
    SearchDocument,
    rank_backlinks,
    tokenize,
)


class RetrievalTests(unittest.TestCase):
    def test_chinese_related_phrases_share_tokens(self) -> None:
        long_text = tokenize("向量数据库使用嵌入模型进行语义检索")
        phrase = tokenize("嵌入模型")
        self.assertTrue(set(long_text) & set(phrase))

    def test_rank_backlinks_uses_body_and_stable_tie_breaking(self) -> None:
        documents = [
            SearchDocument("Vector Search", "Vector Search.md", "semantic retrieval through embeddings"),
            SearchDocument("Agent Workflows", "Agent Workflows.md", "agents inspect context and validate"),
        ]
        ranked = rank_backlinks("semantic retrieval embeddings", documents, limit=5)
        self.assertEqual(["Vector Search.md"], [item.path for item in ranked])
```

- [ ] **Step 2: Run the tests and verify RED**

Run: `python -m unittest tests.test_retrieval -v`

Expected: FAIL because `retrieval.py` does not exist.

- [ ] **Step 3: Implement deterministic shared retrieval**

Implement these public types/functions:

```python
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass


LATIN_TOKEN_RE = re.compile(r"[A-Za-z0-9_+\-.#]{2,}")
CJK_RUN_RE = re.compile(r"[\u4e00-\u9fff]{2,}")
STOPWORDS = {"the", "and", "for", "with", "from", "this", "that", "into", "note", "notes"}


@dataclass(frozen=True)
class SearchDocument:
    title: str
    path: str
    text: str


@dataclass(frozen=True)
class RankedBacklink:
    title: str
    path: str
    score: int


def cjk_ngrams(run: str) -> list[str]:
    grams: list[str] = []
    for size in (2, 3):
        if len(run) < size:
            continue
        grams.extend(run[index : index + size] for index in range(len(run) - size + 1))
    return grams


def tokenize(text: str) -> Counter[str]:
    tokens = [
        token.casefold()
        for token in LATIN_TOKEN_RE.findall(text)
        if token.casefold() not in STOPWORDS
    ]
    for run in CJK_RUN_RE.findall(text):
        tokens.extend(cjk_ngrams(run))
    return Counter(tokens)


def rank_backlinks(query: str, documents: list[SearchDocument], limit: int) -> list[RankedBacklink]:
    query_tokens = tokenize(query)
    ranked: list[RankedBacklink] = []
    for document in documents:
        document_tokens = tokenize(f"{document.title}\n{document.text}")
        score = sum(min(count, document_tokens[token]) for token, count in query_tokens.items())
        if score > 0:
            ranked.append(RankedBacklink(document.title, document.path, score))
    return sorted(ranked, key=lambda item: (-item.score, item.path.casefold()))[:limit]
```

Exclude only exact English stopword tokens, not CJK n-grams.

- [ ] **Step 4: Verify GREEN and commit**

Run: `python -m unittest tests.test_retrieval -v`

Expected: 2 tests pass.

Commit: `feat: add shared multilingual backlink retrieval`

### Task 3: Use One Retrieval Path in CLI, Dry-Run, and MCP

**Files:**
- Modify: `skills/cobsidian/scripts/suggest_backlinks.py`
- Modify: `skills/cobsidian/scripts/dry_run.py`
- Modify: `skills/cobsidian/mcp_server.py`
- Modify: `tests/test_config_and_dry_run.py`
- Modify: `tests/test_mcp_server.py`
- Create: `tests/test_retrieval_entrypoints.py`

- [ ] **Step 1: Write failing body-aware and parity tests**

Add a dry-run regression where the only matching signal is in `Vector Search.md` body:

```python
def test_dry_run_uses_note_body_for_backlinks(self) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        vault_path = Path(temp_dir)
        (vault_path / "Vector Search.md").write_text(
            "# Vector Search\n\nSemantic retrieval through embeddings.\n",
            encoding="utf-8",
        )
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS_DIR / "dry_run.py"),
                str(vault_path),
                "--topic",
                "Retrieval Pipeline",
                "--text",
                "semantic retrieval through embeddings",
                "--json",
            ],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        payload = json.loads(result.stdout)
        self.assertEqual("Vector Search.md", payload["suggested_backlinks"][0]["path"])
```

Add this entrypoint parity test:

```python
from pathlib import Path
import tempfile
import unittest

from skills.cobsidian.mcp_server import tool_cobsidian_suggest_backlinks
from skills.cobsidian.scripts.cobsidian_config import CobsidianConfig
from skills.cobsidian.scripts.dry_run import build_payload
from skills.cobsidian.scripts.retrieval import build_search_documents, rank_backlinks
from skills.cobsidian.scripts.scan_vault import scan_vault


class RetrievalEntrypointTests(unittest.TestCase):
    def test_dry_run_mcp_and_shared_ranker_return_same_order(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir)
            (vault / "Vector Search.md").write_text(
                "# Vector Search\n\nSemantic retrieval through embeddings.\n",
                encoding="utf-8",
            )
            (vault / "Agent Workflows.md").write_text(
                "# Agent Workflows\n\nAgents validate retrieval workflows.\n",
                encoding="utf-8",
            )
            query = "semantic retrieval embeddings"
            notes = scan_vault(vault)
            dry_run = build_payload(
                vault,
                CobsidianConfig(config_path=None, raw={}),
                "Retrieval Pipeline",
                "learning",
                query,
                notes,
            )
            mcp = tool_cobsidian_suggest_backlinks(vault=str(vault), text=query)
            shared = rank_backlinks(query, build_search_documents(vault, notes), limit=8)

            self.assertEqual(
                [item["path"] for item in dry_run["suggested_backlinks"]],
                [item["path"] for item in mcp["suggestions"]],
            )
            self.assertEqual(
                [item["path"] for item in mcp["suggestions"]],
                [item.path for item in shared],
            )
```

- [ ] **Step 2: Run focused tests and verify RED**

Run:

```powershell
python -m unittest tests.test_config_and_dry_run tests.test_mcp_server tests.test_retrieval_entrypoints -v
```

Expected: FAIL because dry-run still searches only title/tag/link metadata.

- [ ] **Step 3: Build search documents from full note content**

In `retrieval.py`, add:

```python
from pathlib import Path
from typing import Iterable, Protocol


class NoteLike(Protocol):
    path: str
    title: str
    tags: list[str]
    wikilinks: list[str]


def read_utf8(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def build_search_documents(vault_path: Path, notes: Iterable[NoteLike]) -> list[SearchDocument]:
    documents: list[SearchDocument] = []
    for note in notes:
        body = read_utf8(vault_path / note.path)
        metadata = " ".join([*note.tags, *note.wikilinks])
        documents.append(SearchDocument(note.title, note.path, f"{metadata}\n{body}"))
    return documents
```

Define a typed `NoteLike` protocol and a local UTF-8 replacement fallback so the module does not import `scan_vault` and create a cycle.

- [ ] **Step 4: Replace all three ranking implementations**

- `suggest_backlinks.py`: build documents and call `rank_backlinks`.
- `dry_run.py`: accept `vault_path`, build documents, exclude the append target, and call `rank_backlinks`.
- `mcp_server.py`: call the same functions and serialize `RankedBacklink` with `asdict`.

Remove duplicate `TOKEN_RE`, `STOPWORDS`, `tokenize`, and `score_note` implementations from the entrypoint files.

- [ ] **Step 5: Verify GREEN and commit**

Run:

```powershell
python -m unittest tests.test_retrieval tests.test_config_and_dry_run tests.test_mcp_server tests.test_retrieval_entrypoints -v
```

Expected: all focused tests pass with identical backlink ordering.

Commit: `fix: unify backlink retrieval across entrypoints`

### Task 4: Publish Only Enforced Configuration

**Files:**
- Modify: `skills/cobsidian/scripts/cobsidian_config.py`
- Modify: `cobsidian.config.example.yml`
- Create: `tests/test_config_contract.py`
- Modify: `README.md`
- Modify: `docs/README.zh-CN.md`
- Modify: `INSTALL.md`
- Modify: `examples/prompts.md`

- [ ] **Step 1: Write a failing supported-key contract test**

```python
from pathlib import Path
import unittest

from skills.cobsidian.scripts.cobsidian_config import (
    SUPPORTED_CONFIG_LEAF_PATHS,
    flatten_leaf_paths,
    parse_simple_yaml,
)


class ConfigContractTests(unittest.TestCase):
    def test_example_contains_only_supported_keys(self) -> None:
        config_path = Path(__file__).resolve().parents[1] / "cobsidian.config.example.yml"
        parsed = parse_simple_yaml(config_path.read_text(encoding="utf-8"))
        self.assertEqual(SUPPORTED_CONFIG_LEAF_PATHS, flatten_leaf_paths(parsed))
```

- [ ] **Step 2: Run the test and verify RED**

Run: `python -m unittest tests.test_config_contract -v`

Expected: FAIL because the constants/functions do not exist and the example advertises unused keys.

- [ ] **Step 3: Define the supported config contract**

```python
SUPPORTED_CONFIG_LEAF_PATHS = {
    "vault.path",
    "defaults.mode",
    "notes.directories.learning",
    "notes.directories.project",
    "notes.directories.review",
    "notes.directories.comparison",
    "notes.directories.index",
    "notes.directories.capture",
    "notes.directories.dissection",
    "linking.max_suggested_backlinks",
    "duplicates.similar_title_threshold",
    "duplicates.prefer_append_over_duplicate",
    "validation.run_after_write",
    "validation.strict",
}


def flatten_leaf_paths(data: ConfigData, prefix: str = "") -> set[str]:
    paths: set[str] = set()
    for key, value in data.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            paths.update(flatten_leaf_paths(value, path))
        else:
            paths.add(path)
    return paths
```

- [ ] **Step 4: Reduce the example and correct public wording**

Keep only the supported fields. Replace claims about naming, redaction, and report customization with explicit `v0.4.0` supported-key language. Keep future naming, templates, redaction, and write policy in the roadmap.

- [ ] **Step 5: Verify GREEN and commit**

Run:

```powershell
python -m unittest tests.test_config_contract tests.test_config_and_dry_run -v
rg -n "redact_tokens|ask_before_large_rewrites|include_files_changed|preserve_existing_style" cobsidian.config.example.yml
```

Expected: tests pass and `rg` returns no matches.

Commit: `fix: align config example with enforced settings`

### Task 5: Bound Large-Vault MCP and Duplicate Work

**Files:**
- Create: `skills/cobsidian/scripts/duplicates.py`
- Modify: `skills/cobsidian/scripts/find_duplicates.py`
- Modify: `skills/cobsidian/mcp_server.py`
- Create: `tests/test_duplicates.py`
- Modify: `tests/test_mcp_server.py`

- [ ] **Step 1: Write failing pagination and truncation tests**

```python
from pathlib import Path
import tempfile

from skills.cobsidian.mcp_server import tool_cobsidian_scan_vault
from skills.cobsidian.scripts.duplicates import find_title_duplicates
from skills.cobsidian.scripts.scan_vault import NoteInfo


def test_scan_tool_paginates_notes(self) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        vault = Path(temp_dir)
        for index in range(4):
            (vault / f"Note {index}.md").write_text(f"# Note {index}\n", encoding="utf-8")
        payload = tool_cobsidian_scan_vault(vault=str(vault), offset=1, limit=2)
        self.assertEqual(4, payload["total_note_count"])
        self.assertEqual({"offset": 1, "limit": 2, "returned": 2}, payload["page"])
        self.assertEqual(2, len(payload["notes"]))


def test_duplicate_search_reports_truncation(self) -> None:
    notes = [
        NoteInfo("one.md", "Agent Workflow", [], [], 1),
        NoteInfo("two.md", "Agent Workflows", [], [], 1),
        NoteInfo("three.md", "Agent Work", [], [], 1),
    ]
    report = find_title_duplicates(notes, threshold=0.5, max_comparisons=1)
    self.assertEqual(1, report.comparisons)
    self.assertTrue(report.truncated)
```

Also test negative offset, zero limit, limit greater than `500`, and negative comparison cap.

- [ ] **Step 2: Run focused tests and verify RED**

Run: `python -m unittest tests.test_duplicates tests.test_mcp_server -v`

Expected: FAIL because pagination arguments and duplicate reports do not exist.

- [ ] **Step 3: Implement bounded duplicate discovery**

`duplicates.py` must define:

```python
from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from difflib import SequenceMatcher

from scan_vault import NoteInfo


@dataclass(frozen=True)
class SimilarTitle:
    score: float
    left: NoteInfo
    right: NoteInfo


@dataclass(frozen=True)
class DuplicateReport:
    exact_duplicates: list[list[NoteInfo]]
    similar_titles: list[SimilarTitle]
    comparisons: int
    truncated: bool


def normalize_title(title: str) -> str:
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", title.casefold())


def find_title_duplicates(
    notes: list[NoteInfo],
    threshold: float,
    max_comparisons: int,
) -> DuplicateReport:
    if max_comparisons < 0:
        raise ValueError("max_comparisons must be non-negative.")

    exact_by_title: dict[str, list[NoteInfo]] = defaultdict(list)
    normalized_notes: list[tuple[NoteInfo, str]] = []
    for note in notes:
        normalized = normalize_title(note.title)
        if normalized:
            exact_by_title[normalized].append(note)
            normalized_notes.append((note, normalized))

    exact_duplicates = [
        sorted(group, key=lambda note: note.path.casefold())
        for group in exact_by_title.values()
        if len(group) > 1
    ]
    exact_duplicates.sort(key=lambda group: group[0].path.casefold())

    similar_titles: list[SimilarTitle] = []
    comparisons = 0
    truncated = False
    stop = False
    for index, (left, left_title) in enumerate(normalized_notes):
        for right, right_title in normalized_notes[index + 1 :]:
            if left_title == right_title:
                continue
            if comparisons >= max_comparisons:
                truncated = True
                stop = True
                break
            comparisons += 1
            score = SequenceMatcher(None, left_title, right_title).ratio()
            if score >= threshold:
                similar_titles.append(SimilarTitle(round(score, 4), left, right))
        if stop:
            break

    similar_titles.sort(key=lambda item: (-item.score, item.left.path.casefold(), item.right.path.casefold()))
    return DuplicateReport(exact_duplicates, similar_titles, comparisons, truncated)
```

Exact-title grouping must inspect every note. Similar-title results must use normalized titles, deterministic ordering, and an observable cap.

- [ ] **Step 4: Add bounded MCP scan pages**

```python
DEFAULT_SCAN_LIMIT = 100
MAX_SCAN_LIMIT = 500


def paginate_notes(notes: list[NoteInfo], offset: int, limit: int) -> list[NoteInfo]:
    if offset < 0:
        raise ValueError("offset must be non-negative.")
    if limit < 1 or limit > MAX_SCAN_LIMIT:
        raise ValueError(f"limit must be between 1 and {MAX_SCAN_LIMIT}.")
    return notes[offset : offset + limit]
```

Return `total_note_count`, `notes`, and page metadata. Add `max_comparisons` to the duplicate MCP tool and CLI.

- [ ] **Step 5: Verify GREEN and commit**

Run:

```powershell
python -m unittest tests.test_duplicates tests.test_mcp_server -v
python skills/cobsidian/scripts/find_duplicates.py examples --max-comparisons 1000
```

Expected: all focused tests pass; CLI exits `0` and reports if comparison was truncated.

Commit: `feat: bound large-vault scan and duplicate work`

### Task 6: Clean Public Adapters and Document v0.4.0

**Files:**
- Modify: `skills/cobsidian/agents/claude.md`
- Modify: `tests/test_documentation_hygiene.py`
- Modify: `README.md`
- Modify: `docs/README.zh-CN.md`
- Modify: `docs/mcp-server.md`
- Modify: `docs/mcp-server.zh-CN.md`
- Modify: `docs/integrations.md`
- Modify: `docs/integrations.zh-CN.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Write the failing adapter hygiene test**

```python
def test_public_adapter_has_no_owner_specific_workflow_rules(self) -> None:
    adapter = (REPO_ROOT / "skills" / "cobsidian" / "agents" / "claude.md").read_text(encoding="utf-8")
    self.assertNotIn("做后端就用superpowers", adapter)
    self.assertNotIn("做知识整理就用cobsidian skill", adapter)
```

- [ ] **Step 2: Run the test and verify RED**

Run: `python -m unittest tests.test_documentation_hygiene -v`

Expected: FAIL on the two personal workflow lines.

- [ ] **Step 3: Remove personal rules and update documentation**

Replace the CLAUDE.md example with only:

```markdown
Read `skills/cobsidian/SKILL.md` when the user asks to organize material into an Obsidian vault or Markdown knowledge base.
```

Document:

- shared body-aware retrieval and CJK n-grams;
- supported config keys;
- MCP scan pagination defaults and maximums;
- duplicate comparison caps and truncation metadata;
- the unchanged read-only MCP boundary.

Move current `Unreleased` content into `v0.4.0` and add all five reliability fixes.

- [ ] **Step 4: Verify GREEN and commit**

Run:

```powershell
python -m unittest tests.test_documentation_hygiene tests.test_readme_landing_contract -v
rg -n "做后端就用|redact_tokens|unbounded" skills README.md docs cobsidian.config.example.yml
```

Expected: tests pass; no personal rule or removed config field remains.

Commit: `docs: prepare Cobsidian v0.4.0`

### Task 7: Verify, Forward-Test, Merge, Release, and Install

**Files:**
- Verify all modified files.
- Update local installation: `$CODEX_HOME/skills/cobsidian` or `~/.codex/skills/cobsidian`.

- [ ] **Step 1: Run the full local verification gate**

```powershell
python -m pip install -r requirements-mcp.txt -r requirements-dev.txt
python -m unittest discover -s tests -v
python -m compileall -q skills tests
python skills/cobsidian/scripts/validate_skill.py skills/cobsidian
python skills/cobsidian/scripts/scan_vault.py examples --json
python skills/cobsidian/scripts/find_duplicates.py examples
python skills/cobsidian/scripts/validate_notes.py examples
git diff --check main...HEAD
git status --short --branch
```

Expected: all tests pass, compileall exits `0`, skill validation prints `Skill is valid!`, example commands exit `0`, and only intended branch commits exist.

- [ ] **Step 2: Forward-test the revised skill**

Use a fresh agent with `skills/cobsidian/SKILL.md` and `examples/demo-vault`. Request Chinese learning-mode dry-run only. Verify:

- mode is `learning`;
- no files change;
- `writes` is empty;
- `Vector Search.md` is suggested from body content;
- completion report is Chinese.

- [ ] **Step 3: Request code review and fix only verified findings**

Run a focused review of the branch diff for correctness, regressions, missing tests, and public documentation consistency. Re-run the full gate after any fix.

- [ ] **Step 4: Push and open the PR**

```powershell
git push -u origin fix/v0.4.0-reliability
$body = @(
  "## Summary",
  "- validate Agent Skill metadata in CI",
  "- unify body-aware English and Chinese backlink retrieval",
  "- publish only enforced config and bound large-vault work",
  "- clean public adapters and prepare v0.4.0",
  "",
  "## Verification",
  "- python -m unittest discover -s tests -v",
  "- python -m compileall -q skills tests",
  "- python skills/cobsidian/scripts/validate_skill.py skills/cobsidian"
) -join "`n"
gh pr create --base main --head fix/v0.4.0-reliability --title "release: Cobsidian v0.4.0 reliability" --body $body
$prNumber = gh pr view fix/v0.4.0-reliability --json number --jq .number
gh pr checks $prNumber --watch --interval 10
```

The PR body must list the five fixes and local verification evidence.

- [ ] **Step 5: Merge after required checks pass**

```powershell
$prNumber = gh pr view fix/v0.4.0-reliability --json number --jq .number
gh pr merge $prNumber --squash --delete-branch
git fetch origin main
```

Expected: `main` contains the squash commit and remains clean.

- [ ] **Step 6: Tag and publish `v0.4.0`**

```powershell
git tag -a v0.4.0 origin/main -m "Cobsidian v0.4.0"
git push origin v0.4.0
gh release create v0.4.0 --repo Totoro-qaq/Cobsidian --title "Cobsidian v0.4.0" --generate-notes
```

Verify with `gh release view v0.4.0 --repo Totoro-qaq/Cobsidian`.

- [ ] **Step 7: Replace the local `v0.3.0` installation with the released skill**

Move the current install to a temporary backup, install from tag with the official installer, validate, then delete the backup only after success:

```powershell
$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
$skillHome = Join-Path $codexHome "skills"
$installed = (Join-Path $skillHome "cobsidian")
$backup = Join-Path $env:TEMP "cobsidian-v0.3.0-backup-$(Get-Date -Format yyyyMMddHHmmss)"
$expectedInstalled = [IO.Path]::GetFullPath((Join-Path $skillHome "cobsidian"))
if ((Resolve-Path $installed).Path -ne $expectedInstalled) {
  throw "Unexpected installed skill path: $installed"
}
Move-Item -LiteralPath $installed -Destination $backup
$installer = Join-Path $skillHome ".system\skill-installer\scripts\install-skill-from-github.py"
$validator = Join-Path $skillHome ".system\skill-creator\scripts\quick_validate.py"
python $installer --repo Totoro-qaq/Cobsidian --path skills/cobsidian --ref v0.4.0
$env:PYTHONUTF8 = "1"
python $validator (Join-Path $skillHome "cobsidian")
$resolvedBackup = (Resolve-Path $backup).Path
$resolvedTemp = (Resolve-Path $env:TEMP).Path
if (-not $resolvedBackup.StartsWith($resolvedTemp, [StringComparison]::OrdinalIgnoreCase)) {
  throw "Refusing to remove backup outside TEMP: $resolvedBackup"
}
Remove-Item -LiteralPath $resolvedBackup -Recurse -Force
```

Expected: installation succeeds and official validation prints `Skill is valid!`. The updated skill becomes available to Codex on the next turn.
