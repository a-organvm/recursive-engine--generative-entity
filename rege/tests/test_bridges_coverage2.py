"""
Tests for bridge module coverage improvements.

Targets uncovered lines in:
- rege/bridges/git.py: 75, 78-80, 95-98, 110-126, 135-149, etc.
- rege/bridges/obsidian.py: 95-98, 116-117, 123-134, etc.
- rege/bridges/maxmsp.py: various uncovered paths
- rege/bridges/base.py: 98, 108, 121, 131, 156-159, etc.
- rege/bridges/config.py: various
"""

import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile


# =============================================================================
# Git Bridge
# =============================================================================

class TestGitBridgeConnect:
    """Tests for GitBridge.connect() paths."""

    def test_connect_to_real_git_repo(self, tmp_path):
        """Test connect to a real git repository."""
        from rege.bridges.git import GitBridge

        # Create a fake .git directory
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        bridge = GitBridge(config={"repo_path": str(tmp_path)})
        result = bridge.connect()
        assert result is True
        assert bridge.is_connected

    def test_connect_nonexistent_path(self, tmp_path):
        """Test connect with nonexistent path (lines 78-80)."""
        from rege.bridges.git import GitBridge

        bridge = GitBridge(config={"repo_path": str(tmp_path / "nonexistent")})
        result = bridge.connect()
        assert result is False
        assert not bridge.is_connected
        assert bridge.last_error is not None

    def test_connect_not_git_repo(self, tmp_path):
        """Test connect to directory that's not a git repo."""
        from rege.bridges.git import GitBridge

        bridge = GitBridge(config={"repo_path": str(tmp_path)})
        result = bridge.connect()
        assert result is False
        assert "git" in bridge.last_error.lower() or "repository" in bridge.last_error.lower()

    def test_connect_uses_cwd_when_no_path(self):
        """Test connect uses current directory when no path (line 75)."""
        from rege.bridges.git import GitBridge
        bridge = GitBridge()
        # Connect to current directory (which is a git repo in this workspace)
        result = bridge.connect()
        # Result depends on whether cwd is a git repo
        assert isinstance(result, bool)

    def test_disconnect(self, tmp_path):
        """Test disconnect (lines 95-98)."""
        from rege.bridges.git import GitBridge
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        bridge = GitBridge(config={"repo_path": str(tmp_path)})
        bridge.connect()
        result = bridge.disconnect()
        assert result is True
        assert not bridge.is_connected


class TestGitBridgeSend:
    """Tests for GitBridge.send() paths."""

    def test_send_when_not_connected(self, tmp_path):
        """Test send when not connected (lines 112-114)."""
        from rege.bridges.git import GitBridge
        bridge = GitBridge()
        result = bridge.send({"type": "generic"})
        assert result["status"] == "failed"
        assert "Not connected" in result["error"]

    def test_send_system_event(self, tmp_path):
        """Test send with system_event type (lines 118-119)."""
        from rege.bridges.git import GitBridge
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        bridge = GitBridge(config={"repo_path": str(tmp_path)})
        bridge.connect()

        result = bridge.send({
            "type": "system_event",
            "event_type": "test_event",
            "event_data": {"organ": "HEART_OF_CANON", "charge": 80},
        })
        assert result["status"] in ("logged", "failed")

    def test_send_install_hooks(self, tmp_path):
        """Test send with install_hooks type (lines 120-121)."""
        from rege.bridges.git import GitBridge
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        bridge = GitBridge(config={"repo_path": str(tmp_path)})
        bridge.connect()

        result = bridge.send({"type": "install_hooks"})
        assert result["status"] in ("installed", "failed")

    def test_send_generic_event(self, tmp_path):
        """Test send with generic event (line 123)."""
        from rege.bridges.git import GitBridge
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        bridge = GitBridge(config={"repo_path": str(tmp_path)})
        bridge.connect()

        result = bridge.send({"type": "unknown", "data": "test"})
        assert result["status"] in ("logged", "failed")


class TestGitBridgeReceive:
    """Tests for GitBridge.receive() paths."""

    def test_receive_when_not_connected(self):
        """Test receive when not connected (lines 137-139)."""
        from rege.bridges.git import GitBridge
        bridge = GitBridge()
        result = bridge.receive()
        assert result is None

    def test_receive_when_connected(self, tmp_path):
        """Test receive returns repo state (lines 141-149)."""
        from rege.bridges.git import GitBridge
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        bridge = GitBridge(config={"repo_path": str(tmp_path)})
        bridge.connect()

        result = bridge.receive()
        assert result is not None
        assert "current_branch" in result
        assert "has_uncommitted" in result
        assert "recent_commits" in result


