"""Tests for scripts/claude_loop_lib/validation.py."""
from __future__ import annotations

import argparse
import io
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from . import _bootstrap  # noqa: F401  — must precede claude_loop_lib imports

from claude_loop import DEFAULT_WORKING_DIRECTORY, YAML_DIR
from claude_loop_lib.validation import (
    KNOWN_EFFORTS,
    KNOWN_MODELS,
    Violation,
    _check_value_whitelist,
    _validate_category,
    _validate_defaults_section,
    _validate_single_yaml,
    _validate_steps_section,
    validate_startup,
)


def _make_args(workflow: str = "full") -> argparse.Namespace:
    return argparse.Namespace(
        workflow=workflow,
        start=1,
        cwd=Path("."),
        dry_run=True,
        log_dir=Path("logs/workflow"),
        no_log=True,
        no_notify=True,
        auto_commit_before=False,
        max_loops=1,
        max_step_runs=None,
    )


class _TempCwdBase(unittest.TestCase):
    """Base class that sets up a minimal valid repo layout in a tempdir."""

    def setUp(self) -> None:
        self.tmp_dir = Path(tempfile.mkdtemp())
        (self.tmp_dir / ".claude").mkdir()
        (self.tmp_dir / ".claude" / "CURRENT_CATEGORY").write_text("util", encoding="utf-8")
        (self.tmp_dir / "docs" / "util").mkdir(parents=True)
        (self.tmp_dir / ".claude" / "skills" / "foo").mkdir(parents=True)
        (self.tmp_dir / ".claude" / "skills" / "foo" / "SKILL.md").write_text(
            "# foo", encoding="utf-8"
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_dir, ignore_errors=True)


class TestValidateCategory(_TempCwdBase):
    def test_missing_category_file_is_warning(self) -> None:
        (self.tmp_dir / ".claude" / "CURRENT_CATEGORY").unlink()
        violations = _validate_category(self.tmp_dir)
        assert len(violations) == 1
        assert violations[0].severity == "warning"

    def test_empty_category_is_error(self) -> None:
        (self.tmp_dir / ".claude" / "CURRENT_CATEGORY").write_text("", encoding="utf-8")
        violations = _validate_category(self.tmp_dir)
        assert len(violations) == 1
        assert violations[0].severity == "error"

    def test_invalid_category_name_is_error(self) -> None:
        (self.tmp_dir / ".claude" / "CURRENT_CATEGORY").write_text(
            "bad/name", encoding="utf-8"
        )
        violations = _validate_category(self.tmp_dir)
        assert len(violations) == 1
        assert violations[0].severity == "error"

    def test_missing_docs_dir_is_error(self) -> None:
        (self.tmp_dir / ".claude" / "CURRENT_CATEGORY").write_text(
            "nonexistent", encoding="utf-8"
        )
        violations = _validate_category(self.tmp_dir)
        assert len(violations) == 1
        assert violations[0].severity == "error"
        assert "docs/nonexistent" in violations[0].message

    def test_valid_category(self) -> None:
        assert _validate_category(self.tmp_dir) == []


class TestValidateSingleYamlShape(_TempCwdBase):
    def _write(self, content: str) -> Path:
        path = self.tmp_dir / "wf.yaml"
        path.write_text(content, encoding="utf-8")
        return path

    def test_file_not_found(self) -> None:
        violations = _validate_single_yaml(self.tmp_dir / "missing.yaml", self.tmp_dir)
        assert any(v.severity == "error" and "File not found" in v.message for v in violations)

    @patch("claude_loop_lib.validation.shutil.which", return_value="/bin/claude")
    def test_yaml_parse_error(self, _which) -> None:
        path = self._write("foo: [unclosed\n")
        violations = _validate_single_yaml(path, self.tmp_dir)
        assert any("YAML parse error" in v.message for v in violations)

    @patch("claude_loop_lib.validation.shutil.which", return_value="/bin/claude")
    def test_top_level_not_mapping(self, _which) -> None:
        path = self._write("- a\n- b\n")
        violations = _validate_single_yaml(path, self.tmp_dir)
        assert any("mapping" in v.message for v in violations)

    @patch("claude_loop_lib.validation.shutil.which", return_value="/bin/claude")
    def test_defaults_not_mapping(self, _which) -> None:
        path = self._write(
            "defaults: notamap\n"
            "steps:\n  - name: s\n    prompt: /foo\n"
        )
        violations = _validate_single_yaml(path, self.tmp_dir)
        assert any("defaults" in v.source and "mapping" in v.message for v in violations)

    @patch("claude_loop_lib.validation.shutil.which", return_value="/bin/claude")
    def test_steps_not_list(self, _which) -> None:
        path = self._write("steps: notalist\n")
        violations = _validate_single_yaml(path, self.tmp_dir)
        assert any("steps" in v.source and "non-empty list" in v.message for v in violations)

    @patch("claude_loop_lib.validation.shutil.which", return_value="/bin/claude")
    def test_valid_yaml_has_no_errors(self, _which) -> None:
        path = self._write(
            "defaults:\n  model: opus\n"
            "steps:\n  - name: foo_step\n    prompt: /foo\n"
        )
        violations = _validate_single_yaml(path, self.tmp_dir)
        errors = [v for v in violations if v.severity == "error"]
        assert errors == []


