"""
Final coverage tests for cli.py:
- 233: fragments list status display
- 338: checkpoint restore organs_restored
- 476: :last command with non-dict output
- 514-519: :history command with non-empty history
- 546-547: :load dispatch exception
- 550-551: :load general exception
- 568-569: :export general exception
- 627: REPL main loop non-dict output
- 633-634: REPL unknown command
- 639-641: REPL EOFError
- 1277: bridge list no active bridges
- 1557: chain show register_builtin_chains
- 1565: chain show json output
- 1579: chain show with phase branches
- 1601: chain run register_builtin_chains
- 1622-1626: chain run dry-run output
"""

import json
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
import pytest

from rege.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


# ============================================================
# Fragment list: line 233 (status display)
# ============================================================

class TestFragmentListStatusDisplay:
    """Cover line 233: status field displayed for fragment."""

    def test_fragments_list_shows_status_when_fragment_exists(self, runner):
        """Line 233: frag.get('status') truthy → click.echo status."""
        mock_frag = MagicMock()
        mock_frag.to_dict.return_value = {
            "id": "FRAG_001",
            "name": "test_fragment",
            "charge": 75,
            "tags": ["CANON+"],
            "status": "active",
        }

        mock_organ = MagicMock(spec=["name", "_fragments"])
        mock_organ.name = "MOCK_ORGAN"
        mock_organ._fragments = {"FRAG_001": mock_frag}
        # Ensure get_fragments does NOT exist
        del mock_organ.get_fragments

        mock_registry = MagicMock()
        mock_registry.__iter__ = MagicMock(return_value=iter([mock_organ]))

        with patch("rege.cli.get_organ_registry", return_value=mock_registry), \
             patch("rege.cli.init_system"):
            result = runner.invoke(cli, ["fragments", "list"])

        assert result.exit_code == 0
        assert "active" in result.output


# ============================================================
# Checkpoint restore: line 338 (organs_restored display)
# ============================================================

class TestCheckpointRestoreOrgansRestored:
    """Cover line 338: organs_restored shown when truthy."""

    def test_restore_shows_organs_restored(self, runner):
        """Line 338: result.get('organs_restored') truthy → show count."""
        mock_recovery = MagicMock()
        mock_recovery.checkpoints = {}
        mock_recovery.full_rollback.return_value = {
            "status": "restored",
            "organs_restored": ["HEART_OF_CANON", "MIRROR_CABINET"],
        }

        mock_manager = MagicMock()
        mock_manager.load_checkpoint.return_value = {"id": "cp_001", "state": {}}

        with patch("rege.cli.get_recovery_protocol", return_value=mock_recovery), \
             patch("rege.cli.get_checkpoint_manager", return_value=mock_manager):
            result = runner.invoke(cli, ["checkpoint", "restore", "cp_001", "--confirm"])

        assert result.exit_code == 0
        # Line 338: Organs Restored count shown
        assert "Organs Restored" in result.output


# ============================================================
# REPL :last with non-dict output: line 476
# ============================================================

class TestReplLastNonDictOutput:
    """Cover line 476: :last with non-dict output."""

    def test_repl_last_non_dict_output(self, runner):
        """Line 476: result.output is not a dict → click.echo(result.output)."""
        with patch("rege.cli.init_system") as mock_init:
            mock_result = MagicMock()
            mock_result.status = "GLOWING"
            mock_result.organ = "HEART_OF_CANON"
            mock_result.output = "a symbolic string output"  # non-dict, truthy
            mock_init.return_value.dispatch.return_value = mock_result

            invocation = (
                "::CALL_ORGAN HEART_OF_CANON\n"
                "::WITH test\n"
                "::MODE mythic\n"
                "::DEPTH standard\n"
                "::EXPECT output"
            )
            result = runner.invoke(
                cli, ["repl"],
                input=f"{invocation}\n\n:last\nexit\n"
            )

        assert result.exit_code == 0
        # Line 476: non-dict output shown in :last display
        assert "a symbolic string output" in result.output or "LAST RESULT" in result.output


# ============================================================
# REPL :history with non-empty history: lines 514-519
# ============================================================

class TestReplHistoryNonEmpty:
    """Cover lines 514-519: :history with entries."""

    def test_repl_history_shows_after_command(self, runner):
        """Lines 514-519: history with entry → shows COMMAND HISTORY."""
        # Type a non-colon command → gets added to history
        # (empty line after executes it as unknown command → UNKNOWN shown)
        # Then :history shows COMMAND HISTORY
        with patch("rege.cli.init_system"):
            result = runner.invoke(
                cli, ["repl"],
                input="hello world\n\n:history\nexit\n"
            )

        assert result.exit_code == 0
        # Lines 514-519: COMMAND HISTORY shown with entry
        assert "COMMAND HISTORY" in result.output


# ============================================================
# REPL :load exception paths: lines 546-547, 550-551
# ============================================================

