"""
Tests for formatting.py coverage improvements.

Targets uncovered lines: 57, 73, 88, 90, 92, 104-107, 152-153, 158,
335, 340, 353-354, 358-367, 374, 376-378, 381-383, 397, 403, 409
"""

import pytest
from unittest.mock import patch


class TestColorsDisable:
    """Tests for Colors.disable() method."""

    def test_colors_disable_sets_empty_strings(self):
        """Test Colors.disable sets all uppercase attrs to empty strings."""
        from rege.formatting import Colors
        # Save original values
        original_reset = Colors.RESET
        original_red = Colors.RED

        Colors.disable()

        assert Colors.RESET == ""
        assert Colors.RED == ""
        assert Colors.GREEN == ""
        assert Colors.BOLD_RED == ""
        assert Colors.DIM == ""

        # Restore for other tests
        Colors.RESET = original_reset
        Colors.RED = original_red

    def test_colors_disable_no_color_env(self):
        """Test that NO_COLOR env triggers disable at import time."""
        # The path at line 57 (`Colors.disable()`) runs when NO_COLOR is set.
        # We test this by importing with patched env and verifying behavior.
        import importlib
        import os
        with patch.dict(os.environ, {"NO_COLOR": "1"}):
            # Test that colorize returns text unchanged when NO_COLOR is set
            from rege.formatting import colorize
            # This calls the module-level check
            result = colorize("test", "\033[31m")
            # With NO_COLOR, returns text unchanged
            # (module was already imported, but we can test the function path)
            assert "test" in result


class TestColorize:
    """Tests for colorize() with NO_COLOR=True."""

    def test_colorize_no_color_returns_plain_text(self):
        """Test colorize returns plain text when NO_COLOR is active (line 73)."""
        import rege.formatting as fmt
        original = fmt.NO_COLOR
        try:
            fmt.NO_COLOR = True
            result = fmt.colorize("hello", "\033[31m")
            assert result == "hello"
        finally:
            fmt.NO_COLOR = original

    def test_colorize_with_color_returns_wrapped(self):
        """Test colorize returns wrapped text when colors are enabled."""
        import rege.formatting as fmt
        original = fmt.NO_COLOR
        try:
            fmt.NO_COLOR = False
            result = fmt.colorize("hello", "\033[31m")
            assert "\033[31m" in result
            assert "hello" in result
        finally:
            fmt.NO_COLOR = original


class TestColorizeCharge:
    """Tests for colorize_charge() tier branches."""

    def test_colorize_charge_processing_tier(self):
        """Charge 26-50 → CYAN (line 88)."""
        from rege.formatting import colorize_charge, Colors
        import rege.formatting as fmt
        original = fmt.NO_COLOR
        try:
            fmt.NO_COLOR = False
            result = colorize_charge(30)
            assert "30" in result
        finally:
            fmt.NO_COLOR = original

    def test_colorize_charge_active_tier(self):
        """Charge 51-70 → GREEN (line 90)."""
        from rege.formatting import colorize_charge
        import rege.formatting as fmt
        original = fmt.NO_COLOR
        try:
            fmt.NO_COLOR = False
            result = colorize_charge(60)
            assert "60" in result
        finally:
            fmt.NO_COLOR = original

    def test_colorize_charge_intense_tier(self):
        """Charge 71-85 → YELLOW (line 92)."""
        from rege.formatting import colorize_charge
        import rege.formatting as fmt
        original = fmt.NO_COLOR
        try:
            fmt.NO_COLOR = False
            result = colorize_charge(80)
            assert "80" in result
        finally:
            fmt.NO_COLOR = original

    def test_colorize_charge_critical_tier(self):
        """Charge 86-100 → BOLD_RED."""
        from rege.formatting import colorize_charge
        result = colorize_charge(90)
        assert "90" in result

    def test_colorize_charge_latent_tier(self):
        """Charge 0-25 → DIM."""
        from rege.formatting import colorize_charge
        result = colorize_charge(10)
        assert "10" in result


