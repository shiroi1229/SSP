#!/usr/bin/env python3
"""Fail when tracked files contain common credential patterns or tracked local env files."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX_SCAN_BYTES = 2_000_000

TOKEN_PATTERNS = {
    "OpenAI API key": re.compile(r"\bsk-proj-[A-Za-z0-9_-]{20,}\b"),
    "Anthropic API key": re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b"),
    "GitHub classic token": re.compile(r"\bghp_[A-Za-z0-9]{30,}\b"),
    "GitHub fine-grained token": re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "Google API key": re.compile(r"\bAIza[0-9A-Za-z_-]{30,}\b"),
    "Slack token": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
    "Hugging Face token": re.compile(r"\bhf_[A-Za-z0-9]{20,}\b"),
    "Private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}

SENSITIVE_ASSIGNMENT = re.compile(
    r"^\s*['\"]?"
    r"([A-Za-z0-9_]*(?:password|secret|token|api_key|private_key|access_key|credential)[A-Za-z0-9_]*)"
    r"['\"]?\s*[:=]\s*(.+?)\s*$",
    re.IGNORECASE,
)

REFERENCE_MARKERS = (
    "${",
    "os.environ",
    "os.getenv",
    "getenv(",
    "process.env",
    "config.get(",
    "secrets.",
    "env.",
)

PLACEHOLDER_MARKERS = (
    "<redacted>",
    "<insert_",
    "change_me",
    "replace_me",
    "your-password",
    "your_password",
    "example",
    "placeholder",
    "dummy",
    "null",
    "none",
)

ALLOWED_ENV_FILES = {".env.example", ".env.sample", ".env.template"}


def tracked_files() -> list[Path]:
    raw = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT)
    return [ROOT / item.decode("utf-8") for item in raw.split(b"\0") if item]


def is_forbidden_env_file(path: Path) -> bool:
    name = path.name
    return name.startswith(".env") and name not in ALLOWED_ENV_FILES


def read_text_if_scannable(path: Path) -> str | None:
    try:
        if not path.is_file() or path.stat().st_size > MAX_SCAN_BYTES:
            return None
        data = path.read_bytes()
    except OSError:
        return None

    if b"\x00" in data[:4096]:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def find_generic_secret(text: str) -> str | None:
    for line in text.splitlines():
        match = SENSITIVE_ASSIGNMENT.match(line)
        if not match:
            continue

        key = match.group(1)
        rhs = match.group(2).strip().rstrip(",")
        rhs_lower = rhs.lower()
        if any(marker in rhs_lower for marker in REFERENCE_MARKERS):
            continue
        if any(marker in rhs_lower for marker in PLACEHOLDER_MARKERS):
            continue

        value = rhs.strip("'\"")
        if len(value) >= 8 and not value.startswith(("$", "{", "[")):
            return key
    return None


def main() -> int:
    findings: list[str] = []

    for path in tracked_files():
        rel = path.relative_to(ROOT)
        if is_forbidden_env_file(path):
            findings.append(f"{rel}: local environment file is tracked")
            continue

        text = read_text_if_scannable(path)
        if text is None:
            continue

        for label, pattern in TOKEN_PATTERNS.items():
            if pattern.search(text):
                findings.append(f"{rel}: possible {label}")

        if path.name not in ALLOWED_ENV_FILES:
            key = find_generic_secret(text)
            if key:
                findings.append(f"{rel}: possible hardcoded secret in {key}")

    if findings:
        print("Secret scan FAILED:\n", file=sys.stderr)
        for finding in sorted(set(findings)):
            print(f" - {finding}", file=sys.stderr)
        return 1

    print("Secret scan passed: no tracked credential patterns detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
