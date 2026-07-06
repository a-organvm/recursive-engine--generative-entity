"""
Tests for the formatting module.
"""

import pytest
import os

from rege.formatting import (
    Colors,
    colorize,
    colorize_tier,
    colorize_charge,
    colorize_status,
    colorize_organ,
    colorize_mode,
    format_yaml,
    format_csv,
    format_table,
    OutputFormatter,
)


class TestColors:
    """Tests for Colors class."""

    def test_colors_defined(self, monkeypatch):
        """Test color constants are defined."""
        monkeypatch.delenv("NO_COLOR", raising=False)
        import importlib
        import rege.formatting as fmt
        importlib.reload(fmt)

        assert fmt.Colors.RED.startswith("\033[")
        assert fmt.Colors.GREEN.startswith("\033[")
        assert fmt.Colors.RESET == "\033[0m"

    def test_colors_disable(self):
        """Test colors can be disabled."""
        # Save original values
        original_attrs = {attr: getattr(Colors, attr) for attr in dir(Colors) if attr.isupper()}

        # Disable
        Colors.disable()

        assert Colors.RED == ""
        assert Colors.RESET == ""

        # Restore
        for attr, val in original_attrs.items():
            setattr(Colors, attr, val)


class TestColorize:
    """Tests for colorize function."""

    def test_colorize_applies_color(self):
        """Test colorize applies color codes."""
        result = colorize("test", Colors.RED)
        assert Colors.RED in result
        assert Colors.RESET in result
        assert "test" in result

    def test_colorize_tier_latent(self):
        """Test colorize_tier for LATENT."""
        result = colorize_tier("LATENT")
        assert "LATENT" in result

    def test_colorize_tier_critical(self):
        """Test colorize_tier for CRITICAL."""
        result = colorize_tier("CRITICAL")
        assert "CRITICAL" in result

    def test_colorize_charge_low(self):
        """Test colorize_charge for low charge."""
        result = colorize_charge(20)
        assert "20" in result

    def test_colorize_charge_high(self):
        """Test colorize_charge for high charge."""
        result = colorize_charge(90)
        assert "90" in result

    def test_colorize_status_success(self):
        """Test colorize_status for success."""
        result = colorize_status("success")
        assert "success" in result

    def test_colorize_status_failed(self):
        """Test colorize_status for failed."""
        result = colorize_status("failed")
        assert "failed" in result

    def test_colorize_organ(self):
        """Test colorize_organ."""
        result = colorize_organ("HEART_OF_CANON")
        assert "HEART_OF_CANON" in result

    def test_colorize_mode(self):
        """Test colorize_mode."""
        result = colorize_mode("mythic")
        assert "mythic" in result


class TestFormatYaml:
    """Tests for YAML formatting."""

    def test_format_yaml_simple_dict(self):
        """Test YAML format for simple dictionary."""
        data = {"name": "test", "value": 42}
        result = format_yaml(data)
        assert "name: test" in result
        assert "value: 42" in result

    def test_format_yaml_nested_dict(self):
        """Test YAML format for nested dictionary."""
        data = {"outer": {"inner": "value"}}
        result = format_yaml(data)
        assert "outer:" in result
        assert "inner: value" in result

    def test_format_yaml_list(self):
        """Test YAML format for list."""
        data = ["item1", "item2", "item3"]
        result = format_yaml(data)
        assert "- item1" in result
        assert "- item2" in result

    def test_format_yaml_boolean(self):
        """Test YAML format for boolean values."""
        data = {"active": True, "disabled": False}
        result = format_yaml(data)
        assert "active: true" in result
        assert "disabled: false" in result

    def test_format_yaml_null(self):
        """Test YAML format for null values."""
        data = {"empty": None}
        result = format_yaml(data)
        assert "empty: null" in result

    def test_format_yaml_string_quoting(self):
        """Test YAML format quotes special strings."""
        data = {"value": "true", "other": "yes"}  # Would be parsed as bool
        result = format_yaml(data)
        # These should be quoted
        assert '"true"' in result or "'true'" in result
        assert '"yes"' in result or "'yes'" in result


class TestFormatCsv:
    """Tests for CSV formatting."""

    def test_format_csv_basic(self):
        """Test CSV format for basic data."""
        data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
        ]
        result = format_csv(data)
        assert "name,age" in result
        assert "Alice,30" in result
        assert "Bob,25" in result

    def test_format_csv_with_columns(self):
        """Test CSV format with specified columns."""
        data = [
            {"name": "Alice", "age": 30, "city": "NYC"},
            {"name": "Bob", "age": 25, "city": "LA"},
        ]
        result = format_csv(data, columns=["name", "city"])
        assert "name,city" in result
        assert "Alice,NYC" in result
        assert "age" not in result.split("\n")[0]

    def test_format_csv_custom_delimiter(self):
        """Test CSV format with custom delimiter."""
        data = [{"a": 1, "b": 2}]
        result = format_csv(data, delimiter=";")
        assert "a;b" in result
        assert "1;2" in result

    def test_format_csv_escaping(self):
        """Test CSV escapes special characters."""
        data = [{"name": 'Value, with "quotes"'}]
        result = format_csv(data)
        # Should be escaped
        assert '"' in result

    def test_format_csv_empty(self):
        """Test CSV format for empty data."""
        result = format_csv([])
        assert result == ""