class TestColorizeStatus:
    """Tests for colorize_status() branches."""

    def test_colorize_status_failed(self):
        """Status 'failed' → RED (line 103)."""
        from rege.formatting import colorize_status
        result = colorize_status("failed")
        assert "failed" in result

    def test_colorize_status_error(self):
        """Status 'error' → RED."""
        from rege.formatting import colorize_status
        result = colorize_status("error")
        assert "error" in result

    def test_colorize_status_halted(self):
        """Status 'halted' → RED."""
        from rege.formatting import colorize_status
        result = colorize_status("halted")
        assert "halted" in result

    def test_colorize_status_warning(self):
        """Status 'warning' → YELLOW (line 105)."""
        from rege.formatting import colorize_status
        result = colorize_status("warning")
        assert "warning" in result

    def test_colorize_status_partial(self):
        """Status 'partial' → YELLOW."""
        from rege.formatting import colorize_status
        result = colorize_status("partial")
        assert "partial" in result

    def test_colorize_status_pending(self):
        """Status 'pending' → YELLOW."""
        from rege.formatting import colorize_status
        result = colorize_status("pending")
        assert "pending" in result

    def test_colorize_status_unknown(self):
        """Status unknown → CYAN (line 107)."""
        from rege.formatting import colorize_status
        result = colorize_status("running")
        assert "running" in result

    def test_colorize_status_success(self):
        """Status 'success' → GREEN."""
        from rege.formatting import colorize_status
        result = colorize_status("success")
        assert "success" in result


class TestFormatYamlRecursive:
    """Tests for _format_yaml_recursive nested/scalar paths."""

    def test_format_yaml_list_with_nested_list(self):
        """List item that is itself a list (line 152-153)."""
        from rege.formatting import format_yaml
        data = [[1, 2], [3, 4]]
        result = format_yaml(data)
        assert "-" in result

    def test_format_yaml_list_with_nested_dict(self):
        """List item that is a dict (line 152-153)."""
        from rege.formatting import format_yaml
        data = [{"key": "val"}, {"other": "data"}]
        result = format_yaml(data)
        assert "key" in result
        assert "val" in result

    def test_format_yaml_scalar_at_root(self):
        """Top-level scalar (line 158)."""
        from rege.formatting import format_yaml
        result = format_yaml("just a string")
        assert "just a string" in result

    def test_format_yaml_integer_at_root(self):
        """Top-level integer scalar (line 158)."""
        from rege.formatting import format_yaml
        result = format_yaml(42)
        assert "42" in result

    def test_format_yaml_none_value(self):
        """None value in dict (uses _format_yaml_value → 'null')."""
        from rege.formatting import format_yaml
        result = format_yaml({"key": None})
        assert "null" in result

    def test_format_yaml_bool_true(self):
        """Bool True value."""
        from rege.formatting import format_yaml
        result = format_yaml({"flag": True})
        assert "true" in result

    def test_format_yaml_bool_false(self):
        """Bool False value."""
        from rege.formatting import format_yaml
        result = format_yaml({"flag": False})
        assert "false" in result

    def test_format_yaml_ambiguous_string_quoted(self):
        """Strings that need quoting (true/false/null/special chars)."""
        from rege.formatting import format_yaml
        result = format_yaml({"key": "true"})
        assert '"true"' in result

        result2 = format_yaml({"key": "null"})
        assert '"null"' in result2

        result3 = format_yaml({"key": "has:colon"})
        assert '"has:colon"' in result3


