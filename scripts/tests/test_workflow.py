"""Tests for scripts/claude_loop_lib/workflow.py."""
from __future__ import annotations

import unittest
from pathlib import Path
from typing import Any

from . import _bootstrap  # noqa: F401  — must precede claude_loop_lib imports

from claude_loop_lib.commands import build_command
from claude_loop_lib.workflow import (
    load_workflow, get_steps, resolve_defaults,
    resolve_command_config,
    resolve_workflow_value,
    FULL_YAML_FILENAME, QUICK_YAML_FILENAME, ISSUE_PLAN_YAML_FILENAME,
    SCOUT_YAML_FILENAME,
    OVERRIDE_STRING_KEYS,
)


_UNSET = object()


class TestResolveCommandConfigRejectsAutoArgs(unittest.TestCase):
    """ver13.0: command.auto_args is removed and must be rejected."""

    def test_rejects_auto_args_key(self) -> None:
        config = {"command": {"auto_args": ["--disallowedTools AskUserQuestion"]}}
        with self.assertRaises(SystemExit) as cm:
            resolve_command_config(config)
        assert "auto_args" in str(cm.exception)

    def test_accepts_command_without_auto_args(self) -> None:
        config = {"command": {"args": ["--flag"]}}
        executable, prompt_flag, common_args = resolve_command_config(config)
        assert executable == "claude"
        assert prompt_flag == "-p"
        assert common_args == ["--flag"]


class TestResolveDefaults(unittest.TestCase):
    """Tests for resolve_defaults()."""

    def test_returns_empty_when_key_absent(self) -> None:
        assert resolve_defaults({}) == {}

    def test_parses_model_and_effort(self) -> None:
        result = resolve_defaults({"defaults": {"model": "opus", "effort": "high"}})
        assert result == {"model": "opus", "effort": "high"}

    def test_omits_absent_keys(self) -> None:
        result = resolve_defaults({"defaults": {"model": "opus"}})
        assert result == {"model": "opus"}
        assert "effort" not in result

    def test_raises_on_non_mapping(self) -> None:
        with self.assertRaises(SystemExit):
            resolve_defaults({"defaults": "opus"})

    def test_raises_on_empty_string(self) -> None:
        with self.assertRaises(SystemExit):
            resolve_defaults({"defaults": {"model": ""}})

    def test_raises_on_non_string(self) -> None:
        with self.assertRaises(SystemExit):
            resolve_defaults({"defaults": {"effort": 5}})


class TestGetStepsModelEffort(unittest.TestCase):
    """Tests for get_steps() with model/effort fields."""

    def _config(self, step: dict) -> dict:
        return {"steps": [step]}

    def test_step_without_model_effort_omits_keys(self) -> None:
        steps = get_steps(self._config({"name": "s", "prompt": "/s"}))
        assert "model" not in steps[0]
        assert "effort" not in steps[0]

    def test_step_with_model_and_effort(self) -> None:
        steps = get_steps(self._config(
            {"name": "s", "prompt": "/s", "model": "opus", "effort": "high"}
        ))
        assert steps[0]["model"] == "opus"
        assert steps[0]["effort"] == "high"

    def test_step_with_only_effort(self) -> None:
        steps = get_steps(self._config({"name": "s", "prompt": "/s", "effort": "low"}))
        assert steps[0]["effort"] == "low"
        assert "model" not in steps[0]

    def test_raises_on_empty_model(self) -> None:
        with self.assertRaises(SystemExit):
            get_steps(self._config({"name": "s", "prompt": "/s", "model": ""}))

    def test_raises_on_non_string_effort(self) -> None:
        with self.assertRaises(SystemExit):
            get_steps(self._config({"name": "s", "prompt": "/s", "effort": 5}))

    def test_none_value_treated_as_absent(self) -> None:
        steps = get_steps(self._config(
            {"name": "s", "prompt": "/s", "model": None, "effort": None}
        ))
        assert "model" not in steps[0]
        assert "effort" not in steps[0]


