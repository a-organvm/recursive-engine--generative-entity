"""
Final coverage tests for:
- bridges/obsidian.py: 336, 348-349
- bridges/git.py: 222-223, 242-243, 269, 277
- bridges/maxmsp.py: 266, 287
"""

import json
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from rege.bridges.obsidian import ObsidianBridge
from rege.bridges.git import GitBridge
from rege.bridges.maxmsp import MaxMSPBridge


def make_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / ".obsidian").mkdir()
    return vault


# ============================================================
# ObsidianBridge sync methods
# ============================================================

class TestObsidianSyncToVault:
    """Cover line 336: sync_to_vault() when connected."""

    def test_sync_to_vault_when_connected(self, tmp_path):
        """Line 336: sync_to_vault calls self.send({"fragments": fragments})."""
        vault = make_vault(tmp_path)
        bridge = ObsidianBridge("test", {"vault_path": str(vault)})
        bridge.connect()

        result = bridge.sync_to_vault([])
        # Line 336: sends fragments list
        assert result is not None

    def test_sync_to_vault_not_connected(self, tmp_path):
        """Not connected → return failed (covers the is_connected check at line 333)."""
        bridge = ObsidianBridge("test", {"vault_path": str(tmp_path / "vault")})
        result = bridge.sync_to_vault([])
        assert result["status"] == "failed"


class TestObsidianSyncFromVault:
    """Cover lines 348-349: sync_from_vault() when connected."""

    def test_sync_from_vault_when_connected(self, tmp_path):
        """Lines 348-349: sync_from_vault calls self.receive()."""
        vault = make_vault(tmp_path)
        bridge = ObsidianBridge("test", {"vault_path": str(vault)})
        bridge.connect()

        result = bridge.sync_from_vault()
        # Lines 348-349: returns receive() result or {"fragments": []}
        assert isinstance(result, dict)

    def test_sync_from_vault_not_connected(self, tmp_path):
        """Not connected → return failed (covers is_connected check)."""
        bridge = ObsidianBridge("test", {"vault_path": str(tmp_path / "vault")})
        result = bridge.sync_from_vault()
        assert result["status"] == "failed"


# ============================================================
# GitBridge error paths
# ============================================================

class TestGitBridgeGetRecentCommitsException:
    """Cover lines 222-223: except clause in _get_recent_commits()."""

    def test_get_recent_commits_subprocess_error(self, tmp_path):
        """Lines 222-223: subprocess raises SubprocessError → return []."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        bridge = GitBridge()
        bridge._git_dir = git_dir
        bridge._repo_path = tmp_path

        with patch(
            "rege.bridges.git.subprocess.run",
            side_effect=subprocess.SubprocessError("git error")
        ):
            commits = bridge._get_recent_commits(5)

        # Lines 222-223: exception caught → return []
        assert commits == []


class TestGitBridgeLogSystemEventOSError:
    """Cover lines 242-243: except OSError in _log_system_event()."""

    def test_log_system_event_write_fails(self, tmp_path):
        """Lines 242-243: OSError when writing event log → return failed status."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        bridge = GitBridge()
        bridge._git_dir = git_dir
        bridge._repo_path = tmp_path

        with patch("builtins.open", side_effect=OSError("permission denied")):
            result = bridge._log_system_event({"event_type": "test", "event_data": {}})

        # Lines 242-243: OSError → {"status": "failed", "error": ...}
        assert result["status"] == "failed"
        assert "error" in result


class TestGitBridgeInstallHooksErrors:
    """Cover lines 269, 277: errors.append when hooks fail in _install_hooks()."""

    def test_install_hooks_pre_commit_fails(self, tmp_path):
        """Lines 269, 277: both hooks fail → errors list has 2 entries."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir()

        bridge = GitBridge()
        bridge._git_dir = git_dir

        # Mock _install_hook to always return failed
        with patch.object(bridge, "_install_hook", return_value={"status": "failed", "error": "mock fail"}):
            result = bridge._install_hooks()

        # Lines 269, 277: errors.append for each failed hook
        assert result["status"] == "failed"
        assert len(result["errors"]) == 2
        assert "mock fail" in result["errors"]


# ============================================================
# MaxMSPBridge failure paths
# ============================================================

class TestMaxMSPSendBatchWithFailures:
    """Cover line 266: failed += 1 in _send_batch() when messages fail."""

    def test_send_batch_some_messages_fail(self):
        """Line 266: batch with a failing message → failed incremented."""
        bridge = MaxMSPBridge()
        bridge.connect()  # mock mode

        # Set osc_client to mock that raises on send_message → all OSC sends fail
        mock_client = MagicMock()
        mock_client.send_message.side_effect = Exception("OSC error")
        bridge._osc_client = mock_client

        result = bridge._send_batch([
            {"type": "fragment", "fragment": {"id": "F1", "name": "test", "charge": 50, "tags": []}},
        ])

        # Line 266: failed += 1 was executed
        assert result["failed"] == 1
        assert result["sent"] == 0


class TestMaxMSPSendGenericFails:
    """Cover line 287: return failed in _send_generic() when _send_osc fails."""

    def test_send_generic_osc_fails(self):
        """Line 287: _send_osc returns False → return {"status": "failed", ...}."""
        bridge = MaxMSPBridge()
        bridge.connect()  # mock mode

        # Make _send_osc fail by setting osc_client that raises
        mock_client = MagicMock()
        mock_client.send_message.side_effect = Exception("OSC error")
        bridge._osc_client = mock_client

        result = bridge._send_generic({"some_key": "some_value"})

        # Line 287: return {"status": "failed", "error": "OSC send failed"}
        assert result["status"] == "failed"
        assert "error" in result
