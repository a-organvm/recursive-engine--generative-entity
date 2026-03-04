"""
Coverage tests for:
- bridges/config.py: 73-76, 106-107, 167-173, 253, 269, 276-277, 280-282
- bridges/obsidian.py: 162-163, 196, 215-216, 242, 262-266, 283-284, 289,
                        302, 308-309, 333-336, 345-349, 353, 357-358
- bridges/git.py: 165, 177-178, 190-191, 210-223, 255, 294-295, 305-306,
                  376, 380-381
- bridges/maxmsp.py: 103-106, 138-143, 166-174, 188-192, 212, 220, 239,
                      243-253, 257-268, 276-287, 303, 307, 311-314
"""

import pytest
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from rege.bridges.config import BridgeConfig
from rege.bridges.obsidian import ObsidianBridge
from rege.bridges.git import GitBridge
from rege.bridges.maxmsp import MaxMSPBridge
from rege.bridges.base import BridgeStatus
from rege.core.models import Fragment


# ============================================================
# BridgeConfig coverage
# ============================================================

class TestBridgeConfigLoadCorruptFile:
    """Cover lines 73-76: except (json.JSONDecodeError, OSError) in load()."""

    def test_load_corrupt_json_returns_false(self, tmp_path):
        """Lines 73-76: corrupt JSON → exception caught → return False."""
        config_file = tmp_path / "rege-bridges.json"
        config_file.write_text("NOT VALID JSON {{{")

        config = BridgeConfig(config_file)
        result = config.load()

        # Lines 73-76: json.JSONDecodeError caught → return False
        assert result is False

    def test_load_unreadable_file_returns_false(self, tmp_path):
        """Lines 73-76: unreadable file → OSError caught → return False."""
        config_file = tmp_path / "rege-bridges.json"
        # Write valid JSON first
        config_file.write_text('{"bridges": {}}')
        # Make it unreadable
        config_file.chmod(0o000)

        try:
            config = BridgeConfig(config_file)
            result = config.load()
            assert result is False
        finally:
            config_file.chmod(0o644)


class TestBridgeConfigSaveFails:
    """Cover lines 106-107: except OSError in save()."""

    def test_save_to_readonly_dir_returns_false(self, tmp_path):
        """Lines 106-107: OSError on write → return False."""
        read_only_dir = tmp_path / "readonly"
        read_only_dir.mkdir()
        config_file = read_only_dir / "rege-bridges.json"

        config = BridgeConfig(config_file)
        config.load()  # creates default config

        # Make directory read-only so write fails
        read_only_dir.chmod(0o444)

        try:
            result = config.save()
            assert result is False
        finally:
            read_only_dir.chmod(0o755)


class TestBridgeConfigEnvOverrides:
    """Cover lines 167-173: _apply_env_overrides() with REGE_BRIDGE_ vars."""

    def test_env_override_applied_to_bridge_config(self, tmp_path, monkeypatch):
        """Lines 167-173: REGE_BRIDGE_<NAME>_<KEY>=value overrides bridge config."""
        config_file = tmp_path / "rege-bridges.json"
        config = BridgeConfig(config_file)

        # First load creates default config in memory, then save to disk
        config.load()
        config.save()

        # Set env override before reloading from disk
        monkeypatch.setenv("REGE_BRIDGE_OBSIDIAN_VAULT_PATH", "/test/vault/path")

        # Lines 167-173: _apply_env_overrides called during load() after parsing file
        config.load()

        obsidian_config = config.get_bridge_config("obsidian")
        assert obsidian_config is not None
        assert obsidian_config.config.get("vault_path") == "/test/vault/path"


class TestBridgeConfigRemoveMissing:
    """Cover line 253: return False in remove_bridge() when not found."""

    def test_remove_nonexistent_bridge_returns_false(self, tmp_path):
        """Line 253: bridge not in _bridges → return False."""
        config = BridgeConfig(tmp_path / "config.json")
        config.load()

        result = config.remove_bridge("NONEXISTENT_BRIDGE")
        assert result is False

    def test_remove_existing_bridge_returns_true(self, tmp_path):
        """Verify remove_bridge returns True for existing bridge."""
        config = BridgeConfig(tmp_path / "config.json")
        config.load()  # creates default with obsidian, git, maxmsp

        result = config.remove_bridge("obsidian")
        assert result is True
        assert config.get_bridge_config("obsidian") is None