class TestGetStepsContinue(unittest.TestCase):
    """Tests for get_steps() with the 'continue' field."""

    def _config(self, step: dict) -> dict:
        return {"steps": [step]}

    def test_omitted_continue_not_in_step_entry(self) -> None:
        steps = get_steps(self._config({"name": "s", "prompt": "/s"}))
        assert "continue" not in steps[0]

    def test_explicit_false_is_retained(self) -> None:
        steps = get_steps(self._config({"name": "s", "prompt": "/s", "continue": False}))
        assert steps[0]["continue"] is False

    def test_explicit_true_is_retained(self) -> None:
        steps = get_steps(self._config({"name": "s", "prompt": "/s", "continue": True}))
        assert steps[0]["continue"] is True

    def test_non_bool_string_raises(self) -> None:
        with self.assertRaises(SystemExit):
            get_steps(self._config({"name": "s", "prompt": "/s", "continue": "yes"}))

    def test_integer_raises(self) -> None:
        with self.assertRaises(SystemExit):
            get_steps(self._config({"name": "s", "prompt": "/s", "continue": 1}))

    def test_none_treated_as_absent(self) -> None:
        steps = get_steps(self._config({"name": "s", "prompt": "/s", "continue": None}))
        assert "continue" not in steps[0]


class TestResolveWorkflowValue(unittest.TestCase):
    """Tests for workflow.resolve_workflow_value()."""

    def setUp(self) -> None:
        self.yaml_dir = Path("/fake/scripts")

    def test_resolve_auto_returns_sentinel(self) -> None:
        assert resolve_workflow_value("auto", self.yaml_dir) == "auto"

    def test_resolve_full_returns_full_yaml_path(self) -> None:
        result = resolve_workflow_value("full", self.yaml_dir)
        assert result == self.yaml_dir / FULL_YAML_FILENAME

    def test_resolve_quick_returns_quick_yaml_path(self) -> None:
        result = resolve_workflow_value("quick", self.yaml_dir)
        assert result == self.yaml_dir / QUICK_YAML_FILENAME

    def test_resolve_scout_returns_scout_yaml_path(self) -> None:
        result = resolve_workflow_value("scout", self.yaml_dir)
        assert result == self.yaml_dir / SCOUT_YAML_FILENAME

    def test_resolve_path_like_returns_path(self) -> None:
        result = resolve_workflow_value("/tmp/foo.yaml", self.yaml_dir)
        assert result == Path("/tmp/foo.yaml")

    def test_resolve_relative_path_preserved(self) -> None:
        result = resolve_workflow_value("other.yaml", self.yaml_dir)
        assert result == Path("other.yaml")

    def test_reserved_values_are_case_sensitive(self) -> None:
        result = resolve_workflow_value("AUTO", self.yaml_dir)
        assert result == Path("AUTO")


class TestResolveDefaultsOverrideKeys(unittest.TestCase):
    """Tests for resolve_defaults() with new override keys (ver10.0)."""

    def test_parses_system_prompt(self) -> None:
        result = resolve_defaults({"defaults": {"system_prompt": "hello"}})
        assert result == {"system_prompt": "hello"}

    def test_parses_append_system_prompt(self) -> None:
        result = resolve_defaults({"defaults": {"append_system_prompt": "extra"}})
        assert result == {"append_system_prompt": "extra"}

    def test_parses_all_four_keys_together(self) -> None:
        result = resolve_defaults({
            "defaults": {
                "model": "opus",
                "effort": "high",
                "system_prompt": "sp",
                "append_system_prompt": "asp",
            }
        })
        assert result == {
            "model": "opus",
            "effort": "high",
            "system_prompt": "sp",
            "append_system_prompt": "asp",
        }

    def test_raises_on_unknown_key(self) -> None:
        with self.assertRaises(SystemExit) as cm:
            resolve_defaults({"defaults": {"temperature": "0.5"}})
        assert "temperature" in str(cm.exception)
        assert "Allowed keys" in str(cm.exception)

    def test_raises_on_empty_system_prompt(self) -> None:
        with self.assertRaises(SystemExit):
            resolve_defaults({"defaults": {"system_prompt": ""}})

    def test_raises_on_non_string_append(self) -> None:
        with self.assertRaises(SystemExit):
            resolve_defaults({"defaults": {"append_system_prompt": 5}})