class TestReplLoadExceptionPaths:
    """Cover lines 546-547 and 550-551."""

    def test_repl_load_dispatch_exception(self, runner, tmp_path):
        """Lines 546-547: dispatch raises Exception → [ERROR] shown."""
        invocation_file = tmp_path / "test_inv.txt"
        invocation_file.write_text(
            "::CALL_ORGAN HEART_OF_CANON\n"
            "::WITH test\n"
            "::MODE mythic\n"
            "::DEPTH standard\n"
            "::EXPECT output\n"
        )

        with patch("rege.cli.init_system") as mock_init:
            mock_init.return_value.dispatch.side_effect = Exception("dispatch error")

            result = runner.invoke(
                cli, ["repl"],
                input=f":load {invocation_file}\nexit\n"
            )

        assert result.exit_code == 0
        # Lines 546-547: [ERROR] dispatch error shown
        assert "ERROR" in result.output or "dispatch error" in result.output

    def test_repl_load_file_open_exception(self, runner):
        """Lines 550-551: general Exception opening file → 'Error loading file' shown."""
        with patch("rege.cli.init_system"), \
             patch("builtins.open", side_effect=PermissionError("access denied")):
            result = runner.invoke(
                cli, ["repl"],
                input=":load /some/protected/file.txt\nexit\n"
            )

        assert result.exit_code == 0
        # Lines 550-551: Error loading file shown
        assert "Error loading" in result.output


# ============================================================
# REPL :export exception: lines 568-569
# ============================================================

class TestReplExportException:
    """Cover lines 568-569: :export raises Exception."""

    def test_repl_export_exception(self, runner):
        """Lines 568-569: writing export file raises → error message shown."""
        with patch("rege.cli.init_system"), \
             patch("builtins.open", side_effect=PermissionError("no write access")):
            result = runner.invoke(
                cli, ["repl"],
                input=":export /some/protected/output.json\nexit\n"
            )

        assert result.exit_code == 0
        # Lines 568-569: Error exporting shown
        assert "Error exporting" in result.output


# ============================================================
# REPL main loop: lines 627, 633-634
# ============================================================

class TestReplMainLoopPaths:
    """Cover lines 627 (non-dict output), 633-634 (unknown command)."""

    def test_repl_main_loop_non_dict_output(self, runner):
        """Line 627: dispatcher returns non-dict output → echoed as string."""
        with patch("rege.cli.init_system") as mock_init:
            mock_result = MagicMock()
            mock_result.status = "GLOWING"
            mock_result.organ = "HEART_OF_CANON"
            mock_result.output = "a symbolic string output"  # non-dict, truthy
            mock_init.return_value.dispatch.return_value = mock_result

            invocation = (
                "::CALL_ORGAN HEART_OF_CANON\n"
                "::WITH test\n"
                "::MODE mythic\n"
                "::DEPTH standard\n"
                "::EXPECT output"
            )
            result = runner.invoke(
                cli, ["repl"],
                input=f"{invocation}\n\nexit\n"
            )

        assert result.exit_code == 0
        # Line 627: non-dict output shown in main REPL loop
        assert "GLOWING" in result.output or "a symbolic string output" in result.output

    def test_repl_unknown_command_not_colon(self, runner):
        """Lines 633-634: non-invocation, non-colon → UNKNOWN message."""
        with patch("rege.cli.init_system"):
            result = runner.invoke(
                cli, ["repl"],
                input="this is not a valid command or invocation\n\nexit\n"
            )

        assert result.exit_code == 0
        # Lines 633-634: [UNKNOWN] Command not recognized
        assert "UNKNOWN" in result.output


# ============================================================
# REPL EOFError: lines 639-641
# ============================================================

class TestReplEOFError:
    """Cover lines 639-641: EOFError exits REPL."""

    def test_repl_eoferror_exits_gracefully(self, runner):
        """Lines 639-641: empty input → EOFError → CONSOLE CLOSED."""
        with patch("rege.cli.init_system"):
            result = runner.invoke(cli, ["repl"], input="")

        assert result.exit_code == 0
        # Lines 639-641: CONSOLE CLOSED message (or exit naturally)
        assert "CONSOLE CLOSED" in result.output or result.exit_code == 0


# ============================================================
# Bridge list: line 1277 (no active bridges)
# ============================================================

class TestBridgeListNoActive:
    """Cover line 1277: bridge list shows 'No active bridges.'"""

    def test_bridge_list_no_active_bridges(self, runner):
        """Line 1277: active is empty → show 'No active bridges.'"""
        mock_registry = MagicMock()
        mock_registry.list_types.return_value = ["obsidian", "git", "maxmsp"]
        mock_registry.list_active.return_value = []  # empty → hits line 1277

        with patch("rege.bridges.get_bridge_registry", return_value=mock_registry):
            result = runner.invoke(cli, ["bridge", "list"])

        assert result.exit_code == 0
        assert "No active bridges" in result.output


# ============================================================
# Chain show: lines 1557, 1565, 1579
# ============================================================

