from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from urllib.error import URLError

from scripts import check_upstream_drift as drift

PINNED = "a" * 40
CURRENT = "b" * 40


class CheckUpstreamDriftTests(unittest.TestCase):
    def test_unchanged_revision_succeeds(self) -> None:
        source = drift.SourcePin("wavekat/voice", PINNED)
        results = drift.check_sources([source], lambda _repository: PINNED)

        self.assertEqual([result.status for result in results], ["unchanged"])
        self.assertEqual(
            drift.format_report(results),
            "wavekat/voice\n"
            f"  pinned:  {PINNED}\n"
            f"  current: {PINNED}\n"
            "  status:  unchanged",
        )

    def test_changed_revision_is_reported_as_drift(self) -> None:
        source = drift.SourcePin("wavekat/voice", PINNED)
        results = drift.check_sources([source], lambda _repository: CURRENT)

        self.assertEqual([result.status for result in results], ["drifted"])
        self.assertEqual(results[0].current, CURRENT)

    def test_malformed_api_response_returns_nonzero(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            source_path = self.write_source(Path(temporary_directory))
            response = io.BytesIO(b'{"sha":"not-a-revision"}')
            stdout = io.StringIO()
            stderr = io.StringIO()
            with (
                patch.object(drift, "SOURCE", source_path),
                patch.object(drift, "urlopen", return_value=response),
                redirect_stdout(stdout),
                redirect_stderr(stderr),
            ):
                result = drift.main()

        self.assertEqual(result, 1)
        self.assertIn("status:  error", stdout.getvalue())
        self.assertIn("no valid 40-character sha", stderr.getvalue())

    def test_network_failure_returns_nonzero(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            source_path = self.write_source(Path(temporary_directory))
            stdout = io.StringIO()
            stderr = io.StringIO()
            with (
                patch.object(drift, "SOURCE", source_path),
                patch.object(drift, "urlopen", side_effect=URLError("offline")),
                redirect_stdout(stdout),
                redirect_stderr(stderr),
            ):
                result = drift.main()

        self.assertEqual(result, 1)
        self.assertIn("status:  error", stdout.getvalue())
        self.assertIn("offline", stderr.getvalue())

    def test_multiple_repositories_are_reported_in_order(self) -> None:
        sources = [
            drift.SourcePin("wavekat/z-model", CURRENT),
            drift.SourcePin("wavekat/a-model", PINNED),
        ]
        revisions = {"wavekat/a-model": PINNED, "wavekat/z-model": CURRENT}
        results = drift.check_sources(sources, revisions.__getitem__)

        self.assertEqual(
            [result.source.repository for result in results],
            ["wavekat/a-model", "wavekat/z-model"],
        )
        self.assertEqual([result.status for result in results], ["unchanged", "unchanged"])

    def test_report_order_is_deterministic_for_reordered_inputs(self) -> None:
        first = [
            drift.SourcePin("wavekat/z-model", CURRENT),
            drift.SourcePin("wavekat/a-model", PINNED),
        ]
        second = list(reversed(first))
        revisions = {"wavekat/a-model": PINNED, "wavekat/z-model": CURRENT}

        first_report = drift.format_report(drift.check_sources(first, revisions.__getitem__))
        second_report = drift.format_report(drift.check_sources(second, revisions.__getitem__))

        self.assertEqual(first_report, second_report)

    @staticmethod
    def write_source(directory: Path) -> Path:
        path = directory / "source.json"
        path.write_text(
            json.dumps(
                {
                    "kind": "qwen3-onnx-source-snapshot",
                    "schema": 1,
                    "sources": [
                        {"repository": "wavekat/voice", "revision": PINNED},
                    ],
                }
            ),
            encoding="utf-8",
        )
        return path


if __name__ == "__main__":
    unittest.main()
