#!/usr/bin/env python3
"""Fail when tracked text resembles a supported provider credential."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
import sys


@dataclass(frozen=True)
class CredentialPattern:
    provider: str
    expression: re.Pattern[str]


PATTERNS = (
    CredentialPattern("OpenAI", re.compile(r"sk-" + r"(?:proj-)?[A-Za-z0-9_-]{20,}")),
    CredentialPattern("Anthropic", re.compile(r"sk-" + r"ant-[A-Za-z0-9_-]{20,}")),
    CredentialPattern("E2B", re.compile(r"e2b_" + r"[A-Za-z0-9_-]{16,}")),
    CredentialPattern("Browserbase", re.compile(r"bb_" + r"[A-Za-z0-9_-]{16,}")),
    CredentialPattern("Google", re.compile(r"AIza" + r"[A-Za-z0-9_-]{24,}")),
    CredentialPattern("GitHub", re.compile(r"gh[pousr]_" + r"[A-Za-z0-9]{20,}")),
    CredentialPattern("GitHub", re.compile(r"github_pat_" + r"[A-Za-z0-9_]{20,}")),
    CredentialPattern("AWS", re.compile(r"AKIA" + r"[A-Z0-9]{16}")),
    CredentialPattern("Hugging-Face", re.compile(r"hf_" + r"[A-Za-z0-9]{20,}")),
    CredentialPattern("NVIDIA-NGC", re.compile(r"nvapi-" + r"[A-Za-z0-9_-]{16,}")),
    CredentialPattern("Sentry", re.compile(r"sntrys_" + r"[A-Za-z0-9_-]{16,}")),
    CredentialPattern("private-key", re.compile(r"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY")),
)


# Internal-only metadata. These are not credentials, but publishing them discloses the
# maintainer host layout and the existence of private repositories, and a public tree is
# indexed and cached even if visibility is later reverted.
DISCLOSURE_PATTERNS = (
    CredentialPattern(
        "host-account-path",
        re.compile(r"/(?:Users|home)/[A-Za-z][A-Za-z0-9._-]*/"),
    ),
    CredentialPattern(
        "private-repository-url",
        re.compile(r"github\.com[/:]ed3c/(?!runtime-env\b)[A-Za-z0-9._-]+"),
    ),
)


def _scan(patterns: tuple[CredentialPattern, ...], text: str) -> list[tuple[str, int]]:
    findings: list[tuple[str, int]] = []
    for pattern in patterns:
        for match in pattern.expression.finditer(text):
            line_number = text.count("\n", 0, match.start()) + 1
            findings.append((pattern.provider, line_number))
    return findings


def matches(text: str) -> list[tuple[str, int]]:
    return _scan(PATTERNS, text)


def disclosure_matches(text: str) -> list[tuple[str, int]]:
    return _scan(DISCLOSURE_PATTERNS, text)


def tracked_paths(repo: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "-C", str(repo), "ls-files", "-z"],
        check=True,
        stdout=subprocess.PIPE,
    )
    return [repo / item.decode("utf-8") for item in result.stdout.split(b"\0") if item]


def scan_repo(repo: Path) -> int:
    findings: list[tuple[Path, str, int]] = []
    disclosures: list[tuple[Path, str, int]] = []
    for path in tracked_paths(repo):
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        relative = path.relative_to(repo)
        findings.extend((relative, provider, line) for provider, line in matches(text))
        disclosures.extend(
            (relative, label, line) for label, line in disclosure_matches(text)
        )
    for path, provider, line in findings:
        print(f"ERROR: possible {provider} credential at {path}:{line}", file=sys.stderr)
    for path, label, line in disclosures:
        print(f"ERROR: internal-only {label} at {path}:{line}", file=sys.stderr)
    if findings or disclosures:
        return 1
    print("PASS: no supported credential signatures in tracked text")
    return 0


def selftest() -> int:
    planted = (
        "sk-" + "proj-" + "A" * 24,
        "sk-" + "ant-" + "B" * 24,
        "e2b_" + "C" * 20,
        "bb_" + "C" * 20,
        "AIza" + "D" * 28,
        "ghp_" + "E" * 24,
        "github_pat_" + "F" * 24,
        "AKIA" + "G" * 16,
        "hf_" + "H" * 24,
        "nvapi-" + "I" * 20,
        "sntrys_" + "J" * 20,
        "-----BEGIN " + "PRIVATE KEY-----",
    )
    missed = [sample for sample in planted if not matches(sample)]
    if missed or matches("E2B_API_KEY=\nOPENAI_API_KEY=\nfixture-only-value"):
        print("ERROR: tracked-text scanner selftest failed", file=sys.stderr)
        return 1

    planted_disclosure = (
        "run it from /Users/" + "someone/runtime-env today",
        "the checkout at /home/" + "builder/runtime-env",
        "see https://github.com/" + "ed3c/some-private-repo/issues/1",
    )
    permitted_disclosure = (
        "run it from ~/runtime-env today",
        "clone https://github.com/" + "ed3c/runtime-env",
        "profile skill-bettor-local and module bettor-arena-proof",
        "the GitHub profile https://github.com/" + "users/ed3c",
    )
    missed_disclosure = [
        sample for sample in planted_disclosure if not disclosure_matches(sample)
    ]
    flagged_permitted = [
        sample for sample in permitted_disclosure if disclosure_matches(sample)
    ]
    if missed_disclosure or flagged_permitted:
        print("ERROR: disclosure scanner selftest failed", file=sys.stderr)
        for sample in missed_disclosure:
            print(f"  missed: {sample}", file=sys.stderr)
        for sample in flagged_permitted:
            print(f"  wrongly flagged: {sample}", file=sys.stderr)
        return 1

    print("PASS: tracked-text scanner detects planted signatures and ignores names")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--selftest", action="store_true")
    selection.add_argument("--repo", type=Path)
    args = parser.parse_args()
    return selftest() if args.selftest else scan_repo(args.repo.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
