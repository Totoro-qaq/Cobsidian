from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml


SKILL_NAME_RE = re.compile(r"^[a-z0-9-]+$")


@dataclass(frozen=True)
class SkillValidationResult:
    name: str
    description: str
    errors: list[str]


def validate_skill(skill_dir: Path) -> SkillValidationResult:
    skill_path = skill_dir / "SKILL.md"
    if not skill_path.is_file():
        return SkillValidationResult("", "", [f"Missing skill file: {skill_path}"])

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
    if name and not SKILL_NAME_RE.fullmatch(name):
        errors.append("Skill name must contain only lowercase letters, digits, and hyphens.")
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
