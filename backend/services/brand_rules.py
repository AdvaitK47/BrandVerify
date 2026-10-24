"""
Per-brand rule loader.

Rules live in backend/rules/<brand_id>.json. A brand with no file gets
rules/default.json. The brand_id from a request is only ever used as a
lookup key into the files that exist, never to build a file path.

Files are read on every scan (they are tiny), so editing a rule file takes
effect immediately without restarting the server.
"""

import json
import re
from pathlib import Path
from typing import Dict, Optional

from backend.services.rule_models import ClaimRule, DisclaimerRule, RuleSet

RULES_DIR = Path(__file__).resolve().parent.parent / "rules"
DEFAULT_RULES = "default"
VALID_SEVERITIES = {"info", "warning", "critical"}


class RuleFileError(ValueError):
    """A rule file is missing, unreadable or invalid."""


def _available_files() -> Dict[str, Path]:
    return {path.stem.lower(): path for path in RULES_DIR.glob("*.json")}


def load_rules(brand_id: Optional[str] = None) -> RuleSet:
    """Rules for this brand, or the default rules if it has no file."""
    files = _available_files()
    key = (brand_id or "").strip().lower()

    if key and key != DEFAULT_RULES and key in files:
        return _parse(files[key], key)

    if DEFAULT_RULES not in files:
        raise RuleFileError(f"Missing {RULES_DIR / 'default.json'}")
    return _parse(files[DEFAULT_RULES], DEFAULT_RULES)


def load_all_rule_files() -> Dict[str, RuleSet]:
    """Parse every rule file. Used by tests to catch typos before they ship."""
    return {name: _parse(path, name) for name, path in _available_files().items()}


def _require(item: dict, keys, where: str) -> None:
    for key in keys:
        if not isinstance(item.get(key), str) or not item[key].strip():
            raise RuleFileError(f"{where}: missing or empty '{key}'")


def _check_regex(pattern: str, where: str) -> None:
    try:
        re.compile(pattern, re.IGNORECASE)
    except re.error as exc:
        raise RuleFileError(f"{where}: bad pattern {pattern!r} ({exc})") from exc


def _parse(path: Path, brand_id: str) -> RuleSet:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuleFileError(f"{path.name}: cannot read file ({exc})") from exc

    if not isinstance(data, dict):
        raise RuleFileError(f"{path.name}: top level must be an object")

    claims = []
    for i, item in enumerate(data.get("claims", [])):
        where = f"{path.name} claims[{i}]"
        if not isinstance(item, dict):
            raise RuleFileError(f"{where}: must be an object")
        _require(item, ("id", "pattern", "title", "fix"), where)
        severity = item.get("severity", "warning")
        if severity not in VALID_SEVERITIES:
            raise RuleFileError(
                f"{where}: severity must be one of {sorted(VALID_SEVERITIES)}"
            )
        _check_regex(item["pattern"], where)
        claims.append(
            ClaimRule(item["id"], item["pattern"], item["title"], item["fix"], severity)
        )

    disclaimers = []
    for i, item in enumerate(data.get("disclaimers", [])):
        where = f"{path.name} disclaimers[{i}]"
        if not isinstance(item, dict):
            raise RuleFileError(f"{where}: must be an object")
        _require(item, ("id", "title", "trigger", "accepted", "fix"), where)
        _check_regex(item["trigger"], where)
        _check_regex(item["accepted"], where)
        disclaimers.append(
            DisclaimerRule(
                item["id"], item["title"], item["trigger"], item["accepted"], item["fix"]
            )
        )

    return RuleSet(
        brand_id=brand_id,
        name=str(data.get("name", brand_id)),
        claims=tuple(claims),
        disclaimers=tuple(disclaimers),
    )