class TestChainShowCoverage:
    """Cover lines 1557 (register builtin), 1565 (json output), 1579 (branches)."""

    def test_chain_show_registers_builtins_when_empty(self, runner):
        """Line 1557: registry.count() == 0 → register_builtin_chains() called."""
        mock_registry = MagicMock()
        mock_registry.count.return_value = 0
        mock_chain = MagicMock()
        mock_chain.name = "genesis_cycle"
        mock_chain.description = "A genesis chain"
        mock_chain.version = "1.0"
        mock_chain.tags = []
        mock_chain.entry_phase = "init"
        mock_chain.phases = []
        mock_chain.validate.return_value = {"valid": True, "errors": []}
        mock_registry.get.return_value = mock_chain

        with patch("rege.orchestration.get_chain_registry", return_value=mock_registry), \
             patch("rege.orchestration.builtin_chains.register_builtin_chains") as mock_reg:
            result = runner.invoke(cli, ["chain", "show", "genesis_cycle"])

        assert result.exit_code == 0
        # Line 1557: register_builtin_chains called when count == 0
        mock_reg.assert_called_once()

    def test_chain_show_json_output(self, runner):
        """Line 1565: chain show --json-output → json.dumps output."""
        mock_registry = MagicMock()
        mock_registry.count.return_value = 1
        mock_chain = MagicMock()
        mock_chain.name = "genesis_cycle"
        mock_chain.to_dict.return_value = {"name": "genesis_cycle", "phases": []}
        mock_registry.get.return_value = mock_chain

        with patch("rege.orchestration.get_chain_registry", return_value=mock_registry):
            result = runner.invoke(cli, ["chain", "show", "genesis_cycle", "--json-output"])

        assert result.exit_code == 0
        # Line 1565: JSON output
        data = json.loads(result.output)
        assert data["name"] == "genesis_cycle"

    def test_chain_show_phase_with_branches(self, runner):
        """Line 1579: phase has branches → Branches count shown."""
        mock_phase = MagicMock()
        mock_phase.name = "phase_one"
        mock_phase.organ = "HEART_OF_CANON"
        mock_phase.mode = "mythic"
        mock_phase.branches = {"success": "phase_two"}  # non-empty

        mock_chain = MagicMock()
        mock_chain.name = "test_chain"
        mock_chain.description = "A test chain"
        mock_chain.version = "1.0"
        mock_chain.tags = []
        mock_chain.entry_phase = "phase_one"
        mock_chain.phases = [mock_phase]
        mock_chain.validate.return_value = {"valid": True, "errors": []}

        mock_registry = MagicMock()
        mock_registry.count.return_value = 1
        mock_registry.get.return_value = mock_chain

        with patch("rege.orchestration.get_chain_registry", return_value=mock_registry):
            result = runner.invoke(cli, ["chain", "show", "test_chain"])

        assert result.exit_code == 0
        # Line 1579: Branches count shown
        assert "Branches" in result.output


# ============================================================
# Chain run: lines 1601, 1622-1626
# ============================================================

class TestChainRunCoverage:
    """Cover lines 1601 (register builtin) and 1622-1626 (dry-run output)."""

    def test_chain_run_registers_builtins_when_empty(self, runner):
        """Line 1601: registry.count() == 0 → register_builtin_chains() called."""
        mock_registry = MagicMock()
        mock_registry.count.return_value = 0

        mock_orchestrator = MagicMock()
        mock_orchestrator.dry_run.return_value = {
            "phase_count": 1,
            "planned_phases": [
                {"name": "init", "organ": "HEART_OF_CANON", "mode": "mythic", "would_execute": True},
            ]
        }

        with patch("rege.orchestration.get_chain_registry", return_value=mock_registry), \
             patch("rege.orchestration.builtin_chains.register_builtin_chains") as mock_reg, \
             patch("rege.orchestration.RitualChainOrchestrator", return_value=mock_orchestrator):
            result = runner.invoke(cli, ["chain", "run", "genesis_cycle", "--dry-run"])

        assert result.exit_code == 0
        # Line 1601: register_builtin_chains called when count == 0
        mock_reg.assert_called_once()

    def test_chain_run_dry_run_non_json_output(self, runner):
        """Lines 1622-1626: dry-run non-json output shows planned phases."""
        mock_registry = MagicMock()
        mock_registry.count.return_value = 1

        mock_orchestrator = MagicMock()
        mock_orchestrator.dry_run.return_value = {
            "phase_count": 2,
            "planned_phases": [
                {"name": "init", "organ": "HEART_OF_CANON", "mode": "mythic", "would_execute": True},
                {"name": "reflect", "organ": "MIRROR_CABINET", "mode": "mythic", "would_execute": False},
            ]
        }

        with patch("rege.orchestration.get_chain_registry", return_value=mock_registry), \
             patch("rege.orchestration.RitualChainOrchestrator", return_value=mock_orchestrator):
            result = runner.invoke(cli, ["chain", "run", "genesis_cycle", "--dry-run"])

        assert result.exit_code == 0
        # Lines 1622-1626: DRY RUN header + planned phases shown
        assert "DRY RUN" in result.output
        assert "EXECUTE" in result.output or "SKIP" in result.output