class TestValidateStepSchema(_TempCwdBase):
    def _validate_steps(self, steps_yaml_body: str) -> list[Violation]:
        import yaml
        data = yaml.safe_load(steps_yaml_body) or {}
        return _validate_steps_section(data, "yaml/x.yaml", self.tmp_dir)

    def test_missing_prompt(self) -> None:
        violations = self._validate_steps("steps:\n  - name: s\n")
        assert any("prompt" in v.source for v in violations)

    def test_non_string_prompt(self) -> None:
        violations = self._validate_steps("steps:\n  - name: s\n    prompt: 42\n")
        assert any("prompt" in v.source and "non-empty" in v.message for v in violations)

    def test_unknown_key(self) -> None:
        violations = self._validate_steps(
            "steps:\n  - name: s\n    prompt: /foo\n    bogus: 1\n"
        )
        assert any("Unknown keys" in v.message for v in violations)

    def test_override_type_invalid(self) -> None:
        violations = self._validate_steps(
            "steps:\n  - name: s\n    prompt: /foo\n    model: []\n"
        )
        assert any(".model" in v.source and v.severity == "error" for v in violations)

    def test_continue_not_bool(self) -> None:
        violations = self._validate_steps(
            "steps:\n  - name: s\n    prompt: /foo\n    continue: \"yes\"\n"
        )
        assert any(".continue" in v.source for v in violations)

    def test_name_not_string(self) -> None:
        violations = self._validate_steps(
            "steps:\n  - name: 123\n    prompt: /foo\n"
        )
        assert any(".name" in v.source for v in violations)

    def test_multi_violation_aggregation(self) -> None:
        violations = self._validate_steps(
            "steps:\n"
            "  - name: ok\n"
            "    prompt: /foo\n"
            "  - prompt: 42\n"
            "    bogus: 1\n"
        )
        # step 2 should contribute multiple violations; step 1 should not
        assert any("[2]" in v.source for v in violations)
        errs = [v for v in violations if "[1]" in v.source and v.severity == "error"]
        assert errs == []

    def test_valid_steps(self) -> None:
        violations = self._validate_steps(
            "steps:\n  - name: foo_step\n    prompt: /foo\n"
        )
        errors = [v for v in violations if v.severity == "error"]
        assert errors == []


class TestValidateOverrideWhitelist(unittest.TestCase):
    def test_unknown_model_is_warning(self) -> None:
        violations = _check_value_whitelist("model", "gpt-5", "src")
        assert len(violations) == 1
        assert violations[0].severity == "warning"

    def test_unknown_effort_is_warning(self) -> None:
        violations = _check_value_whitelist("effort", "extreme", "src")
        assert len(violations) == 1
        assert violations[0].severity == "warning"

    def test_known_model(self) -> None:
        for m in KNOWN_MODELS:
            assert _check_value_whitelist("model", m, "src") == []

    def test_known_effort(self) -> None:
        for e in KNOWN_EFFORTS:
            assert _check_value_whitelist("effort", e, "src") == []