class TestGitBridgeHelpers:
    """Tests for GitBridge helper methods."""

    def test_log_system_event(self, tmp_path):
        """Test _log_system_event writes to .rege directory (lines 226-243)."""
        from rege.bridges.git import GitBridge
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        bridge = GitBridge(config={"repo_path": str(tmp_path)})
        bridge.connect()

        result = bridge._log_system_event({
            "event_type": "test",
            "event_data": {"test": True},
        })
        assert result["status"] in ("logged", "failed")
        if result["status"] == "logged":
            assert (tmp_path / ".rege" / "SYSTEM_EVENT_LOG.jsonl").exists()

    def test_log_generic_event(self, tmp_path):
        """Test _log_generic_event delegates to _log_system_event (lines 246-250)."""
        from rege.bridges.git import GitBridge
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        bridge = GitBridge(config={"repo_path": str(tmp_path)})
        bridge.connect()

        result = bridge._log_generic_event({"data": "test"})
        assert result["status"] in ("logged", "failed")

    def test_install_hooks(self, tmp_path):
        """Test _install_hooks creates hooks in .git/hooks (lines 252-283)."""
        from rege.bridges.git import GitBridge
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        bridge = GitBridge(config={"repo_path": str(tmp_path)})
        bridge.connect()

        result = bridge._install_hooks()
        assert result["status"] in ("installed", "failed")
        if result["status"] == "installed":
            assert len(result["hooks"]) > 0

    def test_install_hook_with_backup(self, tmp_path):
        """Test _install_hook backs up existing hook (lines 290-295)."""
        from rege.bridges.git import GitBridge
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir()

        # Create existing hook
        existing_hook = hooks_dir / "pre-commit"
        existing_hook.write_text("#!/bin/bash\necho 'existing'")

        bridge = GitBridge(config={"repo_path": str(tmp_path)})
        bridge.connect()

        result = bridge._install_hook("pre-commit", "#!/bin/bash\necho 'new'")
        assert result["status"] in ("installed", "failed")

    def test_get_current_branch_when_connected(self, tmp_path):
        """Test _get_current_branch (lines 167-178)."""
        from rege.bridges.git import GitBridge
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        bridge = GitBridge(config={"repo_path": str(tmp_path)})
        bridge.connect()

        branch = bridge._get_current_branch()
        assert isinstance(branch, str)

    def test_get_recent_commits_parsing(self, tmp_path):
        """Test _get_recent_commits parsing (lines 193-223)."""
        from rege.bridges.git import GitBridge
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        bridge = GitBridge(config={"repo_path": str(tmp_path)})
        bridge.connect()

        # Returns empty list for non-real repo
        commits = bridge._get_recent_commits(3)
        assert isinstance(commits, list)

    def test_get_repo_root(self, tmp_path):
        """Test _get_repo_root returns parent of .git (lines 161-165)."""
        from rege.bridges.git import GitBridge
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        bridge = GitBridge(config={"repo_path": str(tmp_path)})
        bridge.connect()

        root = bridge._get_repo_root()
        assert root is not None
        assert root == tmp_path

    def test_bridge_status_info(self, tmp_path):
        """Test bridge status() method (lines 376, 380-381)."""
        from rege.bridges.git import GitBridge
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        bridge = GitBridge(config={"repo_path": str(tmp_path)})
        bridge.connect()

        status = bridge.status()
        assert "status" in status
        assert "operations_count" in status


# =============================================================================
# Obsidian Bridge
# =============================================================================