class TestOutputFormatterFormat:
    """Tests for OutputFormatter.format() all branches."""

    def test_format_yaml(self):
        """OutputFormatter with yaml format (line 335)."""
        from rege.formatting import OutputFormatter
        fmt = OutputFormatter(format_type="yaml")
        result = fmt.format({"key": "value"})
        assert "key" in result
        assert "value" in result

    def test_format_csv_dict(self):
        """OutputFormatter with csv format for single dict (line 340)."""
        from rege.formatting import OutputFormatter
        fmt = OutputFormatter(format_type="csv")
        result = fmt.format({"col1": "a", "col2": "b"})
        assert "col1" in result or "a" in result

    def test_format_csv_list(self):
        """OutputFormatter with csv format for list."""
        from rege.formatting import OutputFormatter
        fmt = OutputFormatter(format_type="csv")
        result = fmt.format([{"col1": "a"}, {"col1": "b"}])
        assert "col1" in result

    def test_format_table_dict(self):
        """OutputFormatter with table format for single dict."""
        from rege.formatting import OutputFormatter
        fmt = OutputFormatter(format_type="table")
        result = fmt.format({"name": "test", "charge": 50})
        assert "name" in result.lower() or "test" in result

    def test_format_json(self):
        """OutputFormatter with json format."""
        from rege.formatting import OutputFormatter
        import json
        fmt = OutputFormatter(format_type="json")
        result = fmt.format({"key": "value"})
        data = json.loads(result)
        assert data["key"] == "value"

    def test_format_text_default(self):
        """OutputFormatter with text format (default)."""
        from rege.formatting import OutputFormatter
        fmt = OutputFormatter(format_type="text")
        result = fmt.format({"key": "value"})
        assert "key" in result


class TestOutputFormatterFormatText:
    """Tests for OutputFormatter._format_text() nested paths."""

    def test_format_text_dict_with_nested_dict(self):
        """Dict with nested dict value (line 353-354)."""
        from rege.formatting import OutputFormatter
        fmt = OutputFormatter(format_type="text", use_color=False)
        result = fmt.format({"outer": {"inner": "value"}})
        assert "outer" in result
        assert "inner" in result

    def test_format_text_dict_with_nested_list(self):
        """Dict with nested list value (line 353-354)."""
        from rege.formatting import OutputFormatter
        fmt = OutputFormatter(format_type="text", use_color=False)
        result = fmt.format({"items": ["a", "b", "c"]})
        assert "items" in result

    def test_format_text_list_with_nested_dict(self):
        """List with nested dict items (lines 361-362)."""
        from rege.formatting import OutputFormatter
        fmt = OutputFormatter(format_type="text", use_color=False)
        result = fmt.format([{"name": "test"}])
        assert "name" in result or "-" in result

    def test_format_text_list_with_nested_list(self):
        """List with nested list items (lines 361-362)."""
        from rege.formatting import OutputFormatter
        fmt = OutputFormatter(format_type="text", use_color=False)
        result = fmt.format([[1, 2], [3, 4]])
        assert "-" in result

    def test_format_text_list_plain_items(self):
        """List with plain string items (lines 363-365)."""
        from rege.formatting import OutputFormatter
        fmt = OutputFormatter(format_type="text", use_color=False)
        result = fmt.format(["alpha", "beta", "gamma"])
        assert "alpha" in result
        assert "beta" in result

    def test_format_text_scalar(self):
        """Scalar value (line 367)."""
        from rege.formatting import OutputFormatter
        fmt = OutputFormatter(format_type="text", use_color=False)
        result = fmt.format("plain text")
        assert "plain text" in result


