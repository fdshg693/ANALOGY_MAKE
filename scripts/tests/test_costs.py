"""Tests for scripts/claude_loop_lib/costs.py (PHASE8.0 §3)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from . import _bootstrap  # noqa: F401 — must precede claude_loop_lib imports

from claude_loop_lib import costs


SAMPLE_RESULT_SUCCESS = json.dumps({
    "type": "result",
    "subtype": "success",
    "uuid": "11111111-1111-1111-1111-111111111111",
    "session_id": "22222222-2222-2222-2222-222222222222",
    "duration_ms": 5000,
    "duration_api_ms": 4800,
    "is_error": False,
    "num_turns": 3,
    "result": "ok",
    "stop_reason": "end_turn",
    "total_cost_usd": 0.04567,
    "usage": {
        "input_tokens": 1200,
        "output_tokens": 340,
        "cache_read_input_tokens": 50,
        "cache_creation_input_tokens": 0,
    },
    "modelUsage": {
        "claude-opus-4-7": {
            "inputTokens": 1200,
            "outputTokens": 340,
            "cacheReadInputTokens": 50,
            "cacheCreationInputTokens": 0,
            "webSearchRequests": 0,
            "costUSD": 0.04567,
            "contextWindow": 200000,
            "maxOutputTokens": 8192,
        },
    },
})


SAMPLE_RESULT_NO_COST = json.dumps({
    "type": "result",
    "subtype": "success",
    "session_id": "ss",
    "num_turns": 1,
    "usage": {
        "input_tokens": 1_000_000,
        "output_tokens": 1_000_000,
        "cache_read_input_tokens": 0,
        "cache_creation_input_tokens": 0,
    },
    "modelUsage": {
        "claude-sonnet-4-6": {"costUSD": 0},
    },
})


class TestParseCliResult(unittest.TestCase):
    def test_parses_valid_json_object(self) -> None:
        result = costs.parse_cli_result(SAMPLE_RESULT_SUCCESS)
        assert result is not None
        assert result["total_cost_usd"] == 0.04567
        assert result["usage"]["input_tokens"] == 1200

    def test_returns_none_for_non_json(self) -> None:
        assert costs.parse_cli_result("hello world") is None

    def test_returns_none_for_empty(self) -> None:
        assert costs.parse_cli_result("") is None
        assert costs.parse_cli_result(None) is None

    def test_returns_none_for_array(self) -> None:
        assert costs.parse_cli_result("[]") is None

    def test_handles_bytes_input(self) -> None:
        result = costs.parse_cli_result(SAMPLE_RESULT_SUCCESS.encode("utf-8"))
        assert result is not None


class TestExtractUsage(unittest.TestCase):
    def test_extracts_four_counters(self) -> None:
        result = json.loads(SAMPLE_RESULT_SUCCESS)
        usage = costs.extract_usage(result)
        assert usage == {
            "input_tokens": 1200,
            "output_tokens": 340,
            "cache_read_input_tokens": 50,
            "cache_creation_input_tokens": 0,
        }

    def test_missing_usage_returns_none_values(self) -> None:
        usage = costs.extract_usage({})
        assert usage == {
            "input_tokens": None,
            "output_tokens": None,
            "cache_read_input_tokens": None,
            "cache_creation_input_tokens": None,
        }


class TestExtractModelName(unittest.TestCase):
    def test_picks_first_model_key(self) -> None:
        result = json.loads(SAMPLE_RESULT_SUCCESS)
        assert costs.extract_model_name(result) == "claude-opus-4-7"

    def test_returns_none_when_absent(self) -> None:
        assert costs.extract_model_name({}) is None


class TestCalculateCostFromPriceBook(unittest.TestCase):
    def test_opus_4_7_million_tokens(self) -> None:
        usage = {
            "input_tokens": 1_000_000,
            "output_tokens": 1_000_000,
            "cache_read_input_tokens": 1_000_000,
            "cache_creation_input_tokens": 1_000_000,
        }
        cost = costs.calculate_cost_from_price_book(usage, model="claude-opus-4-7")
        # 5 + 25 + 0.50 + 6.25 = 36.75
        assert cost is not None
        assert abs(cost - 36.75) < 1e-9

    def test_unknown_model_returns_none(self) -> None:
        usage = {"input_tokens": 100, "output_tokens": 100,
                 "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0}
        assert costs.calculate_cost_from_price_book(usage, model="mystery") is None

    def test_no_tokens_returns_none(self) -> None:
        usage = {"input_tokens": None, "output_tokens": None,
                 "cache_read_input_tokens": None, "cache_creation_input_tokens": None}
        assert costs.calculate_cost_from_price_book(usage, model="claude-opus-4-7") is None

    def test_none_model_returns_none(self) -> None:
        usage = {"input_tokens": 100, "output_tokens": 100,
                 "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0}
        assert costs.calculate_cost_from_price_book(usage, model=None) is None


class TestBuildStepCostFromCliOutput(unittest.TestCase):
    def test_ok_from_success_json(self) -> None:
        step = costs.build_step_cost_from_cli_output(
            step_name="demo",
            session_id="sid",
            started_at="2026-04-24T10:00:00",
            ended_at="2026-04-24T10:00:05",
            duration_seconds=5.0,
            kind="claude",
            raw_output=SAMPLE_RESULT_SUCCESS,
        )
        assert step["status"] == "ok"
        assert step["model"] == "claude-opus-4-7"
        assert step["input_tokens"] == 1200
        assert step["cost_usd"] == 0.04567
        assert step["cost_source"] == "cli"
        assert step["num_turns"] == 3
        assert step["kind"] == "claude"

    def test_unavailable_when_non_json(self) -> None:
        step = costs.build_step_cost_from_cli_output(
            step_name="demo",
            session_id="sid",
            started_at="a",
            ended_at="b",
            duration_seconds=0.0,
            kind="claude",
            raw_output="not json",
            reason_when_missing="non-json-output",
        )
        assert step["status"] == "unavailable"
        assert step["reason"] == "non-json-output"
        assert step["cost_usd"] is None
        assert step["input_tokens"] is None

    def test_unavailable_when_none(self) -> None:
        step = costs.build_step_cost_from_cli_output(
            step_name="demo", session_id="sid",
            started_at="a", ended_at="b", duration_seconds=0.0,
            kind="claude", raw_output=None,
            reason_when_missing="no-log run",
        )
        assert step["status"] == "unavailable"
        assert step["reason"] == "no-log run"

    def test_fallback_price_book_when_cost_missing(self) -> None:
        step = costs.build_step_cost_from_cli_output(
            step_name="demo", session_id="sid",
            started_at="a", ended_at="b", duration_seconds=0.0,
            kind="claude", raw_output=SAMPLE_RESULT_NO_COST,
        )
        assert step["status"] == "ok"
        assert step["cost_source"] == "fallback_price_book"
        # sonnet-4-6: 3 + 15 = 18.0 per million each
        assert step["cost_usd"] is not None
        assert abs(step["cost_usd"] - 18.0) < 1e-9


class TestBuildExternalStepCost(unittest.TestCase):
    def test_external_is_zero_cost_ok(self) -> None:
        step = costs.build_external_step_cost(
            step_name="ext",
            session_id="sid",
            started_at="a",
            ended_at="b",
            duration_seconds=12.5,
        )
        assert step["status"] == "ok"
        assert step["kind"] == "deferred_external"
        assert step["cost_usd"] == 0.0
        assert step["input_tokens"] is None


class TestAggregateRun(unittest.TestCase):
    def _ok(self, name: str, cost: float) -> costs.StepCost:
        return costs.StepCost(
            step_name=name, session_id="s", model="m",
            started_at="a", ended_at="b", duration_seconds=1.0,
            kind="claude",
            input_tokens=1, output_tokens=1,
            cache_read_input_tokens=0, cache_creation_input_tokens=0,
            num_turns=1,
            cost_usd=cost, cost_source="cli",
            status="ok", reason=None,
        )

    def _unavailable(self, name: str) -> costs.StepCost:
        return costs.unavailable_step(
            step_name=name, session_id="s",
            started_at="a", ended_at="b", duration_seconds=1.0,
            kind="claude", reason="no-json",
        )

    def test_sums_ok_only_counts_missing(self) -> None:
        summary = costs.aggregate_run(
            workflow_label="demo",
            started_at="t0", ended_at="t1",
            steps=[self._ok("a", 0.10), self._ok("b", 0.20), self._unavailable("c")],
            claude_code_cli_version="2.1.117",
        )
        assert abs(summary["total_cost_usd"] - 0.30) < 1e-9
        assert summary["missing_steps"] == 1
        assert len(summary["steps"]) == 3
        assert summary["claude_code_cli_version"] == "2.1.117"
        assert summary["price_book_source"] == costs.PRICE_BOOK_SOURCE

    def test_empty_steps_zero_total(self) -> None:
        summary = costs.aggregate_run(
            workflow_label="demo", started_at="t0", ended_at="t1", steps=[],
        )
        assert summary["total_cost_usd"] == 0.0
        assert summary["missing_steps"] == 0


class TestWriteSidecar(unittest.TestCase):
    def test_roundtrip(self) -> None:
        summary = costs.aggregate_run(
            workflow_label="demo", started_at="t0", ended_at="t1",
            steps=[
                costs.build_step_cost_from_cli_output(
                    step_name="x", session_id="sid",
                    started_at="a", ended_at="b", duration_seconds=1.0,
                    kind="claude", raw_output=SAMPLE_RESULT_SUCCESS,
                ),
            ],
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "run.costs.json"
            costs.write_sidecar(path, summary)
            assert path.exists()
            loaded = json.loads(path.read_text(encoding="utf-8"))
            assert loaded["workflow_label"] == "demo"
            assert loaded["steps"][0]["model"] == "claude-opus-4-7"


if __name__ == "__main__":
    unittest.main()
