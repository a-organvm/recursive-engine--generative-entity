"""
Coverage tests for:
- persistence/archive.py: 82-83, 111-112, 125
- persistence/checkpoint.py: 91-92, 131-132
"""

import pytest
import json
import os
from pathlib import Path

from rege.persistence.archive import ArchiveManager
from rege.persistence.checkpoint import CheckpointManager
from rege.core.exceptions import PersistenceError, CheckpointNotFound
from rege.core.models import RecoveryTrigger


# ============================================================
# ArchiveManager coverage
# ============================================================

class TestArchiveSaveRaisesError:
    """Cover lines 82-83: save() raises PersistenceError on write failure."""

    def test_save_raises_persistence_error_on_write_failure(self, tmp_path):
        """Lines 82-83: PermissionError during write → PersistenceError raised."""
        archive = ArchiveManager(str(tmp_path))

        # Make the patches subdir read-only so the write fails
        patches_dir = tmp_path / "patches"
        patches_dir.chmod(0o444)

        try:
            with pytest.raises(PersistenceError):
                archive.save("patches", "test.json", {"key": "value"})
        finally:
            # Restore permissions so cleanup works
            patches_dir.chmod(0o755)


class TestArchiveLoadRaisesError:
    """Cover lines 111-112: load() raises PersistenceError on non-JSON exception."""

    def test_load_raises_persistence_error_on_permission_denied(self, tmp_path):
        """Lines 111-112: PermissionError during read → PersistenceError raised."""
        archive = ArchiveManager(str(tmp_path))

        # Write a valid JSON file first
        archive.save("patches", "readable.json", {"key": "value"})
        file_path = tmp_path / "patches" / "readable.json"

        # Make it unreadable (no read permissions)
        file_path.chmod(0o000)

        try:
            with pytest.raises(PersistenceError):
                archive.load("patches", "readable.json")
        finally:
            # Restore permissions so cleanup works
            file_path.chmod(0o644)


class TestArchiveAppendWrapsNonList:
    """Cover line 125: append() wraps non-list loaded data in a list."""

    def test_append_wraps_dict_in_list(self, tmp_path):
        """Line 125: loaded data is a dict → wrap in list before appending."""
        archive = ArchiveManager(str(tmp_path))

        # Save a dict (not a list) as the file content
        archive.save("logs", "test_log.json", {"existing": "dict_data"})

        # append() loads the dict → isinstance check fails → wraps in list (line 125)
        archive.append("logs", "test_log.json", {"new": "entry"})

        result = archive.load("logs", "test_log.json")
        assert isinstance(result, list)
        # Wrapped dict + new entry = 2 items
        assert len(result) == 2
        assert result[0] == {"existing": "dict_data"}
        assert result[1] == {"new": "entry"}

    def test_append_wraps_string_in_list(self, tmp_path):
        """Line 125: loaded data is a string → wrap in list."""
        archive = ArchiveManager(str(tmp_path))

        archive.save("logs", "str_log.json", "just a string")
        archive.append("logs", "str_log.json", {"new": "entry"})

        result = archive.load("logs", "str_log.json")
        assert isinstance(result, list)
        assert len(result) == 2


# ============================================================
# CheckpointManager coverage
# ============================================================

class TestCheckpointSaveSnapshotRaisesError:
    """Cover lines 91-92: _save_snapshot raises PersistenceError on write failure."""

    def test_save_snapshot_raises_on_permission_error(self, tmp_path):
        """Lines 91-92: PermissionError writing snapshot → PersistenceError raised."""
        archive = ArchiveManager(str(tmp_path))
        manager = CheckpointManager(archive_manager=archive)

        # Make the snapshots dir read-only so write fails
        snapshots_dir = manager._snapshots_dir
        snapshots_dir.chmod(0o444)

        try:
            with pytest.raises(PersistenceError):
                manager.create_checkpoint(
                    "test_checkpoint",
                    {"metrics": {}, "organs": {}, "pending": [], "errors": []},
                )
        finally:
            snapshots_dir.chmod(0o755)


class TestCheckpointLoadSnapshotRaisesError:
    """Cover lines 131-132: load_checkpoint raises PersistenceError on read failure."""

    def test_load_checkpoint_raises_on_permission_error(self, tmp_path):
        """Lines 131-132: PermissionError reading snapshot → PersistenceError raised."""
        archive = ArchiveManager(str(tmp_path))
        manager = CheckpointManager(archive_manager=archive)

        # Create a valid checkpoint first
        snapshot = manager.create_checkpoint(
            "readable_checkpoint",
            {"metrics": {}, "organs": {}, "pending": [], "errors": []},
        )
        snapshot_id = snapshot.snapshot_id

        # Make the snapshot file unreadable
        snapshot_file = manager._snapshots_dir / f"{snapshot_id}.json"
        snapshot_file.chmod(0o000)

        try:
            with pytest.raises(PersistenceError):
                manager.load_checkpoint(snapshot_id)
        finally:
            snapshot_file.chmod(0o644)

    def test_load_checkpoint_raises_not_found_for_missing(self, tmp_path):
        """load_checkpoint raises CheckpointNotFound for non-existent snapshot."""
        archive = ArchiveManager(str(tmp_path))
        manager = CheckpointManager(archive_manager=archive)

        with pytest.raises(CheckpointNotFound):
            manager.load_checkpoint("SNAP_NONEXISTENT_00000000_000000")
