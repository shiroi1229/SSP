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


def parse_version_sort_key(version_str: str | None) -> Tuple[int, int, int, int, int]:
    """
    バージョンの並び順を決めるためのソートキー。
    - プレフィックス順（UI- < R- < A- < その他）
    - メジャー / マイナー / パッチ番号
    - PoC かどうか（PoC は常に後ろ）を反映する。
    """
    if not version_str:
        return (99, 0, 0, 0, 0)

    # 例: R-v0.3, R-v0.1.1, R-v0.1.1_PoC など
    match = re.match(r"([A-Z]+-)?v(\d+)\.(\d+)(?:\.(\d+))?", version_str)
    prefix_num = 99
    major_int = 0
    minor_int = 0
    patch_int = 0

    if match:
        prefix, major, minor, patch = match.groups()
        prefix = prefix or ""
        prefix_num = PREFIX_ORDER.get(prefix, 99)
        major_int = int(major)
        minor_int = int(minor)
        patch_int = int(patch) if patch is not None else 0

    is_poc = 1 if "PoC" in (version_str or "") else 0
    return (prefix_num, major_int, minor_int, patch_int, is_poc)