class TestBridgeConfigValidateNotFound:
    """Cover line 269: return {"valid": False, ...} in validate_config() when bridge not found."""

    def test_validate_nonexistent_bridge_returns_invalid(self, tmp_path):
        """Line 269: bridge not found → return {"valid": False, "errors": ["Bridge not found"]}."""
        config = BridgeConfig(tmp_path / "config.json")
        config.load()

        result = config.validate_config("NONEXISTENT_BRIDGE")
        assert result["valid"] is False
        assert "Bridge not found" in result["errors"]


class TestBridgeConfigValidateObsidianVaultPath:
    """Cover lines 276-277: obsidian with non-existent vault_path."""

    def test_validate_obsidian_nonexistent_path(self, tmp_path):
        """Lines 276-277: vault_path exists but path doesn't → error appended."""
        config = BridgeConfig(tmp_path / "config.json")
        config.load()

        # Set a vault_path that doesn't exist
        config.set_bridge_config(
            "obsidian_test", "obsidian",
            config={"vault_path": "/nonexistent/vault/path/xyz"}
        )

        result = config.validate_config("obsidian_test")
        # Lines 276-277: path doesn't exist → error added
        assert result["valid"] is False
        assert any("vault_path" in e or "does not exist" in e for e in result["errors"])


class TestBridgeConfigValidateGitBridge:
    """Cover lines 280-282: git bridge type validation."""

    def test_validate_git_with_nonexistent_path(self, tmp_path):
        """Lines 280-282: git bridge with missing repo_path → error."""
        config = BridgeConfig(tmp_path / "config.json")
        config.load()

        config.set_bridge_config(
            "git_test", "git",
            config={"repo_path": "/nonexistent/repo/path/xyz"}
        )

        result = config.validate_config("git_test")
        # Lines 280-282: repo_path doesn't exist → error added
        assert result["valid"] is False
        assert any("repo_path" in e for e in result["errors"])

    def test_validate_git_empty_repo_path_is_valid(self, tmp_path):
        """Git bridge with empty repo_path passes (path check skipped when empty)."""
        config = BridgeConfig(tmp_path / "config.json")
        config.load()

        config.set_bridge_config("git_empty", "git", config={"repo_path": ""})
        result = config.validate_config("git_empty")
        assert result["valid"] is True


# ============================================================
# ObsidianBridge coverage
# ============================================================

def make_vault(tmp_path: Path) -> Path:
    """Create a minimal Obsidian vault structure."""
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / ".obsidian").mkdir()
    return vault


class TestObsidianReceiveNoFragmentsFolder:
    """Cover lines 162-163: receive() when FRAGMENTS folder doesn't exist."""

    def test_receive_no_fragments_folder_returns_empty(self, tmp_path):
        """Lines 162-163: connected but FRAGMENTS missing → return {"fragments": []}."""
        vault = make_vault(tmp_path)
        bridge = ObsidianBridge("test", {"vault_path": str(vault)})
        bridge.connect()

        # Remove FRAGMENTS folder that was created by connect()
        fragments_dir = vault / "FRAGMENTS"
        fragments_dir.rmdir()

        # Lines 162-163: FRAGMENTS doesn't exist → return empty list
        result = bridge.receive()
        assert result is not None
        assert result["fragments"] == []


class TestObsidianExportFragmentWithToDict:
    """Cover line 196: fragment.to_dict() in _export_fragment."""

    def test_export_fragment_object_with_to_dict(self, tmp_path):
        """Line 196: fragment has to_dict() → frag_dict = fragment.to_dict()."""
        vault = make_vault(tmp_path)
        bridge = ObsidianBridge("test", {"vault_path": str(vault)})
        bridge.connect()

        # Fragment object with to_dict() method
        fragment = Fragment(
            id="FRAG_TEST01",
            name="test fragment",
            charge=75,
            tags=["CANON+"],
        )

        result = bridge.send({"fragment": fragment})
        # Line 196: fragment.to_dict() called
        assert result["status"] == "exported"


