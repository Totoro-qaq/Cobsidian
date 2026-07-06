from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


ConfigData = dict[str, Any]


@dataclass(frozen=True)
class CobsidianConfig:
    config_path: Path | None
    raw: ConfigData

    @property
    def vault_path(self) -> Path | None:
        raw_path = self.get("vault", "path")
        if raw_path is None:
            return None
        path = Path(str(raw_path)).expanduser()
        if path.is_absolute() or self.config_path is None:
            return path.resolve()
        return (self.config_path.parent / path).resolve()

    @property
    def mode(self) -> str | None:
        mode = self.get("defaults", "mode")
        return str(mode) if mode else None

    @property
    def similar_title_threshold(self) -> float:
        return float(self.get("duplicates", "similar_title_threshold", default=0.86))

    @property
    def max_suggested_backlinks(self) -> int:
        return int(self.get("linking", "max_suggested_backlinks", default=8))

    @property
    def validation_strict(self) -> bool:
        return bool(self.get("validation", "strict", default=False))

    @property
    def validation_run_after_write(self) -> bool:
        return bool(self.get("validation", "run_after_write", default=True))

    @property
    def prefer_append_over_duplicate(self) -> bool:
        return bool(self.get("duplicates", "prefer_append_over_duplicate", default=True))

    def get(self, section: str, key: str, default: Any = None) -> Any:
        section_value = self.raw.get(section, {})
        if not isinstance(section_value, dict):
            return default
        return section_value.get(key, default)

    def note_directory_for_mode(self, mode: str | None) -> str | None:
        directories = self.get("notes", "directories", default={})
        if not isinstance(directories, dict) or mode is None:
            return None
        directory = directories.get(mode)
        return str(directory) if directory else None

    def public_summary(self) -> ConfigData:
        return {
            "path": str(self.config_path) if self.config_path else None,
            "defaults": dict(self.raw.get("defaults", {})) if isinstance(self.raw.get("defaults"), dict) else {},
            "duplicates": dict(self.raw.get("duplicates", {})) if isinstance(self.raw.get("duplicates"), dict) else {},
            "linking": dict(self.raw.get("linking", {})) if isinstance(self.raw.get("linking"), dict) else {},
            "validation": dict(self.raw.get("validation", {})) if isinstance(self.raw.get("validation"), dict) else {},
        }


def load_config(config_path: Path | None) -> CobsidianConfig:
    if config_path is None:
        return CobsidianConfig(config_path=None, raw={})

    resolved_path = config_path.expanduser().resolve()
    if not resolved_path.exists() or not resolved_path.is_file():
        raise SystemExit(f"Config file does not exist: {resolved_path}")
    return CobsidianConfig(config_path=resolved_path, raw=parse_simple_yaml(resolved_path.read_text(encoding="utf-8")))


def resolve_vault_path(positional_vault: Path | None, config: CobsidianConfig) -> Path:
    if positional_vault is not None:
        return positional_vault.expanduser().resolve()
    if config.vault_path is not None:
        return config.vault_path
    raise SystemExit("Provide a vault path or --config with vault.path.")


def parse_simple_yaml(text: str) -> ConfigData:
    root: ConfigData = {}
    stack: list[tuple[int, ConfigData]] = [(-1, root)]

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        if ":" not in stripped:
            raise SystemExit(f"Invalid config line {line_number}: {raw_line}")

        key, raw_value = stripped.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        if not key:
            raise SystemExit(f"Invalid empty config key at line {line_number}.")

        while indent <= stack[-1][0]:
            stack.pop()

        current = stack[-1][1]
        if not raw_value:
            nested: ConfigData = {}
            current[key] = nested
            stack.append((indent, nested))
        else:
            current[key] = parse_scalar(raw_value)

    return root


def parse_scalar(raw_value: str) -> Any:
    value = raw_value.strip()
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]

    lowered = value.casefold()
    if lowered in {"null", "none", "~"}:
        return None
    if lowered == "true":
        return True
    if lowered == "false":
        return False

    try:
        if any(character in value for character in (".", "e", "E")):
            return float(value)
        return int(value)
    except ValueError:
        return value