class TestGetStepsOverrideKeys(unittest.TestCase):
    """Tests for get_steps() with new override keys (ver10.0)."""

    def _config(self, step: dict) -> dict:
        return {"steps": [step]}

    def test_step_with_system_prompt(self) -> None:
        steps = get_steps(self._config(
            {"name": "s", "prompt": "/s", "system_prompt": "hello"}
        ))
        assert steps[0]["system_prompt"] == "hello"

    def test_step_with_append_system_prompt(self) -> None:
        steps = get_steps(self._config(
            {"name": "s", "prompt": "/s", "append_system_prompt": "extra"}
        ))
        assert steps[0]["append_system_prompt"] == "extra"

    def test_step_with_all_four_overrides(self) -> None:
        steps = get_steps(self._config({
            "name": "s",
            "prompt": "/s",
            "model": "opus",
            "effort": "high",
            "system_prompt": "sp",
            "append_system_prompt": "asp",
        }))
        assert steps[0]["model"] == "opus"
        assert steps[0]["effort"] == "high"
        assert steps[0]["system_prompt"] == "sp"
        assert steps[0]["append_system_prompt"] == "asp"

    def test_step_unknown_key_raises(self) -> None:
        with self.assertRaises(SystemExit) as cm:
            get_steps(self._config(
                {"name": "s", "prompt": "/s", "temperature": "0.5"}
            ))
        assert "temperature" in str(cm.exception)
        assert "Allowed keys" in str(cm.exception)

    def test_step_omits_keys_returns_no_keys(self) -> None:
        steps = get_steps(self._config({"name": "s", "prompt": "/s"}))
        assert "system_prompt" not in steps[0]
        assert "append_system_prompt" not in steps[0]

    def test_step_none_value_treated_as_absent(self) -> None:
        steps = get_steps(self._config({
            "name": "s",
            "prompt": "/s",
            "system_prompt": None,
            "append_system_prompt": None,
        }))
        assert "system_prompt" not in steps[0]
        assert "append_system_prompt" not in steps[0]

    def test_step_empty_string_raises_for_each_key(self) -> None:
        for key in OVERRIDE_STRING_KEYS:
            with self.subTest(key=key):
                with self.assertRaises(SystemExit):
                    get_steps(self._config({"name": "s", "prompt": "/s", key: ""}))


class TestYamlSyncOverrideKeys(unittest.TestCase):
    """Verify the 3 shipped workflow YAMLs only use allowed override keys."""

    def _yaml_path(self, name: str) -> Path:
        return Path(__file__).resolve().parent.parent.parent / "scripts" / name

    def test_full_yaml_uses_only_allowed_keys(self) -> None:
        config = load_workflow(self._yaml_path(FULL_YAML_FILENAME))
        steps = get_steps(config)
        defaults = resolve_defaults(config)
        # Sanity: parsing succeeded, so all keys are within ALLOWED sets.
        assert isinstance(steps, list) and len(steps) > 0
        assert isinstance(defaults, dict)

    def test_quick_yaml_uses_only_allowed_keys(self) -> None:
        config = load_workflow(self._yaml_path(QUICK_YAML_FILENAME))
        steps = get_steps(config)
        defaults = resolve_defaults(config)
        assert isinstance(steps, list) and len(steps) > 0
        assert isinstance(defaults, dict)

    def test_issue_plan_yaml_uses_only_allowed_keys(self) -> None:
        config = load_workflow(self._yaml_path(ISSUE_PLAN_YAML_FILENAME))
        steps = get_steps(config)
        defaults = resolve_defaults(config)
        assert isinstance(steps, list) and len(steps) > 0
        assert isinstance(defaults, dict)

    def test_scout_yaml_uses_only_allowed_keys(self) -> None:
        config = load_workflow(self._yaml_path(SCOUT_YAML_FILENAME))
        steps = get_steps(config)
        defaults = resolve_defaults(config)
        assert isinstance(steps, list) and len(steps) > 0
        assert isinstance(defaults, dict)