class TestObsidianExportFragmentOSError:
    """Cover lines 215-216: OSError in _export_fragment()."""

    def test_export_to_readonly_directory_returns_failed(self, tmp_path):
        """Lines 215-216: OSError when writing fragment → return failed status."""
        vault = make_vault(tmp_path)
        bridge = ObsidianBridge("test", {"vault_path": str(vault)})
        bridge.connect()

        # Make FRAGMENTS read-only
        fragments_dir = vault / "FRAGMENTS"
        fragments_dir.chmod(0o444)

        try:
            result = bridge._export_fragment({"id": "FRAG_001", "name": "test"})
            # Lines 215-216: OSError → return {"status": "failed", "error": str(e)}
            assert result["status"] == "failed"
            assert "error" in result
        finally:
            fragments_dir.chmod(0o755)


class TestObsidianFragmentMarkdownCreatedAt:
    """Cover line 242: created_at in frontmatter."""

    def test_fragment_with_created_at_includes_it(self, tmp_path):
        """Line 242: fragment with created_at → frontmatter includes created_at."""
        vault = make_vault(tmp_path)
        bridge = ObsidianBridge("test", {"vault_path": str(vault)})
        bridge.connect()

        frag = {
            "id": "FRAG_002",
            "name": "test with date",
            "charge": 60,
            "created_at": "2024-01-01T10:00:00",
        }

        result = bridge._export_fragment(frag)
        assert result["status"] == "exported"

        # Verify file content has created_at
        exported_file = Path(result["file"])
        content = exported_file.read_text()
        assert "created_at: 2024-01-01T10:00:00" in content  # Line 242


class TestObsidianFragmentMarkdownMetadata:
    """Cover lines 262-266: metadata block in _fragment_to_markdown()."""

    def test_fragment_with_metadata_includes_block(self, tmp_path):
        """Lines 262-266: fragment with 'metadata' key → metadata block appended."""
        vault = make_vault(tmp_path)
        bridge = ObsidianBridge("test", {"vault_path": str(vault)})
        bridge.connect()

        frag = {
            "id": "FRAG_003",
            "name": "test with meta",
            "charge": 60,
            "metadata": {"key1": "value1", "key2": "value2"},
        }

        result = bridge._export_fragment(frag)
        assert result["status"] == "exported"

        exported_file = Path(result["file"])
        content = exported_file.read_text()
        # Lines 262-266: metadata block present
        assert "## Metadata" in content
        assert "**key1:** value1" in content


class TestObsidianImportFragmentOSError:
    """Cover lines 283-284: OSError in _import_fragment()."""

    def test_import_unreadable_file_returns_none(self, tmp_path):
        """Lines 283-284: OSError reading file → return None."""
        vault = make_vault(tmp_path)
        bridge = ObsidianBridge("test", {"vault_path": str(vault)})
        bridge.connect()

        # Create a file then make it unreadable
        test_file = vault / "FRAGMENTS" / "unreadable.md"
        test_file.write_text("content")
        test_file.chmod(0o000)

        try:
            result = bridge._import_fragment(test_file)
            # Lines 283-284: OSError caught → return None
            assert result is None
        finally:
            test_file.chmod(0o644)


class TestObsidianImportFragmentNoFrontmatter:
    """Cover line 289: no frontmatter match → return None."""

    def test_import_file_without_frontmatter_returns_none(self, tmp_path):
        """Line 289: file has no YAML frontmatter → return None."""
        vault = make_vault(tmp_path)
        bridge = ObsidianBridge("test", {"vault_path": str(vault)})
        bridge.connect()

        no_frontmatter = vault / "FRAGMENTS" / "no_front.md"
        no_frontmatter.write_text("Just plain markdown content, no frontmatter.\n# Title\nbody text")

        result = bridge._import_fragment(no_frontmatter)
        # Line 289: no frontmatter match → None
        assert result is None