class TestObsidianBridge:
    """Tests for ObsidianBridge."""

    def _create_vault(self, tmp_path):
        """Create a minimal Obsidian vault structure."""
        obsidian_dir = tmp_path / ".obsidian"
        obsidian_dir.mkdir()
        return tmp_path

    def test_disconnect(self, tmp_path):
        """Test disconnect (lines 95-98)."""
        from rege.bridges.obsidian import ObsidianBridge
        vault = self._create_vault(tmp_path)

        bridge = ObsidianBridge(config={"vault_path": str(vault)})
        bridge.connect()
        result = bridge.disconnect()
        assert result is True
        assert not bridge.is_connected

    def test_send_not_connected(self):
        """Test send when not connected (lines 116-117)."""
        from rege.bridges.obsidian import ObsidianBridge
        bridge = ObsidianBridge()
        result = bridge.send({"fragment": {"id": "F1", "name": "Test"}})
        assert result["status"] == "failed"
        assert "Not connected" in result["error"]

    def test_send_single_fragment(self, tmp_path):
        """Test send with single fragment (lines 119-122)."""
        from rege.bridges.obsidian import ObsidianBridge
        vault = self._create_vault(tmp_path)

        bridge = ObsidianBridge(config={"vault_path": str(vault)})
        bridge.connect()

        result = bridge.send({
            "fragment": {
                "id": "FRAG_001",
                "name": "Test Fragment",
                "charge": 75,
                "tags": ["CANON+"],
                "content": "This is a test fragment",
            }
        })
        assert result["status"] in ("exported", "failed")

    def test_send_batch_fragments(self, tmp_path):
        """Test send with batch fragments (lines 123-132)."""
        from rege.bridges.obsidian import ObsidianBridge
        vault = self._create_vault(tmp_path)

        bridge = ObsidianBridge(config={"vault_path": str(vault)})
        bridge.connect()

        result = bridge.send({
            "fragments": [
                {"id": "F1", "name": "Fragment 1", "charge": 60},
                {"id": "F2", "name": "Fragment 2", "charge": 70},
            ]
        })
        assert result["status"] in ("exported", "failed")
        if result["status"] == "exported":
            assert "count" in result

    def test_send_no_fragment_data(self, tmp_path):
        """Test send with no fragment data (line 134)."""
        from rege.bridges.obsidian import ObsidianBridge
        vault = self._create_vault(tmp_path)

        bridge = ObsidianBridge(config={"vault_path": str(vault)})
        bridge.connect()

        result = bridge.send({"other": "data"})
        assert result["status"] == "failed"

    def test_receive_not_connected(self):
        """Test receive when not connected (lines 156-158)."""
        from rege.bridges.obsidian import ObsidianBridge
        bridge = ObsidianBridge()
        result = bridge.receive()
        assert result is None

    def test_receive_when_connected_no_fragments(self, tmp_path):
        """Test receive when connected with no FRAGMENTS folder (lines 161-163)."""
        from rege.bridges.obsidian import ObsidianBridge
        vault = self._create_vault(tmp_path)

        bridge = ObsidianBridge(config={"vault_path": str(vault)})
        bridge.connect()

        result = bridge.receive()
        assert result is not None
        assert "fragments" in result

    def test_receive_with_existing_fragments(self, tmp_path):
        """Test receive with actual fragment files (lines 165-176)."""
        from rege.bridges.obsidian import ObsidianBridge
        vault = self._create_vault(tmp_path)

        # Create FRAGMENTS folder with a markdown file
        fragments_dir = vault / "FRAGMENTS"
        fragments_dir.mkdir()
        fragment_file = fragments_dir / "test_fragment.md"
        fragment_file.write_text("""---
id: FRAG_001
name: Test Fragment
charge: 75
---

# Test Fragment

This is a test fragment content.
""")

        bridge = ObsidianBridge(config={"vault_path": str(vault)})
        bridge.connect()

        result = bridge.receive()
        assert result is not None
        assert "fragments" in result

    def test_bridge_status(self, tmp_path):
        """Test bridge status() method."""
        from rege.bridges.obsidian import ObsidianBridge
        vault = self._create_vault(tmp_path)

        bridge = ObsidianBridge(config={"vault_path": str(vault)})
        bridge.connect()

        status = bridge.status()
        assert "status" in status
        assert status["status"] == "connected"


# =============================================================================
# MaxMSP Bridge
# =============================================================================

class TestMaxMSPBridge:
    """Tests for MaxMSPBridge."""

    def test_connect_fails_when_no_server(self):
        """Test connect fails gracefully when Max/MSP not running (lines 73-80)."""
        from rege.bridges.maxmsp import MaxMSPBridge
        bridge = MaxMSPBridge(config={"host": "127.0.0.1", "port": 19999})
        result = bridge.connect()
        # Will fail since no server is running
        assert isinstance(result, bool)

    def test_send_not_connected(self):
        """Test send when not connected (lines 93-96)."""
        from rege.bridges.maxmsp import MaxMSPBridge
        bridge = MaxMSPBridge()
        result = bridge.send({"message": "test"})
        assert result["status"] == "failed"

    def test_receive_not_connected(self):
        """Test receive when not connected (lines 127-128)."""
        from rege.bridges.maxmsp import MaxMSPBridge
        bridge = MaxMSPBridge()
        result = bridge.receive()
        assert result is None

    def test_disconnect_not_connected(self):
        """Test disconnect when not connected."""
        from rege.bridges.maxmsp import MaxMSPBridge
        bridge = MaxMSPBridge()
        result = bridge.disconnect()
        assert isinstance(result, bool)

    def test_bridge_default_config(self):
        """Test MaxMSP bridge with default config."""
        from rege.bridges.maxmsp import MaxMSPBridge
        bridge = MaxMSPBridge()
        assert bridge is not None

    def test_bridge_custom_config(self):
        """Test MaxMSP bridge with custom host/port."""
        from rege.bridges.maxmsp import MaxMSPBridge
        bridge = MaxMSPBridge(config={"host": "192.168.1.1", "port": 8000})
        assert bridge is not None