class TestFormatTable:
    """Tests for table formatting."""

    def test_format_table_basic(self):
        """Test table format for basic data."""
        data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
        ]
        result = format_table(data)
        assert "NAME" in result
        assert "AGE" in result
        assert "Alice" in result
        assert "Bob" in result
        assert "|" in result
        assert "+" in result

    def test_format_table_with_columns(self):
        """Test table format with specified columns."""
        data = [
            {"name": "Alice", "age": 30, "city": "NYC"},
        ]
        result = format_table(data, columns=["name", "city"])
        assert "NAME" in result
        assert "CITY" in result
        assert "AGE" not in result

    def test_format_table_with_headers(self):
        """Test table format with custom headers."""
        data = [{"id": 1, "val": "test"}]
        headers = {"id": "ID Number", "val": "Value"}
        result = format_table(data, headers=headers)
        assert "ID Number" in result
        assert "Value" in result

    def test_format_table_empty(self):
        """Test table format for empty data."""
        result = format_table([])
        assert "No data" in result


class TestOutputFormatter:
    """Tests for OutputFormatter class."""

    def test_formatter_json(self):
        """Test JSON format output."""
        formatter = OutputFormatter(format_type="json")
        data = {"key": "value"}
        result = formatter.format(data)
        assert '"key"' in result
        assert '"value"' in result

    def test_formatter_yaml(self):
        """Test YAML format output."""
        formatter = OutputFormatter(format_type="yaml")
        data = {"key": "value"}
        result = formatter.format(data)
        assert "key: value" in result

    def test_formatter_csv(self):
        """Test CSV format output."""
        formatter = OutputFormatter(format_type="csv")
        data = [{"a": 1, "b": 2}]
        result = formatter.format(data)
        assert "a,b" in result

    def test_formatter_table(self):
        """Test table format output."""
        formatter = OutputFormatter(format_type="table")
        data = [{"a": 1, "b": 2}]
        result = formatter.format(data)
        assert "|" in result

    def test_formatter_text_default(self):
        """Test default text format output."""
        formatter = OutputFormatter(format_type="text")
        data = {"key": "value"}
        result = formatter.format(data)
        assert "key: value" in result

    def test_formatter_success_message(self):
        """Test success message formatting."""
        formatter = OutputFormatter(use_color=True)
        result = formatter.success("Operation complete")
        assert "Operation complete" in result

    def test_formatter_error_message(self):
        """Test error message formatting."""
        formatter = OutputFormatter(use_color=True)
        result = formatter.error("Something failed")
        assert "Something failed" in result

    def test_formatter_warning_message(self):
        """Test warning message formatting."""
        formatter = OutputFormatter(use_color=True)
        result = formatter.warning("Be careful")
        assert "Be careful" in result

    def test_formatter_info_message(self):
        """Test info message formatting."""
        formatter = OutputFormatter(use_color=True)
        result = formatter.info("Note this")
        assert "Note this" in result

    def test_formatter_no_color(self):
        """Test formatter with color disabled."""
        formatter = OutputFormatter(use_color=False)
        result = formatter.success("Test")
        # Should not contain color codes
        assert "\033[" not in result


class TestEnhancedREPLCommands:
    """Tests for enhanced REPL commands using CliRunner."""

    @pytest.fixture
    def runner(self):
        from click.testing import CliRunner
        return CliRunner()

    def test_repl_help_command(self, runner):
        """Test :help command in REPL."""
        from rege.cli import cli
        result = runner.invoke(cli, ['repl'], input=':help\nexit\n')
        assert "HELP" in result.output
        assert ":organs" in result.output or "organs" in result.output

    def test_repl_status_command(self, runner):
        """Test :status command in REPL."""
        from rege.cli import cli
        result = runner.invoke(cli, ['repl'], input=':status\nexit\n')
        assert "Queue" in result.output

    def test_repl_organs_command(self, runner):
        """Test :organs command in REPL."""
        from rege.cli import cli
        result = runner.invoke(cli, ['repl'], input=':organs\nexit\n')
        assert "HEART_OF_CANON" in result.output

    def test_repl_vars_command(self, runner):
        """Test :vars command in REPL."""
        from rege.cli import cli
        result = runner.invoke(cli, ['repl'], input=':vars\nexit\n')
        assert "CHARGE" in result.output
        assert "DEPTH" in result.output

    def test_repl_set_command(self, runner):
        """Test :set command in REPL."""
        from rege.cli import cli
        result = runner.invoke(cli, ['repl'], input=':set CHARGE 75\n:vars\nexit\n')
        assert "Set $CHARGE = 75" in result.output

    def test_repl_set_depth(self, runner):
        """Test :set DEPTH command in REPL."""
        from rege.cli import cli
        result = runner.invoke(cli, ['repl'], input=':set DEPTH light\nexit\n')
        assert "Set $DEPTH = light" in result.output

    def test_repl_history_empty(self, runner):
        """Test :history command with no history."""
        from rege.cli import cli
        result = runner.invoke(cli, ['repl'], input=':history\nexit\n')
        assert "No history" in result.output or "HISTORY" in result.output

    def test_repl_last_no_result(self, runner):
        """Test :last command with no previous result."""
        from rege.cli import cli
        result = runner.invoke(cli, ['repl'], input=':last\nexit\n')
        assert "No previous result" in result.output

    def test_repl_modes_command(self, runner):
        """Test :modes command in REPL."""
        from rege.cli import cli
        result = runner.invoke(cli, ['repl'], input=':modes HEART_OF_CANON\nexit\n')
        assert "MODES" in result.output or "mythic" in result.output

    def test_repl_modes_unknown_organ(self, runner):
        """Test :modes command with unknown organ."""
        from rege.cli import cli
        result = runner.invoke(cli, ['repl'], input=':modes UNKNOWN_ORGAN\nexit\n')
        assert "not found" in result.output.lower()

    def test_repl_clear_command(self, runner):
        """Test :clear command in REPL."""
        from rege.cli import cli
        result = runner.invoke(cli, ['repl'], input=':clear\nexit\n')
        # Clear should still show console header after
        assert result.exit_code == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