class TestObsidianImportFragmentTagsList:
    """Cover line 302: tags list parsing in _import_fragment()."""

    def test_import_file_with_tags_list_parsed_correctly(self, tmp_path):
        """Line 302: tags: [canon, echo] → parsed as list."""
        vault = make_vault(tmp_path)
        bridge = ObsidianBridge("test", {"vault_path": str(vault)})
        bridge.connect()

        tagged_file = vault / "FRAGMENTS" / "tagged.md"
        tagged_file.write_text(
            "---\nid: FRAG_004\nname: tagged fragment\ncharge: 70\ntags: [canon, echo]\n---\ncontent"
        )

        result = bridge._import_fragment(tagged_file)
        assert result is not None
        # Line 302: tags parsed as list
        assert isinstance(result["tags"], list)


class TestObsidianImportFragmentChargeValueError:
    """Cover lines 308-309: ValueError when parsing charge."""

    def test_import_file_with_non_numeric_charge(self, tmp_path):
        """Lines 308-309: charge: 'not_a_number' → ValueError → default 50."""
        vault = make_vault(tmp_path)
        bridge = ObsidianBridge("test", {"vault_path": str(vault)})
        bridge.connect()

        bad_charge_file = vault / "FRAGMENTS" / "bad_charge.md"
        bad_charge_file.write_text(
            "---\nid: FRAG_005\nname: bad charge\ncharge: not_a_number\n---\ncontent"
        )

        result = bridge._import_fragment(bad_charge_file)
        assert result is not None
        # Lines 308-309: ValueError → charge defaults to 50
        assert result["charge"] == 50


class TestObsidianSyncWhenNotConnected:
    """Cover lines 333-336 and 345-349: sync methods when not connected."""

    def test_sync_to_vault_not_connected_returns_failed(self, tmp_path):
        """Lines 333-336: sync_to_vault() when not connected → failed."""
        bridge = ObsidianBridge("test", {"vault_path": str(tmp_path)})
        # Not connected
        result = bridge.sync_to_vault([])
        # Lines 333-336: not connected → return failed
        assert result["status"] == "failed"

    def test_sync_from_vault_not_connected_returns_failed(self, tmp_path):
        """Lines 345-349: sync_from_vault() when not connected → returns {"fragments": []}."""
        bridge = ObsidianBridge("test", {"vault_path": str(tmp_path)})
        # Not connected
        result = bridge.sync_from_vault()
        # Lines 345-349: not connected → receive returns None → {"fragments": []}
        assert "fragments" in result or result.get("status") == "failed"


class TestObsidianGetSetVaultPath:
    """Cover lines 353, 357-358: get_vault_path and set_vault_path."""

    def test_get_vault_path(self, tmp_path):
        """Line 353: get_vault_path() returns configured path."""
        vault = make_vault(tmp_path)
        bridge = ObsidianBridge("test", {"vault_path": str(vault)})
        result = bridge.get_vault_path()
        assert result == vault  # Line 353

    def test_set_vault_path(self, tmp_path):
        """Lines 357-358: set_vault_path updates _vault_path and config."""
        bridge = ObsidianBridge("test")
        bridge.set_vault_path(str(tmp_path))
        # Lines 357-358: vault_path set
        assert bridge._vault_path == tmp_path
        assert bridge._config["vault_path"] == str(tmp_path)


# ============================================================
# GitBridge coverage
# ============================================================

class TestGitBridgeRepoRootNone:
    """Cover line 165: _get_repo_root() returns None when _git_dir is None."""

    def test_get_repo_root_without_git_dir(self):
        """Line 165: _git_dir is None → return None."""
        bridge = GitBridge()
        # _git_dir is None before connect
        result = bridge._get_repo_root()
        assert result is None  # Line 165


class TestGitBridgeSubprocessFailures:
    """Cover lines 177-178, 190-191: subprocess exception handlers."""

    def test_get_current_branch_subprocess_failure(self, tmp_path):
        """Lines 177-178: FileNotFoundError in _get_current_branch() → return 'unknown'."""
        bridge = GitBridge()
        bridge._repo_path = tmp_path

        with patch("rege.bridges.git.subprocess.run", side_effect=FileNotFoundError()):
            result = bridge._get_current_branch()

        assert result == "unknown"  # Line 178

    def test_has_uncommitted_changes_subprocess_failure(self, tmp_path):
        """Lines 190-191: FileNotFoundError in _has_uncommitted_changes() → return False."""
        bridge = GitBridge()
        bridge._repo_path = tmp_path

        with patch("rege.bridges.git.subprocess.run", side_effect=FileNotFoundError()):
            result = bridge._has_uncommitted_changes()

        assert result is False  # Line 191