class TestOverrideInheritanceMatrix(unittest.TestCase):
    """3-stage inheritance matrix verification for each override key (ver10.0)."""

    _FLAGS = {
        "model": "--model",
        "effort": "--effort",
        "system_prompt": "--system-prompt",
        "append_system_prompt": "--append-system-prompt",
    }

    def _build(self, key: str, step_value: Any, defaults_value: Any) -> list[str]:
        step: dict[str, Any] = {"name": "s", "prompt": "/s", "args": []}
        if step_value is not _UNSET:
            step[key] = step_value
        defaults: dict[str, str] = {}
        if defaults_value is not _UNSET:
            defaults[key] = defaults_value
        return build_command("claude", "-p", [], step, defaults=defaults)

    def _flag_value(self, cmd: list[str], flag: str) -> str | None:
        if flag not in cmd:
            return None
        return cmd[cmd.index(flag) + 1]

    def _assert_contains(self, key: str, value: str | None, expected: str) -> None:
        # ver13.0: --append-system-prompt is always emitted because the
        # unattended system prompt is injected unconditionally. The effective
        # override value is concatenated to the tail, so we check containment
        # rather than equality for that key.
        if key == "append_system_prompt":
            assert value is not None and expected in value
        else:
            assert value == expected

    def test_step_value_wins_when_both_set(self) -> None:
        for key in OVERRIDE_STRING_KEYS:
            with self.subTest(key=key):
                cmd = self._build(key, "STEP", "DEFAULT")
                value = self._flag_value(cmd, self._FLAGS[key])
                self._assert_contains(key, value, "STEP")
                if key == "append_system_prompt":
                    assert "DEFAULT" not in (value or "")

    def test_step_value_used_when_defaults_absent(self) -> None:
        for key in OVERRIDE_STRING_KEYS:
            with self.subTest(key=key):
                cmd = self._build(key, "STEP", _UNSET)
                value = self._flag_value(cmd, self._FLAGS[key])
                self._assert_contains(key, value, "STEP")

    def test_defaults_used_when_step_absent(self) -> None:
        for key in OVERRIDE_STRING_KEYS:
            with self.subTest(key=key):
                cmd = self._build(key, _UNSET, "DEFAULT")
                value = self._flag_value(cmd, self._FLAGS[key])
                self._assert_contains(key, value, "DEFAULT")

    def test_flag_omitted_when_neither_set(self) -> None:
        for key in OVERRIDE_STRING_KEYS:
            with self.subTest(key=key):
                cmd = self._build(key, _UNSET, _UNSET)
                if key == "append_system_prompt":
                    # ver13.0: unattended prompt is always injected via
                    # --append-system-prompt. The flag is still present; we
                    # only assert the override value didn't leak into it.
                    value = self._flag_value(cmd, self._FLAGS[key])
                    assert value is not None
                    assert "DEFAULT" not in value and "STEP" not in value
                else:
                    assert self._FLAGS[key] not in cmd

    def test_step_none_falls_back_to_defaults(self) -> None:
        # Note: step entries are produced by get_steps() which strips None
        # values. This test verifies build_command's behavior when callers pass
        # a step dict without the key (the post-get_steps state after a None
        # YAML entry).
        for key in OVERRIDE_STRING_KEYS:
            with self.subTest(key=key):
                cmd = self._build(key, _UNSET, "DEFAULT")
                value = self._flag_value(cmd, self._FLAGS[key])
                self._assert_contains(key, value, "DEFAULT")


if __name__ == "__main__":
    unittest.main()