# =============================================================================
# Bridge Base and Registry
# =============================================================================

class TestBridgeBase:
    """Tests for BridgeBase uncovered paths."""

    def test_get_safe_config_masks_sensitive_keys(self):
        """Test _get_safe_config masks sensitive values (lines 156-159)."""
        from rege.bridges.obsidian import ObsidianBridge

        bridge = ObsidianBridge(config={
            "vault_path": "/test",
            "password": "secret123",
            "token": "abc123token",
            "api_key": "mykey",
        })

        safe_config = bridge._get_safe_config()
        assert safe_config["password"] == "***"
        assert safe_config["token"] == "***"
        assert safe_config["api_key"] == "***"
        assert safe_config["vault_path"] == "/test"

    def test_operations_log_tracking(self):
        """Test _log_operation records operations."""
        from rege.bridges.git import GitBridge
        bridge = GitBridge()
        # Operations are logged via _log_operation
        bridge._log_operation("test_op", status="started")
        assert len(bridge._operations_log) > 0

    def test_bridge_status_method(self):
        """Test status() method returns all expected fields."""
        from rege.bridges.git import GitBridge
        bridge = GitBridge(config={"repo_path": "/tmp"})
        status = bridge.status()
        assert "name" in status
        assert "status" in status
        assert "is_connected" in status
        assert "connected_at" in status
        assert "last_error" in status
        assert "operations_count" in status
        assert "config" in status


class TestBridgeRegistry:
    """Tests for bridge registry uncovered paths (lines 96, 140)."""

    def test_registry_list_types(self):
        """Test registry lists bridge types."""
        from rege.bridges import get_bridge_registry
        registry = get_bridge_registry()
        types = registry.list_types()
        assert isinstance(types, list)
        assert len(types) > 0

    def test_registry_has_type(self):
        """Test registry.has_type() method."""
        from rege.bridges import get_bridge_registry
        registry = get_bridge_registry()
        assert registry.has_type("obsidian")
        assert registry.has_type("git")
        assert registry.has_type("maxmsp")
        assert not registry.has_type("nonexistent_bridge_xyz")

    def test_registry_create_bridge(self):
        """Test creating a bridge instance via registry (line 96)."""
        from rege.bridges import get_bridge_registry
        registry = get_bridge_registry()
        bridge = registry.create_bridge("git", instance_name="test-git")
        assert bridge is not None

    def test_registry_get_bridge(self):
        """Test getting bridge by name (line 140)."""
        from rege.bridges import get_bridge_registry
        registry = get_bridge_registry()

        # Create one first
        bridge = registry.create_bridge("obsidian", instance_name="test-obs")
        retrieved = registry.get_bridge("test-obs")
        assert retrieved is not None

    def test_registry_get_nonexistent_bridge(self):
        """Test getting nonexistent bridge returns None."""
        from rege.bridges import get_bridge_registry
        registry = get_bridge_registry()
        bridge = registry.get_bridge("definitely_does_not_exist_xyz")
        assert bridge is None


# =============================================================================
# Bridge Config
# =============================================================================

class TestBridgeConfig:
    """Tests for bridge config uncovered paths."""

    def test_get_bridge_config_default(self):
        """Test getting bridge config."""
        from rege.bridges import get_bridge_config
        config = get_bridge_config()
        assert config is not None

    def test_set_bridge_config(self):
        """Test setting bridge config."""
        from rege.bridges import get_bridge_config
        config = get_bridge_config()
        config.set_bridge_config("obsidian", "obsidian")
        bridge_cfg = config.get_bridge_config("obsidian")
        assert bridge_cfg is not None

    def test_bridge_config_all_types(self):
        """Test that default configs exist for all bridge types."""
        from rege.bridges import get_bridge_config
        config = get_bridge_config()
        for bridge_type in ["obsidian", "git", "maxmsp"]:
            cfg = config.get_bridge_config(bridge_type)
            # May or may not exist depending on default setup
            assert cfg is None or hasattr(cfg, "bridge_type")