class TestGitBridgeCommitLoop:
    """Cover lines 210-223: commit loop in _get_recent_commits()."""

    def test_get_recent_commits_parses_output(self, tmp_path):
        """Lines 210-223: mocked subprocess returns commit data → parsed correctly."""
        bridge = GitBridge()
        bridge._repo_path = tmp_path

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = (
            "abc12345|First commit|Author One|2024-01-01 10:00:00\n"
            "def67890|Second commit|Author Two|2024-01-02 11:00:00\n"
        )

        with patch("rege.bridges.git.subprocess.run", return_value=mock_result):
            commits = bridge._get_recent_commits(5)

        # Lines 210-223: commit list parsed
        assert len(commits) == 2
        assert commits[0]["hash"] == "abc12345"[:8]
        assert commits[0]["message"] == "First commit"
        assert commits[0]["author"] == "Author One"


class TestGitBridgeInstallHooksNoGitDir:
    """Cover line 255: _install_hooks() when _git_dir is None."""

    def test_install_hooks_without_git_dir(self):
        """Line 255: _git_dir is None → return failed."""
        bridge = GitBridge()
        bridge._git_dir = None

        result = bridge._install_hooks()
        # Line 255: return {"status": "failed", "error": "No git directory"}
        assert result["status"] == "failed"
        assert "No git directory" in result.get("error", "")


class TestGitBridgeInstallHookFails:
    """Cover lines 294-295, 305-306: _install_hook() error paths."""

    def test_install_hook_write_fails(self, tmp_path):
        """Lines 305-306: OSError when writing hook → return failed."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir()

        bridge = GitBridge()
        bridge._git_dir = git_dir

        # Mock open to raise OSError (hook doesn't exist yet so no backup needed)
        with patch("builtins.open", side_effect=OSError("permission denied")):
            result = bridge._install_hook("pre-commit", "#!/bin/bash\nexit 0\n")

        # Lines 305-306: OSError → return {"status": "failed", ...}
        assert result["status"] == "failed"
        assert "error" in result

    def test_install_hook_backup_oserror_continues(self, tmp_path):
        """Lines 294-295: OSError on backup rename → pass (continue anyway)."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir()

        bridge = GitBridge()
        bridge._git_dir = git_dir

        # Create an existing hook
        hook_path = hooks_dir / "pre-commit"
        hook_path.write_text("existing hook")

        # Mock rename to fail, but write should still succeed
        with patch.object(Path, "rename", side_effect=OSError("rename failed")):
            result = bridge._install_hook("pre-commit", "#!/bin/bash\nexit 0\n")
            # Lines 294-295: OSError on rename → pass, then write succeeds
            assert result["status"] == "installed"


class TestGitBridgeGetSetRepoPath:
    """Cover lines 376, 380-381: get_repo_path and set_repo_path."""

    def test_get_repo_path(self):
        """Line 376: get_repo_path() returns configured path."""
        bridge = GitBridge("test", {"repo_path": "/some/path"})
        result = bridge.get_repo_path()
        assert result == Path("/some/path")  # Line 376

    def test_set_repo_path(self):
        """Lines 380-381: set_repo_path updates _repo_path and config."""
        bridge = GitBridge()
        bridge.set_repo_path("/new/path")
        # Lines 380-381: set
        assert bridge._repo_path == Path("/new/path")
        assert bridge._config["repo_path"] == "/new/path"


# ============================================================
# MaxMSPBridge coverage
# ============================================================