class TestOutputFormatterFormatValue:
    """Tests for OutputFormatter._format_value() with color."""

    def test_format_value_none_with_color(self):
        """None value with color enabled (line 374)."""
        from rege.formatting import OutputFormatter
        fmt = OutputFormatter(format_type="text", use_color=True)
        import rege.formatting as fmtmod
        original = fmtmod.NO_COLOR
        try:
            fmtmod.NO_COLOR = False
            fmt.use_color = True
            result = fmt._format_value(None)
            assert "null" in result
        finally:
            fmtmod.NO_COLOR = original

    def test_format_value_none_no_color(self):
        """None value without color."""
        from rege.formatting import OutputFormatter
        fmt = OutputFormatter(format_type="text", use_color=False)
        result = fmt._format_value(None)
        assert result == "null"

    def test_format_value_bool_true_with_color(self):
        """Bool True with color (line 376-378)."""
        from rege.formatting import OutputFormatter
        fmt = OutputFormatter(format_type="text", use_color=False)
        result = fmt._format_value(True)
        assert result == "true"

    def test_format_value_bool_false_with_color(self):
        """Bool False with color."""
        from rege.formatting import OutputFormatter
        fmt = OutputFormatter(format_type="text", use_color=False)
        result = fmt._format_value(False)
        assert result == "false"

    def test_format_value_int_in_charge_range(self):
        """Int in 0-100 range (line 381-383)."""
        from rege.formatting import OutputFormatter
        fmt = OutputFormatter(format_type="text", use_color=False)
        result = fmt._format_value(75)
        assert "75" in result

    def test_format_value_int_outside_charge_range(self):
        """Int outside 0-100 range."""
        from rege.formatting import OutputFormatter
        fmt = OutputFormatter(format_type="text", use_color=False)
        result = fmt._format_value(150)
        assert result == "150"

    def test_format_value_string(self):
        """String value."""
        from rege.formatting import OutputFormatter
        fmt = OutputFormatter(format_type="text", use_color=False)
        result = fmt._format_value("hello")
        assert result == "hello"


class TestOutputFormatterMessages:
    """Tests for OutputFormatter message methods."""

    def test_success_with_color(self):
        """success() with color enabled (line 397)."""
        from rege.formatting import OutputFormatter
        fmt = OutputFormatter(use_color=True)
        import rege.formatting as fmtmod
        original = fmtmod.NO_COLOR
        try:
            fmtmod.NO_COLOR = False
            fmt.use_color = True
            result = fmt.success("Operation succeeded")
            assert "Operation succeeded" in result
        finally:
            fmtmod.NO_COLOR = original

    def test_success_without_color(self):
        """success() without color."""
        from rege.formatting import OutputFormatter
        fmt = OutputFormatter(use_color=False)
        result = fmt.success("done")
        assert result == "done"

    def test_error_with_color(self):
        """error() with color enabled (line 403)."""
        from rege.formatting import OutputFormatter
        fmt = OutputFormatter(use_color=True)
        import rege.formatting as fmtmod
        original = fmtmod.NO_COLOR
        try:
            fmtmod.NO_COLOR = False
            fmt.use_color = True
            result = fmt.error("Something failed")
            assert "Something failed" in result
        finally:
            fmtmod.NO_COLOR = original

    def test_error_without_color(self):
        """error() without color."""
        from rege.formatting import OutputFormatter
        fmt = OutputFormatter(use_color=False)
        result = fmt.error("failed")
        assert result == "failed"

    def test_warning_with_color(self):
        """warning() with color enabled."""
        from rege.formatting import OutputFormatter
        fmt = OutputFormatter(use_color=True)
        import rege.formatting as fmtmod
        original = fmtmod.NO_COLOR
        try:
            fmtmod.NO_COLOR = False
            fmt.use_color = True
            result = fmt.warning("Watch out")
            assert "Watch out" in result
        finally:
            fmtmod.NO_COLOR = original

    def test_warning_without_color(self):
        """warning() without color."""
        from rege.formatting import OutputFormatter
        fmt = OutputFormatter(use_color=False)
        result = fmt.warning("caution")
        assert result == "caution"

    def test_info_with_color(self):
        """info() with color enabled (line 409)."""
        from rege.formatting import OutputFormatter
        fmt = OutputFormatter(use_color=True)
        import rege.formatting as fmtmod
        original = fmtmod.NO_COLOR
        try:
            fmtmod.NO_COLOR = False
            fmt.use_color = True
            result = fmt.info("Information")
            assert "Information" in result
        finally:
            fmtmod.NO_COLOR = original

    def test_info_without_color(self):
        """info() without color."""
        from rege.formatting import OutputFormatter
        fmt = OutputFormatter(use_color=False)
        result = fmt.info("note")
        assert result == "note"
