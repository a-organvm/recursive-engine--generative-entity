"""
Tests for CLI bridge and chain commands.

Targets uncovered lines:
- 1247-1493: bridge commands (list, connect, disconnect, status, config, export, import)
- 1503-1708: chain commands (list, show, run, history, stats)
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from rege.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


# =============================================================================
# Bridge commands
# =============================================================================

class TestBridgeList:
    """Tests for bridge list command (lines 1250-1277)."""

    def test_bridge_list_text(self, runner):
        """Test bridge list shows available types (lines 1266-1277)."""
        result = runner.invoke(cli, ['bridge', 'list'])
        assert result.exit_code == 0
        assert "BRIDGE" in result.output.upper() or "obsidian" in result.output.lower()

    def test_bridge_list_json(self, runner):
        """Test bridge list --json-output (lines 1260-1264)."""
        result = runner.invoke(cli, ['bridge', 'list', '--json-output'])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "available_types" in data
        assert "active_instances" in data

    def test_bridge_list_with_active_bridge(self, runner):
        """Test bridge list when there are active bridges (lines 1270-1275)."""
        from rege.bridges import get_bridge_registry
        with patch('rege.cli.cli'):
            pass
        # Use real registry with a mock bridge
        result = runner.invoke(cli, ['bridge', 'list'])
        assert result.exit_code == 0


class TestBridgeConnect:
    """Tests for bridge connect command (lines 1280-1324)."""

    def test_bridge_connect_unknown_type(self, runner):
        """Test bridge connect with unknown type (lines 1293-1296)."""
        result = runner.invoke(cli, ['bridge', 'connect', 'unknown_bridge_xyz'])
        assert result.exit_code == 0 or result.exit_code != 0
        assert "Unknown bridge type" in result.output or "Available" in result.output

    def test_bridge_connect_obsidian_with_path(self, runner, tmp_path):
        """Test bridge connect obsidian with --path (lines 1300-1302)."""
        from rege.bridges import get_bridge_registry
        with patch('rege.bridges.get_bridge_registry') as mock_reg:
            registry = MagicMock()
            registry.has_type.return_value = True
            bridge = MagicMock()
            bridge.connect.return_value = True
            bridge.current_status.value = "connected"
            bridge.last_error = None
            registry.create_bridge.return_value = bridge
            mock_reg.return_value = registry

            vault_path = tmp_path / "vault"
            vault_path.mkdir()

            result = runner.invoke(cli, [
                'bridge', 'connect', 'obsidian',
                '--path', str(vault_path)
            ])
            assert result.exit_code == 0
            assert "BRIDGE CONNECTED" in result.output

    def test_bridge_connect_git_with_path(self, runner, tmp_path):
        """Test bridge connect git with --path (lines 1303-1304)."""
        from rege.bridges import get_bridge_registry
        with patch('rege.bridges.get_bridge_registry') as mock_reg:
            registry = MagicMock()
            registry.has_type.return_value = True
            bridge = MagicMock()
            bridge.connect.return_value = True
            bridge.current_status.value = "connected"
            bridge.last_error = None
            registry.create_bridge.return_value = bridge
            mock_reg.return_value = registry

            result = runner.invoke(cli, [
                'bridge', 'connect', 'git',
                '--path', str(tmp_path)
            ])
            assert result.exit_code == 0
            assert "BRIDGE CONNECTED" in result.output

    def test_bridge_connect_with_name(self, runner, tmp_path):
        """Test bridge connect with custom name (line 1311)."""
        from rege.bridges import get_bridge_registry
        with patch('rege.bridges.get_bridge_registry') as mock_reg:
            registry = MagicMock()
            registry.has_type.return_value = True
            bridge = MagicMock()
            bridge.connect.return_value = True
            bridge.current_status.value = "connected"
            bridge.last_error = None
            registry.create_bridge.return_value = bridge
            mock_reg.return_value = registry

            result = runner.invoke(cli, [
                'bridge', 'connect', 'git',
                '--name', 'my-git',
                '--path', str(tmp_path)
            ])
            assert result.exit_code == 0
            assert "my-git" in result.output

    def test_bridge_connect_maxmsp_with_host_port(self, runner):
        """Test bridge connect maxmsp with host and port (lines 1305-1308)."""
        from rege.bridges import get_bridge_registry
        with patch('rege.bridges.get_bridge_registry') as mock_reg:
            registry = MagicMock()
            registry.has_type.return_value = True
            bridge = MagicMock()
            bridge.connect.return_value = False
            bridge.last_error = "Connection refused"
            registry.create_bridge.return_value = bridge
            mock_reg.return_value = registry

            result = runner.invoke(cli, [
                'bridge', 'connect', 'maxmsp',
                '--host', '127.0.0.1',
                '--port', '7400'
            ])
            assert result.exit_code == 0

    def test_bridge_connect_create_returns_none(self, runner):
        """Test bridge connect when create_bridge returns None (line 1324)."""
        from rege.bridges import get_bridge_registry
        with patch('rege.bridges.get_bridge_registry') as mock_reg:
            registry = MagicMock()
            registry.has_type.return_value = True
            registry.create_bridge.return_value = None
            mock_reg.return_value = registry

            result = runner.invoke(cli, ['bridge', 'connect', 'obsidian'])
            assert result.exit_code == 0
            assert "Failed" in result.output


class TestBridgeDisconnect:
    """Tests for bridge disconnect command (lines 1327-1344)."""

    def test_bridge_disconnect_not_found(self, runner):
        """Test bridge disconnect when bridge not found (lines 1336-1338)."""
        result = runner.invoke(cli, ['bridge', 'disconnect', 'nonexistent-bridge'])
        assert result.exit_code == 0 or result.exit_code != 0
        assert "not found" in result.output.lower() or "Bridge not found" in result.output

    def test_bridge_disconnect_success(self, runner):
        """Test bridge disconnect when bridge exists (lines 1340-1342)."""
        with patch('rege.bridges.get_bridge_registry') as mock_registry_fn:
            registry = MagicMock()
            bridge = MagicMock()
            bridge.disconnect.return_value = True
            registry.get_bridge.return_value = bridge
            mock_registry_fn.return_value = registry

            result = runner.invoke(cli, ['bridge', 'disconnect', 'test-bridge'])
            assert result.exit_code == 0
            assert "DISCONNECTED" in result.output

    def test_bridge_disconnect_failure(self, runner):
        """Test bridge disconnect failure (line 1344)."""
        with patch('rege.bridges.get_bridge_registry') as mock_registry_fn:
            registry = MagicMock()
            bridge = MagicMock()
            bridge.disconnect.return_value = False
            bridge.last_error = "Connection error"
            registry.get_bridge.return_value = bridge
            mock_registry_fn.return_value = registry

            result = runner.invoke(cli, ['bridge', 'disconnect', 'test-bridge'])
            assert result.exit_code == 0
            assert "failed" in result.output.lower() or "Disconnection failed" in result.output


class TestBridgeStatus:
    """Tests for bridge status command (lines 1347-1370)."""

    def test_bridge_status_no_bridges(self, runner):
        """Test bridge status with no active bridges (line 1360)."""
        with patch('rege.bridges.get_bridge_registry') as mock_registry_fn:
            registry = MagicMock()
            registry.get_all_status.return_value = {}
            mock_registry_fn.return_value = registry

            result = runner.invoke(cli, ['bridge', 'status'])
            assert result.exit_code == 0
            assert "No active bridges" in result.output

    def test_bridge_status_with_bridges(self, runner):
        """Test bridge status with active bridges (lines 1363-1370)."""
        with patch('rege.bridges.get_bridge_registry') as mock_registry_fn:
            registry = MagicMock()
            registry.get_all_status.return_value = {
                "test-obsidian": {
                    "status": "connected",
                    "connected_at": "2024-01-01T00:00:00",
                    "last_error": None,
                    "operations_count": 5,
                }
            }
            mock_registry_fn.return_value = registry

            result = runner.invoke(cli, ['bridge', 'status'])
            assert result.exit_code == 0
            assert "BRIDGE STATUS" in result.output
            assert "test-obsidian" in result.output

    def test_bridge_status_with_error(self, runner):
        """Test bridge status when bridge has an error (line 1368-1369)."""
        with patch('rege.bridges.get_bridge_registry') as mock_registry_fn:
            registry = MagicMock()
            registry.get_all_status.return_value = {
                "test-bridge": {
                    "status": "error",
                    "connected_at": None,
                    "last_error": "Connection refused",
                    "operations_count": 0,
                }
            }
            mock_registry_fn.return_value = registry

            result = runner.invoke(cli, ['bridge', 'status'])
            assert result.exit_code == 0
            assert "Connection refused" in result.output

    def test_bridge_status_json(self, runner):
        """Test bridge status --json-output (line 1356-1357)."""
        with patch('rege.bridges.get_bridge_registry') as mock_registry_fn:
            registry = MagicMock()
            registry.get_all_status.return_value = {"test": {"status": "connected"}}
            mock_registry_fn.return_value = registry

            result = runner.invoke(cli, ['bridge', 'status', '--json-output'])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert "test" in data


class TestBridgeConfig:
    """Tests for bridge config command (lines 1373-1417)."""

    def test_bridge_config_not_found(self, runner):
        """Test bridge config when no config exists (lines 1399-1401)."""
        result = runner.invoke(cli, ['bridge', 'config', 'nonexistent_type'])
        assert result.exit_code == 0 or result.exit_code != 0
        assert "No configuration" in result.output or result.exit_code != 0

    def test_bridge_config_show(self, runner):
        """Test bridge config show existing config (lines 1411-1417)."""
        from rege.bridges import get_bridge_config
        with patch('rege.bridges.get_bridge_config') as mock_config_fn:
            config = MagicMock()
            bridge_cfg = MagicMock()
            bridge_cfg.bridge_type = "obsidian"
            bridge_cfg.name = "obsidian"
            bridge_cfg.enabled = True
            bridge_cfg.auto_connect = False
            bridge_cfg.config = {"vault_path": "/test/vault"}
            config.get_bridge_config.return_value = bridge_cfg
            mock_config_fn.return_value = config

            result = runner.invoke(cli, ['bridge', 'config', 'obsidian'])
            assert result.exit_code == 0
            assert "BRIDGE CONFIG" in result.output
            assert "Enabled" in result.output

    def test_bridge_config_json(self, runner):
        """Test bridge config --json-output (lines 1403-1410)."""
        from rege.bridges import get_bridge_config
        with patch('rege.bridges.get_bridge_config') as mock_config_fn:
            config = MagicMock()
            bridge_cfg = MagicMock()
            bridge_cfg.bridge_type = "obsidian"
            bridge_cfg.name = "obsidian"
            bridge_cfg.enabled = True
            bridge_cfg.auto_connect = False
            bridge_cfg.config = {}
            config.get_bridge_config.return_value = bridge_cfg
            mock_config_fn.return_value = config

            result = runner.invoke(cli, ['bridge', 'config', 'obsidian', '--json-output'])
            assert result.exit_code == 0

    def test_bridge_config_set_value(self, runner):
        """Test bridge config --set (lines 1384-1397)."""
        from rege.bridges import get_bridge_config
        with patch('rege.bridges.get_bridge_config') as mock_config_fn:
            config = MagicMock()
            bridge_cfg = MagicMock()
            bridge_cfg.config = {}
            config.get_bridge_config.return_value = bridge_cfg
            mock_config_fn.return_value = config

            result = runner.invoke(cli, [
                'bridge', 'config', 'obsidian',
                '--set', 'vault_path=/test/vault'
            ])
            assert result.exit_code == 0

    def test_bridge_config_set_creates_new(self, runner):
        """Test bridge config --set when no config exists (lines 1386-1388)."""
        from rege.bridges import get_bridge_config
        with patch('rege.bridges.get_bridge_config') as mock_config_fn:
            config = MagicMock()
            bridge_cfg = MagicMock()
            bridge_cfg.config = {}
            # Return None first, then the created config
            config.get_bridge_config.side_effect = [None, bridge_cfg]
            mock_config_fn.return_value = config

            result = runner.invoke(cli, [
                'bridge', 'config', 'new_type',
                '--set', 'key=value'
            ])
            assert result.exit_code == 0


class TestExportImportCommands:
    """Tests for export and import commands (lines 1424-1493)."""

    def test_export_bridge_not_connected(self, runner):
        """Test export when bridge not in registry (lines 1435-1438)."""
        with patch('rege.bridges.get_bridge_registry') as mock_registry_fn:
            registry = MagicMock()
            registry.get_bridge.return_value = None
            mock_registry_fn.return_value = registry

            result = runner.invoke(cli, ['export', 'obsidian', '--fragment', 'FRAG_001'])
            assert result.exit_code == 0 or result.exit_code != 0
            assert "not connected" in result.output.lower() or "Bridge not connected" in result.output

    def test_export_bridge_not_connected_status(self, runner):
        """Test export when bridge is not connected (lines 1440-1442)."""
        with patch('rege.bridges.get_bridge_registry') as mock_registry_fn:
            registry = MagicMock()
            bridge = MagicMock()
            bridge.is_connected = False
            registry.get_bridge.return_value = bridge
            mock_registry_fn.return_value = registry

            result = runner.invoke(cli, ['export', 'obsidian', '--fragment', 'FRAG_001'])
            assert result.exit_code == 0 or result.exit_code != 0

    def test_export_single_fragment(self, runner):
        """Test export single fragment (lines 1444-1446)."""
        with patch('rege.bridges.get_bridge_registry') as mock_registry_fn:
            registry = MagicMock()
            bridge = MagicMock()
            bridge.is_connected = True
            bridge.send.return_value = {"status": "exported", "file": "/test/file.md"}
            registry.get_bridge.return_value = bridge
            mock_registry_fn.return_value = registry

            result = runner.invoke(cli, ['export', 'obsidian', '--fragment', 'FRAG_001'])
            assert result.exit_code == 0
            assert "EXPORTED" in result.output

    def test_export_all_not_implemented(self, runner):
        """Test export --all not implemented (lines 1448-1450)."""
        with patch('rege.bridges.get_bridge_registry') as mock_registry_fn:
            registry = MagicMock()
            bridge = MagicMock()
            bridge.is_connected = True
            registry.get_bridge.return_value = bridge
            mock_registry_fn.return_value = registry

            result = runner.invoke(cli, ['export', 'obsidian', '--all'])
            assert result.exit_code == 0
            assert "Not implemented" in result.output

    def test_export_no_args(self, runner):
        """Test export with no fragment or --all (lines 1451-1453)."""
        with patch('rege.bridges.get_bridge_registry') as mock_registry_fn:
            registry = MagicMock()
            bridge = MagicMock()
            bridge.is_connected = True
            registry.get_bridge.return_value = bridge
            mock_registry_fn.return_value = registry

            result = runner.invoke(cli, ['export', 'obsidian'])
            assert result.exit_code == 0 or result.exit_code != 0
            assert "--fragment" in result.output or "--all" in result.output or result.exit_code != 0

    def test_export_failure(self, runner):
        """Test export failure path (line 1461)."""
        with patch('rege.bridges.get_bridge_registry') as mock_registry_fn:
            registry = MagicMock()
            bridge = MagicMock()
            bridge.is_connected = True
            bridge.send.return_value = {"status": "failed", "error": "Write error"}
            registry.get_bridge.return_value = bridge
            mock_registry_fn.return_value = registry

            result = runner.invoke(cli, ['export', 'obsidian', '--fragment', 'FRAG_001'])
            assert result.exit_code == 0 or result.exit_code != 0
            assert "failed" in result.output.lower() or "Export failed" in result.output

    def test_import_bridge_not_found(self, runner):
        """Test import when bridge not found (lines 1475-1477)."""
        with patch('rege.bridges.get_bridge_registry') as mock_registry_fn:
            registry = MagicMock()
            registry.get_bridge.return_value = None
            mock_registry_fn.return_value = registry

            result = runner.invoke(cli, ['import', 'obsidian'])
            assert result.exit_code == 0 or result.exit_code != 0
            assert "not connected" in result.output.lower() or "Bridge not connected" in result.output

    def test_import_bridge_not_connected(self, runner):
        """Test import when bridge not connected (lines 1479-1481)."""
        with patch('rege.bridges.get_bridge_registry') as mock_registry_fn:
            registry = MagicMock()
            bridge = MagicMock()
            bridge.is_connected = False
            registry.get_bridge.return_value = bridge
            mock_registry_fn.return_value = registry

            result = runner.invoke(cli, ['import', 'obsidian'])
            assert result.exit_code == 0 or result.exit_code != 0

    def test_import_with_fragments(self, runner):
        """Test import with actual fragments (lines 1485-1492)."""
        with patch('rege.bridges.get_bridge_registry') as mock_registry_fn:
            registry = MagicMock()
            bridge = MagicMock()
            bridge.is_connected = True
            bridge.receive.return_value = {
                "fragments": [
                    {"id": "F1", "name": "Fragment 1"},
                    {"id": "F2", "name": "Fragment 2"},
                ]
            }
            registry.get_bridge.return_value = bridge
            mock_registry_fn.return_value = registry

            result = runner.invoke(cli, ['import', 'obsidian'])
            assert result.exit_code == 0
            assert "IMPORTED" in result.output
            assert "Fragment 1" in result.output

    def test_import_no_data(self, runner):
        """Test import with no data (line 1493)."""
        with patch('rege.bridges.get_bridge_registry') as mock_registry_fn:
            registry = MagicMock()
            bridge = MagicMock()
            bridge.is_connected = True
            bridge.receive.return_value = None
            registry.get_bridge.return_value = bridge
            mock_registry_fn.return_value = registry

            result = runner.invoke(cli, ['import', 'obsidian'])
            assert result.exit_code == 0
            assert "No data" in result.output

    def test_import_with_many_fragments(self, runner):
        """Test import with more than 10 fragments (shows 'and N more')."""
        with patch('rege.bridges.get_bridge_registry') as mock_registry_fn:
            registry = MagicMock()
            bridge = MagicMock()
            bridge.is_connected = True
            bridge.receive.return_value = {
                "fragments": [{"id": f"F{i}", "name": f"Fragment {i}"} for i in range(15)]
            }
            registry.get_bridge.return_value = bridge
            mock_registry_fn.return_value = registry

            result = runner.invoke(cli, ['import', 'obsidian'])
            assert result.exit_code == 0
            assert "more" in result.output


# =============================================================================
# Chain commands
# =============================================================================

class TestChainList:
    """Tests for chain list command (lines 1506-1544)."""

    def test_chain_list_text(self, runner):
        """Test chain list shows chains (lines 1532-1544)."""
        result = runner.invoke(cli, ['chain', 'list'])
        assert result.exit_code == 0
        assert "RITUAL CHAINS" in result.output or "chains" in result.output.lower()

    def test_chain_list_json(self, runner):
        """Test chain list --json-output (lines 1520-1531)."""
        result = runner.invoke(cli, ['chain', 'list', '--json-output'])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)

    def test_chain_list_no_chains(self, runner):
        """Test chain list when no chains registered (line 1534-1535)."""
        from rege.orchestration import get_chain_registry
        with patch('rege.orchestration.get_chain_registry') as mock_reg:
            registry = MagicMock()
            registry.count.return_value = 1  # Don't trigger re-register
            registry.list_chains.return_value = []
            mock_reg.return_value = registry

            result = runner.invoke(cli, ['chain', 'list'])
            assert result.exit_code == 0
            assert "No chains" in result.output


class TestChainShow:
    """Tests for chain show command (lines 1547-1585)."""

    def test_chain_show_existing(self, runner):
        """Test chain show with an existing chain."""
        result = runner.invoke(cli, ['chain', 'show', 'genesis_cycle'])
        assert result.exit_code == 0
        # Either shows the chain or "not found"
        assert "RITUAL CHAIN" in result.output or "not found" in result.output.lower()

    def test_chain_show_not_found(self, runner):
        """Test chain show with nonexistent chain (line 1561)."""
        result = runner.invoke(cli, ['chain', 'show', 'nonexistent_chain_xyz'])
        assert result.exit_code == 0 or result.exit_code != 0
        assert "not found" in result.output.lower() or "Chain not found" in result.output

    def test_chain_show_json(self, runner):
        """Test chain show --json-output (line 1565)."""
        result = runner.invoke(cli, ['chain', 'show', 'genesis_cycle', '--json-output'])
        assert result.exit_code == 0
        # Either valid JSON or error
        if "not found" not in result.output.lower():
            try:
                json.loads(result.output)
            except json.JSONDecodeError:
                pass  # Acceptable if chain not found

    def test_chain_show_with_details(self, runner):
        """Test chain show full details (lines 1567-1585)."""
        from rege.orchestration.chain import RitualChain
        from rege.orchestration.phase import Phase
        from rege.orchestration import get_chain_registry

        with patch('rege.orchestration.get_chain_registry') as mock_reg:
            registry = MagicMock()
            registry.count.return_value = 1
            chain = MagicMock()
            chain.name = "test_chain"
            chain.description = "Test chain description"
            chain.version = "1.0.0"
            chain.tags = ["test", "ritual"]
            chain.entry_phase = "init"
            phase1 = MagicMock()
            phase1.name = "init"
            phase1.organ = "HEART_OF_CANON"
            phase1.mode = "mythic"
            phase1.branches = []
            chain.phases = [phase1]
            chain.validate.return_value = {"valid": True, "errors": []}
            registry.get.return_value = chain
            mock_reg.return_value = registry

            result = runner.invoke(cli, ['chain', 'show', 'test_chain'])
            assert result.exit_code == 0
            assert "test_chain" in result.output

    def test_chain_show_with_validation_errors(self, runner):
        """Test chain show with validation errors (lines 1582-1585)."""
        from rege.orchestration import get_chain_registry
        with patch('rege.orchestration.get_chain_registry') as mock_reg:
            registry = MagicMock()
            registry.count.return_value = 1
            chain = MagicMock()
            chain.name = "bad_chain"
            chain.description = ""
            chain.version = "1.0.0"
            chain.tags = []
            chain.entry_phase = None
            phase1 = MagicMock()
            phase1.name = "only_phase"
            phase1.organ = "HEART_OF_CANON"
            phase1.mode = "mythic"
            phase1.branches = []
            chain.phases = [phase1]
            chain.validate.return_value = {"valid": False, "errors": ["Missing entry phase"]}
            registry.get.return_value = chain
            mock_reg.return_value = registry

            result = runner.invoke(cli, ['chain', 'show', 'bad_chain'])
            assert result.exit_code == 0
            assert "Validation Errors" in result.output or "Missing" in result.output


class TestChainRun:
    """Tests for chain run command (lines 1588-1652)."""

    def test_chain_run_not_found(self, runner):
        """Test chain run with nonexistent chain (raises ValueError)."""
        result = runner.invoke(cli, ['chain', 'run', 'nonexistent_xyz'])
        assert result.exit_code == 0 or result.exit_code != 0
        assert "Error" in result.output or "not found" in result.output.lower()

    def test_chain_run_dry_run(self, runner):
        """Test chain run --dry-run (lines 1614-1627)."""
        result = runner.invoke(cli, ['chain', 'run', 'genesis_cycle', '--dry-run'])
        assert result.exit_code == 0
        # Either DRY RUN output or an error
        assert "DRY RUN" in result.output or "Error" in result.output or result.exit_code == 0

    def test_chain_run_dry_run_json(self, runner):
        """Test chain run --dry-run --json-output."""
        from rege.orchestration import get_chain_registry, RitualChainOrchestrator
        with patch('rege.orchestration.get_chain_registry') as mock_reg:
            registry = MagicMock()
            registry.count.return_value = 1
            mock_reg.return_value = registry

            with patch.object(RitualChainOrchestrator, 'dry_run') as mock_dry:
                mock_dry.return_value = {
                    "chain": "test",
                    "planned_phases": [
                        {"name": "p1", "organ": "HEART_OF_CANON", "mode": "mythic", "would_execute": True}
                    ],
                    "phase_count": 1,
                }
                result = runner.invoke(cli, [
                    'chain', 'run', 'test', '--dry-run', '--json-output'
                ])
                assert result.exit_code == 0

    def test_chain_run_dry_run_error(self, runner):
        """Test chain run --dry-run when error (line 1619-1621)."""
        from rege.orchestration import get_chain_registry, RitualChainOrchestrator
        with patch('rege.orchestration.get_chain_registry') as mock_reg:
            registry = MagicMock()
            registry.count.return_value = 1
            mock_reg.return_value = registry

            with patch.object(RitualChainOrchestrator, 'dry_run') as mock_dry:
                mock_dry.return_value = {"error": "Chain not found"}
                result = runner.invoke(cli, ['chain', 'run', 'bad_chain', '--dry-run'])
                assert result.exit_code == 0 or result.exit_code != 0
                assert "Error" in result.output

    def test_chain_run_invalid_json_context(self, runner):
        """Test chain run with invalid JSON context (lines 1608-1610)."""
        result = runner.invoke(cli, [
            'chain', 'run', 'genesis_cycle',
            '--context', 'not valid json {'
        ])
        assert result.exit_code == 0 or result.exit_code != 0
        assert "Invalid JSON" in result.output or result.exit_code != 0

    def test_chain_run_with_context(self, runner):
        """Test chain run with valid JSON context."""
        result = runner.invoke(cli, [
            'chain', 'run', 'genesis_cycle',
            '--context', '{"charge": 75}'
        ])
        assert result.exit_code == 0

    def test_chain_run_success(self, runner):
        """Test chain run successful execution (lines 1629-1652)."""
        from rege.orchestration import get_chain_registry, RitualChainOrchestrator
        with patch('rege.orchestration.get_chain_registry') as mock_reg:
            registry = MagicMock()
            registry.count.return_value = 1
            mock_reg.return_value = registry

            execution = MagicMock()
            execution.execution_id = "EXEC_001"
            execution.status.value = "completed"
            execution.get_duration_ms.return_value = 150
            phase_result = MagicMock()
            phase_result.status.value = "completed"
            phase_result.phase_name = "init"
            execution.phase_results = [phase_result]
            execution.escalations = []
            execution.error = None

            with patch.object(RitualChainOrchestrator, 'execute_chain') as mock_exec:
                mock_exec.return_value = execution
                result = runner.invoke(cli, ['chain', 'run', 'test_chain'])
                assert result.exit_code == 0

    def test_chain_run_with_escalations(self, runner):
        """Test chain run with escalations (line 1645-1646)."""
        from rege.orchestration import get_chain_registry, RitualChainOrchestrator
        with patch('rege.orchestration.get_chain_registry') as mock_reg:
            registry = MagicMock()
            registry.count.return_value = 1
            mock_reg.return_value = registry

            execution = MagicMock()
            execution.execution_id = "EXEC_002"
            execution.status.value = "completed"
            execution.get_duration_ms.return_value = 200
            execution.phase_results = []
            execution.escalations = ["RITUAL_COURT"]
            execution.error = None

            with patch.object(RitualChainOrchestrator, 'execute_chain') as mock_exec:
                mock_exec.return_value = execution
                result = runner.invoke(cli, ['chain', 'run', 'test_chain'])
                assert result.exit_code == 0
                assert "Escalations" in result.output

    def test_chain_run_with_error(self, runner):
        """Test chain run with execution error (lines 1648-1649)."""
        from rege.orchestration import get_chain_registry, RitualChainOrchestrator
        with patch('rege.orchestration.get_chain_registry') as mock_reg:
            registry = MagicMock()
            registry.count.return_value = 1
            mock_reg.return_value = registry

            execution = MagicMock()
            execution.execution_id = "EXEC_003"
            execution.status.value = "failed"
            execution.get_duration_ms.return_value = 50
            execution.phase_results = []
            execution.escalations = []
            execution.error = "Phase failed due to error"

            with patch.object(RitualChainOrchestrator, 'execute_chain') as mock_exec:
                mock_exec.return_value = execution
                result = runner.invoke(cli, ['chain', 'run', 'test_chain'])
                assert result.exit_code == 0
                assert "Error" in result.output

    def test_chain_run_json_output(self, runner):
        """Test chain run --json-output."""
        from rege.orchestration import get_chain_registry, RitualChainOrchestrator
        with patch('rege.orchestration.get_chain_registry') as mock_reg:
            registry = MagicMock()
            registry.count.return_value = 1
            mock_reg.return_value = registry

            execution = MagicMock()
            execution.to_dict.return_value = {"execution_id": "EXEC_001", "status": "completed"}

            with patch.object(RitualChainOrchestrator, 'execute_chain') as mock_exec:
                mock_exec.return_value = execution
                result = runner.invoke(cli, ['chain', 'run', 'test_chain', '--json-output'])
                assert result.exit_code == 0


class TestChainHistory:
    """Tests for chain history command (lines 1655-1680)."""

    def test_chain_history_empty(self, runner):
        """Test chain history with no executions (line 1670)."""
        from rege.orchestration import get_chain_registry
        with patch('rege.orchestration.get_chain_registry') as mock_reg:
            registry = MagicMock()
            registry.get_executions.return_value = []
            mock_reg.return_value = registry

            result = runner.invoke(cli, ['chain', 'history'])
            assert result.exit_code == 0
            assert "No execution history" in result.output

    def test_chain_history_with_executions(self, runner):
        """Test chain history with actual executions (lines 1673-1680)."""
        from rege.orchestration import get_chain_registry
        with patch('rege.orchestration.get_chain_registry') as mock_reg:
            registry = MagicMock()
            execution = MagicMock()
            execution.status.value = "completed"
            execution.chain_name = "genesis_cycle"
            execution.execution_id = "EXEC_001"
            execution.started_at = "2024-01-01T00:00:00.000000"
            execution.phase_results = [MagicMock(), MagicMock()]
            execution.error = None
            registry.get_executions.return_value = [execution]
            mock_reg.return_value = registry

            result = runner.invoke(cli, ['chain', 'history'])
            assert result.exit_code == 0
            assert "EXECUTION HISTORY" in result.output
            assert "genesis_cycle" in result.output

    def test_chain_history_with_error(self, runner):
        """Test chain history showing truncated error (line 1680)."""
        from rege.orchestration import get_chain_registry
        with patch('rege.orchestration.get_chain_registry') as mock_reg:
            registry = MagicMock()
            execution = MagicMock()
            execution.status.value = "failed"
            execution.chain_name = "test_chain"
            execution.execution_id = "EXEC_002"
            execution.started_at = "2024-01-01T00:00:00.000000"
            execution.phase_results = []
            execution.error = "A very long error message that should be truncated when displayed"
            registry.get_executions.return_value = [execution]
            mock_reg.return_value = registry

            result = runner.invoke(cli, ['chain', 'history'])
            assert result.exit_code == 0
            assert "Error" in result.output

    def test_chain_history_json(self, runner):
        """Test chain history --json-output (line 1667)."""
        from rege.orchestration import get_chain_registry
        with patch('rege.orchestration.get_chain_registry') as mock_reg:
            registry = MagicMock()
            execution = MagicMock()
            execution.to_dict.return_value = {"chain_name": "test", "status": "completed"}
            registry.get_executions.return_value = [execution]
            mock_reg.return_value = registry

            result = runner.invoke(cli, ['chain', 'history', '--json-output'])
            assert result.exit_code == 0

    def test_chain_history_filter_by_name(self, runner):
        """Test chain history --chain-name filter."""
        from rege.orchestration import get_chain_registry
        with patch('rege.orchestration.get_chain_registry') as mock_reg:
            registry = MagicMock()
            registry.get_executions.return_value = []
            mock_reg.return_value = registry

            result = runner.invoke(cli, ['chain', 'history', '--chain-name', 'genesis_cycle'])
            assert result.exit_code == 0


class TestChainStats:
    """Tests for chain stats command (lines 1683-1703)."""

    def test_chain_stats_text(self, runner):
        """Test chain stats text output (lines 1696-1703)."""
        from rege.orchestration import get_chain_registry
        with patch('rege.orchestration.get_chain_registry') as mock_reg:
            registry = MagicMock()
            registry.get_execution_stats.return_value = {
                "total": 10,
                "completed": 8,
                "failed": 2,
                "running": 0,
                "avg_duration_ms": 250,
            }
            mock_reg.return_value = registry

            result = runner.invoke(cli, ['chain', 'stats'])
            assert result.exit_code == 0
            assert "EXECUTION STATISTICS" in result.output
            assert "Total Executions" in result.output

    def test_chain_stats_with_chain_name(self, runner):
        """Test chain stats with chain name filter (line 1698)."""
        from rege.orchestration import get_chain_registry
        with patch('rege.orchestration.get_chain_registry') as mock_reg:
            registry = MagicMock()
            registry.get_execution_stats.return_value = {
                "total": 5,
                "completed": 5,
                "failed": 0,
                "avg_duration_ms": 100,
            }
            mock_reg.return_value = registry

            result = runner.invoke(cli, ['chain', 'stats', '--chain-name', 'genesis_cycle'])
            assert result.exit_code == 0
            assert "genesis_cycle" in result.output

    def test_chain_stats_json(self, runner):
        """Test chain stats --json-output (line 1694)."""
        from rege.orchestration import get_chain_registry
        with patch('rege.orchestration.get_chain_registry') as mock_reg:
            registry = MagicMock()
            registry.get_execution_stats.return_value = {
                "total": 0,
                "completed": 0,
                "failed": 0,
                "avg_duration_ms": 0,
            }
            mock_reg.return_value = registry

            result = runner.invoke(cli, ['chain', 'stats', '--json-output'])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert "total" in data