class TestMaxMSPDisconnectWithOscClient:
    """Cover lines 103-106: disconnect() when _osc_client is set."""

    def test_disconnect_with_osc_client_set_sends_message(self):
        """Lines 103-106: _osc_client set → tries to send disconnect message."""
        bridge = MaxMSPBridge()
        bridge.connect()  # mock mode: osc_client = None

        # Manually set osc_client to a mock
        mock_client = MagicMock()
        bridge._osc_client = mock_client

        result = bridge.disconnect()
        # Lines 103-106: osc_client is set → send_message called (may succeed or fail)
        mock_client.send_message.assert_called_once_with("/rege/disconnect", [1])
        assert result is True

    def test_disconnect_with_osc_client_raising_continues(self):
        """Lines 105-106: send_message raises → except Exception: pass."""
        bridge = MaxMSPBridge()
        bridge.connect()

        mock_client = MagicMock()
        mock_client.send_message.side_effect = Exception("OSC error")
        bridge._osc_client = mock_client

        # Lines 105-106: exception caught → pass → disconnect still succeeds
        result = bridge.disconnect()
        assert result is True


class TestMaxMSPSendDataTypes:
    """Cover lines 138-143: send() with bloom_phase, canon_event, batch, generic types."""

    def setup_connected_bridge(self):
        bridge = MaxMSPBridge()
        bridge.connect()  # mock mode
        return bridge

    def test_send_bloom_phase(self):
        """Line 138: data_type == 'bloom_phase' → _send_bloom_phase."""
        bridge = self.setup_connected_bridge()
        result = bridge.send({"type": "bloom_phase", "phase": "spring"})
        assert result["status"] == "sent"

    def test_send_canon_event(self):
        """Line 139: data_type == 'canon_event' → _send_canon_event."""
        bridge = self.setup_connected_bridge()
        result = bridge.send({"type": "canon_event", "event": {"event_id": "EV01", "charge": 80}})
        assert result["status"] == "sent"

    def test_send_batch(self):
        """Lines 140-141: data_type == 'batch' → _send_batch."""
        bridge = self.setup_connected_bridge()
        result = bridge.send({
            "type": "batch",
            "messages": [
                {"type": "charge", "charge": 50},
                {"type": "fragment", "fragment": {"id": "F1", "name": "test"}},
            ]
        })
        assert "sent" in result

    def test_send_generic(self):
        """Line 142: data_type == unknown → _send_generic."""
        bridge = self.setup_connected_bridge()
        result = bridge.send({"type": "unknown_custom_type", "some_key": "some_value"})
        assert result["status"] == "sent"


class TestMaxMSPReceiveWhenConnected:
    """Cover lines 166-174: receive() when connected."""

    def test_receive_returns_state(self):
        """Lines 166-174: receive() when connected → returns state dict."""
        bridge = MaxMSPBridge("test", {"host": "localhost", "port": 7400})
        bridge.connect()  # mock mode

        result = bridge.receive()
        # Lines 166-174: returns state dict
        assert result is not None
        assert result["connected"] is True
        assert result["host"] == "localhost"
        assert result["port"] == 7400
        assert result["mock_mode"] is True  # osc_client is None


class TestMaxMSPSendOscWithClient:
    """Cover lines 188-192: _send_osc() when _osc_client is set."""

    def test_send_osc_with_client_success(self):
        """Lines 188-190: osc_client set → send_message called → return True."""
        bridge = MaxMSPBridge()
        bridge.connect()

        mock_client = MagicMock()
        bridge._osc_client = mock_client

        result = bridge._send_osc("/rege/test", [1, 2, 3])
        # Lines 188-190: send_message called
        mock_client.send_message.assert_called_once_with("/rege/test", [1, 2, 3])
        assert result is True

    def test_send_osc_with_client_failure(self):
        """Lines 191-192: send_message raises → return False."""
        bridge = MaxMSPBridge()
        bridge.connect()

        mock_client = MagicMock()
        mock_client.send_message.side_effect = Exception("OSC fail")
        bridge._osc_client = mock_client

        result = bridge._send_osc("/rege/test", [1])
        # Lines 191-192: exception → return False
        assert result is False