class TestValidateStepReferences(_TempCwdBase):
    def _validate_steps(self, steps_yaml_body: str) -> list[Violation]:
        import yaml
        data = yaml.safe_load(steps_yaml_body) or {}
        return _validate_steps_section(data, "yaml/x.yaml", self.tmp_dir)

    def test_unresolved_skill_is_error(self) -> None:
        violations = self._validate_steps(
            "steps:\n  - name: s\n    prompt: /nonexistent_skill\n"
        )
        assert any(
            "SKILL" in v.message and v.severity == "error" for v in violations
        )

    def test_existing_skill_resolves(self) -> None:
        violations = self._validate_steps(
            "steps:\n  - name: s\n    prompt: /foo\n"
        )
        assert not any("SKILL" in v.message for v in violations)

    def test_non_slash_prompt_is_not_validated(self) -> None:
        violations = self._validate_steps(
            "steps:\n  - name: s\n    prompt: hello world\n"
        )
        assert not any("SKILL" in v.message for v in violations)

    def test_prompt_with_args_resolves_by_first_token(self) -> None:
        violations = self._validate_steps(
            "steps:\n  - name: s\n    prompt: /foo extra arg\n"
        )
        assert not any("SKILL" in v.message for v in violations)


class TestValidateDefaultsSection(_TempCwdBase):
    def _validate(self, body: str) -> list[Violation]:
        import yaml
        data = yaml.safe_load(body) or {}
        return _validate_defaults_section(data, "yaml/x.yaml")

    def test_unknown_key(self) -> None:
        violations = self._validate("defaults:\n  bogus: x\n")
        assert any("Unknown keys" in v.message for v in violations)

    def test_unknown_model_warns(self) -> None:
        violations = self._validate("defaults:\n  model: super-model\n")
        assert any(v.severity == "warning" for v in violations)


class TestValidateStartupAggregation(_TempCwdBase):
    """End-to-end aggregation: collect across YAMLs; SystemExit on error."""

    def _write_yaml(self, name: str, body: str) -> Path:
        path = self.tmp_dir / name
        path.write_text(body, encoding="utf-8")
        return path

    def _valid_body(self) -> str:
        return (
            "defaults:\n  model: opus\n"
            "steps:\n  - name: foo_step\n    prompt: /foo\n"
        )

    @patch("claude_loop_lib.validation.shutil.which", return_value="/bin/claude")
    def test_all_yamls_valid_passes(self, _which) -> None:
        path = self._write_yaml("wf.yaml", self._valid_body())
        args = _make_args()
        validate_startup(path, args, self.tmp_dir, self.tmp_dir)

    @patch("claude_loop_lib.validation.shutil.which", return_value="/bin/claude")
    @patch("sys.stderr", new_callable=io.StringIO)
    def test_error_raises_systemexit_2(self, _stderr, _which) -> None:
        path = self._write_yaml(
            "wf.yaml", "steps:\n  - name: s\n    prompt: /missing_skill\n"
        )
        args = _make_args()
        with self.assertRaises(SystemExit) as ctx:
            validate_startup(path, args, self.tmp_dir, self.tmp_dir)
        assert ctx.exception.code == 2

    @patch("claude_loop_lib.validation.shutil.which", return_value="/bin/claude")
    @patch("sys.stderr", new_callable=io.StringIO)
    def test_warnings_only_does_not_raise(self, stderr, _which) -> None:
        path = self._write_yaml(
            "wf.yaml",
            "defaults:\n  model: unknown_model\n"
            "steps:\n  - name: s\n    prompt: /foo\n",
        )
        args = _make_args()
        validate_startup(path, args, self.tmp_dir, self.tmp_dir)
        assert "VALIDATION WARNING" in stderr.getvalue()

    @patch("claude_loop_lib.validation.shutil.which", return_value="/bin/claude")
    @patch("sys.stderr", new_callable=io.StringIO)
    def test_multi_yaml_aggregation(self, _stderr, _which) -> None:
        """If one YAML parse fails, other YAMLs are still validated."""
        (self.tmp_dir / "a.yaml").write_text("foo: [unclosed\n", encoding="utf-8")
        (self.tmp_dir / "b.yaml").write_text(
            "steps:\n  - name: s\n    prompt: /missing_skill\n",
            encoding="utf-8",
        )
        errs_a = _validate_single_yaml(self.tmp_dir / "a.yaml", self.tmp_dir)
        errs_b = _validate_single_yaml(self.tmp_dir / "b.yaml", self.tmp_dir)
        assert any("parse error" in v.message.lower() for v in errs_a)
        assert any("SKILL" in v.message for v in errs_b)


