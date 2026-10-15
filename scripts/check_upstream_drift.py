"""Read-only drift check for the pinned Hugging Face model sources."""
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib.error import URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "catalog" / "source.json"
REVISION_RE = re.compile(r"^[0-9a-f]{40}$")
REPOSITORY_RE = re.compile(r"^[^/\\\s]+/[^/\\\s]+$")


@dataclass(frozen=True)
class SourcePin:
    repository: str
    revision: str


@dataclass(frozen=True)
class DriftResult:
    source: SourcePin
    current: str | None
    status: str
    error: str | None = None


def load_sources(path: Path = SOURCE) -> list[SourcePin]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("sources"), list):
        raise ValueError("source snapshot must contain a sources list")

    sources = []
    for index, entry in enumerate(payload["sources"]):
        if not isinstance(entry, dict):
            raise ValueError(f"source {index} must be an object")
        repository = entry.get("repository")
        revision = entry.get("revision")
        if not isinstance(repository, str) or not REPOSITORY_RE.fullmatch(repository):
            raise ValueError(f"source {index} has an invalid repository")
        if not isinstance(revision, str) or not REVISION_RE.fullmatch(revision):
            raise ValueError(f"source {index} has an invalid pinned revision")
        sources.append(SourcePin(repository, revision))

    if not sources:
        raise ValueError("source snapshot has no sources")
    return sorted(sources, key=lambda source: (source.repository, source.revision))


def parse_api_response(payload: object) -> str:
    if not isinstance(payload, dict):
        raise ValueError("Hugging Face API response must be an object")
    revision = payload.get("sha")
    if not isinstance(revision, str) or not REVISION_RE.fullmatch(revision):
        raise ValueError("Hugging Face API response has no valid 40-character sha")
    return revision


def fetch_head_sha(repository: str) -> str:
    url = f"https://huggingface.co/api/models/{quote(repository, safe='/')}"
    request = Request(url, headers={"Accept": "application/json"})
    try:
        with urlopen(request, timeout=30) as response:
            payload = json.load(response)
    except (OSError, TimeoutError, URLError, json.JSONDecodeError) as exc:
        raise ValueError(f"Hugging Face API request failed: {exc}") from exc
    return parse_api_response(payload)


def check_sources(
    sources: list[SourcePin], fetch_head: Callable[[str], str] = fetch_head_sha
) -> list[DriftResult]:
    results = []
    for source in sorted(sources, key=lambda item: (item.repository, item.revision)):
        try:
            current = fetch_head(source.repository)
        except (OSError, TimeoutError, URLError, ValueError) as exc:
            results.append(DriftResult(source, None, "error", str(exc)))
            continue
        status = "unchanged" if current == source.revision else "drifted"
        results.append(DriftResult(source, current, status))
    return results


def format_report(results: list[DriftResult]) -> str:
    lines = []
    for result in results:
        lines.extend(
            (
                result.source.repository,
                f"  pinned:  {result.source.revision}",
                f"  current: {result.current or 'unavailable'}",
                f"  status:  {result.status}",
            )
        )
    return "\n".join(lines)


def main() -> int:
    try:
        sources = load_sources()
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    results = check_sources(sources)
    print(format_report(results))
    for result in results:
        if result.error:
            print(f"{result.source.repository}: {result.error}", file=sys.stderr)
    return int(any(result.status != "unchanged" for result in results))


if __name__ == "__main__":
    raise SystemExit(main())