class TestMaxMSPSendOscFailPaths:
    """Cover lines 212, 220, 239: failed send paths in fragment, charge, bloom_phase."""

    def setup_failing_bridge(self):
        bridge = MaxMSPBridge()
        bridge.connect()
        mock_client = MagicMock()
        mock_client.send_message.side_effect = Exception("OSC fail")
        bridge._osc_client = mock_client
        return bridge

    def test_send_fragment_fail(self):
        """Line 212: _send_fragment when _send_osc returns False."""
        bridge = self.setup_failing_bridge()
        result = bridge.send({"type": "fragment", "fragment": {"id": "F1", "name": "test"}})
        assert result["status"] == "failed"  # Line 212

    def test_send_charge_fail(self):
        """Line 220: _send_charge when _send_osc returns False."""
        bridge = self.setup_failing_bridge()
        result = bridge.send({"type": "charge", "charge": 50})
        assert result["status"] == "failed"  # Line 220

    def test_send_bloom_phase_fail(self):
        """Line 239: _send_bloom_phase when _send_osc returns False."""
        bridge = self.setup_failing_bridge()
        result = bridge.send({"type": "bloom_phase", "phase": "dormant"})
        assert result["status"] == "failed"  # Line 239


class TestMaxMSPSendCanonEvent:
    """Cover lines 243-253: _send_canon_event."""

    def test_send_canon_event_success(self):
        """Lines 243-253: _send_canon_event sends OSC and returns sent."""
        bridge = MaxMSPBridge()
        bridge.connect()  # mock mode (osc_client=None)

        result = bridge._send_canon_event({
            "event_id": "EV_001",
            "charge": 85,
            "status": "glowing",
        })
        assert result["status"] == "sent"  # Lines 243-253

    def test_send_canon_event_fail(self):
        """Line 253: _send_canon_event fails when OSC client raises."""
        bridge = MaxMSPBridge()
        bridge.connect()
        mock_client = MagicMock()
        mock_client.send_message.side_effect = Exception()
        bridge._osc_client = mock_client

        result = bridge._send_canon_event({"event_id": "EV_002"})
        assert result["status"] == "failed"


class TestMaxMSPSendBatch:
    """Cover lines 257-268: _send_batch."""

    def test_send_batch_multiple_messages(self):
        """Lines 257-268: batch with multiple messages → sent/failed counts."""
        bridge = MaxMSPBridge()
        bridge.connect()

        result = bridge._send_batch([
            {"type": "charge", "charge": 50},
            {"type": "fragment", "fragment": {"id": "F1"}},
        ])
        # Lines 257-268: sent and failed counted
        assert "sent" in result
        assert "failed" in result

    def test_send_batch_empty(self):
        """Lines 257-268: empty batch → sent=0, failed=0."""
        bridge = MaxMSPBridge()
        bridge.connect()

        result = bridge._send_batch([])
        assert result["sent"] == 0
        assert result["failed"] == 0
        assert result["status"] == "sent"


class TestMaxMSPSendGeneric:
    """Cover lines 276-287: _send_generic."""

    def test_send_generic_flattens_data(self):
        """Lines 276-287: _send_generic converts data to flat OSC args."""
        bridge = MaxMSPBridge()
        bridge.connect()

        result = bridge._send_generic({"key1": "value1", "key2": 42, "type": "skip_me"})
        # Lines 276-287: type key skipped, rest converted to args
        assert result["status"] == "sent"


class TestMaxMSPGetterSetter:
    """Cover lines 303, 307, 311-314: get_host, get_port, set_connection."""

    def test_get_host(self):
        """Line 303: get_host() returns configured host."""
        bridge = MaxMSPBridge("test", {"host": "192.168.1.100", "port": 7500})
        assert bridge.get_host() == "192.168.1.100"  # Line 303

    def test_get_port(self):
        """Line 307: get_port() returns configured port."""
        bridge = MaxMSPBridge("test", {"host": "localhost", "port": 8888})
        assert bridge.get_port() == 8888  # Line 307

    def test_set_connection(self):
        """Lines 311-314: set_connection updates host, port, and config."""
        bridge = MaxMSPBridge()
        bridge.set_connection("10.0.0.1", 9999)
        # Lines 311-314: all set
        assert bridge._host == "10.0.0.1"
        assert bridge._port == 9999
        assert bridge._config["host"] == "10.0.0.1"
        assert bridge._config["port"] == 9999
