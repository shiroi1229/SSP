import re
from typing import Tuple

PREFIX_ORDER = {
    "": 0,
    "UI-": 1,
    "R-": 2,
    "A-": 3,
}


def categorize_version(version: str | None) -> str:
    if not version:
        return "backend"
    if version.startswith("UI-v"):
        return "frontend"
    if version.startswith("R-v"):
        return "robustness"
    if version.startswith("A-v"):
        return "Awareness_Engine"
    return "backend"


def parse_version_sort_key(version_str: str | None) -> Tuple[int, int, int | str]:
    if not version_str:
        return (99, 0, 0)
    match = re.match(r"([A-Z]+-)?v(\d+)\.(\d+)", version_str)
    if not match:
        return (99, version_str, 0)
    prefix, major, minor = match.groups()
    prefix = prefix or ""
    prefix_num = PREFIX_ORDER.get(prefix, 99)
    return (prefix_num, int(major), int(minor))