class TestValidateRejectsLegacyKeys(_TempCwdBase):
    """ver13.0: validation must reject legacy `mode:` and `command.auto_args`."""

    def _write(self, content: str) -> Path:
        path = self.tmp_dir / "wf.yaml"
        path.write_text(content, encoding="utf-8")
        return path

    @patch("claude_loop_lib.validation.shutil.which", return_value="/bin/claude")
    def test_rejects_toplevel_mode_key(self, _which) -> None:
        path = self._write(
            "mode:\n  auto: true\n"
            "steps:\n  - name: s\n    prompt: /foo\n"
        )
        violations = _validate_single_yaml(path, self.tmp_dir)
        errs = [v for v in violations if v.severity == "error" and "mode" in v.source]
        assert errs, f"expected mode error, got {violations}"
        assert "removed in ver13.0" in errs[0].message

    @patch("claude_loop_lib.validation.shutil.which", return_value="/bin/claude")
    def test_rejects_command_auto_args(self, _which) -> None:
        path = self._write(
            "command:\n"
            "  auto_args:\n"
            "    - --disallowedTools \"AskUserQuestion\"\n"
            "steps:\n  - name: s\n    prompt: /foo\n"
        )
        violations = _validate_single_yaml(path, self.tmp_dir)
        errs = [v for v in violations if v.severity == "error" and "auto_args" in v.source]
        assert errs, f"expected auto_args error, got {violations}"
        assert "removed in ver13.0" in errs[0].message

    @patch("claude_loop_lib.validation.shutil.which", return_value="/bin/claude")
    def test_rejects_unknown_toplevel_key(self, _which) -> None:
        path = self._write(
            "bogus_section: hello\n"
            "steps:\n  - name: s\n    prompt: /foo\n"
        )
        violations = _validate_single_yaml(path, self.tmp_dir)
        errs = [
            v for v in violations
            if v.severity == "error" and "Unknown top-level keys" in v.message
        ]
        assert errs

    @patch("claude_loop_lib.validation.shutil.which", return_value="/bin/claude")
    def test_rejects_unknown_command_key(self, _which) -> None:
        path = self._write(
            "command:\n  bogus: x\n"
            "steps:\n  - name: s\n    prompt: /foo\n"
        )
        violations = _validate_single_yaml(path, self.tmp_dir)
        errs = [
            v for v in violations
            if v.severity == "error" and "command" in v.source and "Unknown" in v.message
        ]
        assert errs


class TestValidateStartupExistingYamls(unittest.TestCase):
    """Regression guard: all repo YAMLs must pass validation."""

    def test_full_yaml_passes(self) -> None:
        from claude_loop_lib.workflow import FULL_YAML_FILENAME
        args = _make_args(workflow="full")
        path = YAML_DIR / FULL_YAML_FILENAME
        validate_startup(path, args, YAML_DIR, DEFAULT_WORKING_DIRECTORY)

    def test_quick_yaml_passes(self) -> None:
        from claude_loop_lib.workflow import QUICK_YAML_FILENAME
        args = _make_args(workflow="quick")
        path = YAML_DIR / QUICK_YAML_FILENAME
        validate_startup(path, args, YAML_DIR, DEFAULT_WORKING_DIRECTORY)

    def test_issue_plan_yaml_passes(self) -> None:
        from claude_loop_lib.workflow import ISSUE_PLAN_YAML_FILENAME
        args = _make_args(workflow="full")
        path = YAML_DIR / ISSUE_PLAN_YAML_FILENAME
        validate_startup(path, args, YAML_DIR, DEFAULT_WORKING_DIRECTORY)

    def test_auto_validates_all_three_yamls(self) -> None:
        args = _make_args(workflow="auto")
        validate_startup("auto", args, YAML_DIR, DEFAULT_WORKING_DIRECTORY)


if __name__ == "__main__":
    unittest.main()
