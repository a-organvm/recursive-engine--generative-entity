"""
Tests for registry and protocol coverage improvements.

Targets uncovered lines in:
- rege/orchestration/registry.py: 75, 83-85, 100, 139, 142, 185-189, 201, 205, 214-225
- rege/organs/registry.py: 73-76, 96, 108-111, 115, 124, 136-139
- rege/protocols/recovery.py: 110, 116, 152, 197-212, 260, 263, 297, 306, 322, 330, 347-352
- rege/protocols/fuse01.py: 84, 115, 165, 174, 181, 189, 231, 257-262, 295, 309-313
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta


# ==================== ChainRegistry Tests ====================

class TestChainRegistryMissingPaths:
    """Tests for uncovered ChainRegistry methods."""

    def _make_registry_with_execution(self):
        from rege.orchestration.registry import ChainRegistry
        from rege.orchestration.chain import ChainExecution, ChainStatus
        registry = ChainRegistry()
        execution = MagicMock()
        execution.execution_id = "EXEC_001"
        execution.chain_name = "test_chain"
        execution.status = MagicMock()
        execution.status.value = "completed"
        execution.completed_at = datetime.now()
        execution.get_duration_ms.return_value = 500
        registry._execution_history.append(execution)
        return registry, execution

    def test_get_all_returns_copy(self):
        """Test get_all() returns copy of chains dict (line 75)."""
        from rege.orchestration.registry import ChainRegistry
        from rege.orchestration.chain import RitualChain
        from rege.orchestration.phase import Phase
        registry = ChainRegistry()
        phase = Phase(name="p1", organ="HEART_OF_CANON", mode="mythic")
        chain = RitualChain(name="my_chain", phases=[phase])
        registry.register(chain)
        all_chains = registry.get_all()
        assert "my_chain" in all_chains
        # Mutating the copy doesn't affect internal state
        all_chains["extra"] = None
        assert "extra" not in registry._chains

    def test_clear_returns_count(self):
        """Test clear() returns number of cleared chains (lines 83-85)."""
        from rege.orchestration.registry import ChainRegistry
        from rege.orchestration.chain import RitualChain
        from rege.orchestration.phase import Phase
        registry = ChainRegistry()
        for i in range(3):
            phase = Phase(name=f"p{i}", organ="HEART_OF_CANON", mode="mythic")
            chain = RitualChain(name=f"chain_{i}", phases=[phase])
            registry.register(chain)
        count = registry.clear()
        assert count == 3
        assert registry.count() == 0

    def test_get_execution_not_found_returns_none(self):
        """Test get_execution() returns None when not found (line 100)."""
        from rege.orchestration.registry import ChainRegistry
        registry = ChainRegistry()
        result = registry.get_execution("NONEXISTENT_ID")
        assert result is None

    def test_get_execution_stats_with_chain_name_filter(self):
        """Test get_execution_stats() filters by chain_name (line 139)."""
        registry, execution = self._make_registry_with_execution()
        stats = registry.get_execution_stats(chain_name="test_chain")
        assert stats["total"] >= 1

    def test_get_execution_stats_empty_with_filter(self):
        """Test get_execution_stats() returns zeros when no matching chain (line 142)."""
        from rege.orchestration.registry import ChainRegistry
        registry = ChainRegistry()
        # No executions at all
        stats = registry.get_execution_stats(chain_name="nonexistent")
        assert stats["total"] == 0
        assert stats["completed"] == 0

    def test_get_execution_stats_empty_no_filter(self):
        """Test get_execution_stats() returns zeros when empty (line 142)."""
        from rege.orchestration.registry import ChainRegistry
        registry = ChainRegistry()
        stats = registry.get_execution_stats()
        assert stats["total"] == 0
        assert stats["avg_duration_ms"] == 0

    def test_clear_history_with_chain_name_filter(self):
        """Test clear_history() with chain_name filter (lines 185-189)."""
        registry, execution = self._make_registry_with_execution()
        # Add another execution for a different chain
        other_exec = MagicMock()
        other_exec.chain_name = "other_chain"
        registry._execution_history.append(other_exec)

        cleared = registry.clear_history(chain_name="test_chain")
        assert cleared == 1
        assert len(registry._execution_history) == 1
        assert registry._execution_history[0].chain_name == "other_chain"

    def test_to_dict_serialization(self):
        """Test to_dict() serializes registry (lines 201, 205)."""
        from rege.orchestration.registry import ChainRegistry
        from rege.orchestration.chain import RitualChain
        from rege.orchestration.phase import Phase
        registry = ChainRegistry()
        phase = Phase(name="p1", organ="HEART_OF_CANON", mode="mythic")
        chain = RitualChain(name="serial_chain", phases=[phase])
        registry.register(chain)
        result = registry.to_dict()
        assert "chains" in result
        assert "serial_chain" in result["chains"]
        assert "max_history" in result

    def test_from_dict_deserialization(self):
        """Test from_dict() deserializes registry (lines 214-225)."""
        from rege.orchestration.registry import ChainRegistry
        from rege.orchestration.chain import RitualChain
        from rege.orchestration.phase import Phase
        registry = ChainRegistry()
        phase = Phase(name="p1", organ="HEART_OF_CANON", mode="mythic")
        chain = RitualChain(name="deser_chain", phases=[phase])
        registry.register(chain)
        data = registry.to_dict()
        # Deserialize from dict
        restored = ChainRegistry.from_dict(data)
        assert restored.get("deser_chain") is not None
        assert restored.count() == 1

    def test_from_dict_with_execution_history(self):
        """Test from_dict() restores execution history (lines 221-223)."""
        from rege.orchestration.registry import ChainRegistry
        from rege.orchestration.chain import RitualChain, ChainExecution, ChainStatus
        from rege.orchestration.phase import Phase

        registry = ChainRegistry()
        phase = Phase(name="p1", organ="HEART_OF_CANON", mode="mythic")
        chain = RitualChain(name="exec_chain", phases=[phase])
        registry.register(chain)

        # Create a real execution and add to history
        execution = ChainExecution(chain_name="exec_chain")
        execution.mark_running("p1")
        execution.mark_completed()
        registry.add_execution(execution)

        data = registry.to_dict()
        restored = ChainRegistry.from_dict(data)
        assert len(restored._execution_history) == 1

    def test_set_max_history_trims_old_entries(self):
        """Test set_max_history() trims excess history (line 201)."""
        from rege.orchestration.registry import ChainRegistry
        registry = ChainRegistry()
        for i in range(5):
            exec_mock = MagicMock()
            exec_mock.chain_name = f"chain_{i}"
            registry._execution_history.append(exec_mock)
        registry.set_max_history(3)
        assert len(registry._execution_history) == 3


# ==================== OrganRegistry Tests ====================

class TestOrganRegistryMissingPaths:
    """Tests for uncovered OrganRegistry methods."""

    def _get_registry_with_handler(self):
        from rege.organs.registry import OrganRegistry
        from rege.organs.heart_of_canon import HeartOfCanon
        registry = OrganRegistry()
        handler = HeartOfCanon()
        registry.register(handler)
        return registry, handler

    def test_get_or_raise_raises_when_not_found(self):
        """Test get_or_raise() raises OrganNotFoundError (lines 73-76)."""
        from rege.organs.registry import OrganRegistry
        from rege.core.exceptions import OrganNotFoundError
        registry = OrganRegistry()
        with pytest.raises(OrganNotFoundError):
            registry.get_or_raise("NONEXISTENT_ORGAN")

    def test_list_handlers_returns_handlers(self):
        """Test list_handlers() returns list of handler instances (line 96)."""
        registry, handler = self._get_registry_with_handler()
        handlers = registry.list_handlers()
        assert len(handlers) >= 1
        assert handler in handlers

    def test_unregister_found(self):
        """Test unregister() returns True when organ found (lines 108-110)."""
        registry, handler = self._get_registry_with_handler()
        result = registry.unregister("HEART_OF_CANON")
        assert result is True
        assert registry.get("HEART_OF_CANON") is None

    def test_unregister_not_found(self):
        """Test unregister() returns False when not found (line 111)."""
        from rege.organs.registry import OrganRegistry
        registry = OrganRegistry()
        result = registry.unregister("NONEXISTENT")
        assert result is False

    def test_clear_empties_registry(self):
        """Test clear() removes all handlers (line 115)."""
        registry, handler = self._get_registry_with_handler()
        registry.clear()
        assert len(registry) == 0

    def test_get_all_states(self):
        """Test get_all_states() returns dict of organ states (line 124)."""
        registry, handler = self._get_registry_with_handler()
        states = registry.get_all_states()
        assert isinstance(states, dict)
        assert "HEART_OF_CANON" in states

    def test_restore_all_states(self):
        """Test restore_all_states() restores organ states (lines 136-139)."""
        registry, handler = self._get_registry_with_handler()
        states = registry.get_all_states()
        # Restore (even if identical state)
        registry.restore_all_states(states)
        # Should not raise

    def test_restore_all_states_unknown_organ(self):
        """Test restore_all_states() silently skips unknown organs."""
        from rege.organs.registry import OrganRegistry
        registry = OrganRegistry()
        # Pass state for non-existent organ - should not raise
        registry.restore_all_states({"NONEXISTENT": {}})


# ==================== SystemRecoveryProtocol Tests ====================

class TestRecoveryProtocolMissingPaths:
    """Tests for uncovered SystemRecoveryProtocol paths."""

    def _make_protocol(self):
        from rege.protocols.recovery import SystemRecoveryProtocol, RecoveryTrigger
        protocol = SystemRecoveryProtocol()
        # Create a checkpoint
        snapshot = protocol.capture_snapshot(
            RecoveryTrigger.MANUAL,
            {"organs": {"HEART_OF_CANON": {"charge": 50}}, "metrics": {}, "pending": [], "errors": []}
        )
        return protocol, snapshot.snapshot_id

    def test_full_rollback_checkpoint_not_found(self):
        """Test full_rollback raises CheckpointNotFound (line 110)."""
        from rege.protocols.recovery import SystemRecoveryProtocol
        from rege.core.exceptions import CheckpointNotFound
        protocol = SystemRecoveryProtocol()
        with pytest.raises(CheckpointNotFound):
            protocol.full_rollback("NONEXISTENT_CHECKPOINT", confirm=True)

    def test_full_rollback_requires_authorization(self):
        """Test full_rollback raises RecoveryAuthorizationRequired (line 116)."""
        from rege.protocols.recovery import SystemRecoveryProtocol, RecoveryTrigger
        from rege.core.exceptions import RecoveryAuthorizationRequired
        protocol = SystemRecoveryProtocol()
        # Create an old checkpoint by patching its timestamp
        snapshot = protocol.capture_snapshot(
            RecoveryTrigger.MANUAL,
            {"organs": {}, "metrics": {}, "pending": [], "errors": []}
        )
        # Make it appear old (beyond threshold)
        snapshot.timestamp = datetime.now() - timedelta(hours=25)
        with pytest.raises(RecoveryAuthorizationRequired):
            protocol.full_rollback(snapshot.snapshot_id, confirm=True)

    def test_partial_recovery_checkpoint_not_found(self):
        """Test partial_recovery raises CheckpointNotFound (line 152)."""
        from rege.protocols.recovery import SystemRecoveryProtocol
        from rege.core.exceptions import CheckpointNotFound
        protocol = SystemRecoveryProtocol()
        with pytest.raises(CheckpointNotFound):
            protocol.partial_recovery(["HEART_OF_CANON"], "NONEXISTENT")

    def test_reconstruct_data(self):
        """Test reconstruct_data method (lines 197-212)."""
        from rege.protocols.recovery import SystemRecoveryProtocol
        protocol = SystemRecoveryProtocol()
        result = protocol.reconstruct_data(
            target="fragment_001",
            sources=["ECHO_SHELL", "ARCHIVE_ORDER"]
        )
        assert result["status"] == "attempted"
        assert result["target"] == "fragment_001"
        assert "sources_searched" in result

    def test_resume_from_halt_not_halted(self):
        """Test resume_from_halt when not halted (line 260)."""
        from rege.protocols.recovery import SystemRecoveryProtocol
        protocol = SystemRecoveryProtocol()
        result = protocol.resume_from_halt()
        assert result["status"] == "not_halted"

    def test_resume_from_halt_confirmation_required(self):
        """Test resume_from_halt confirmation required (line 263)."""
        from rege.protocols.recovery import SystemRecoveryProtocol
        protocol = SystemRecoveryProtocol()
        protocol._halted = True
        result = protocol.resume_from_halt(confirm=False)
        assert result["status"] == "confirmation_required"

    def test_requires_ritual_court_returns_false(self):
        """Test requires_ritual_court returns False for non-rollback mode (line 297)."""
        from rege.protocols.recovery import SystemRecoveryProtocol, RecoveryMode
        protocol = SystemRecoveryProtocol()
        result = protocol.requires_ritual_court(RecoveryMode.PARTIAL)
        assert result is False

    def test_find_last_stable_checkpoint(self):
        """Test _find_last_stable_checkpoint with manual checkpoint (line 306)."""
        from rege.protocols.recovery import SystemRecoveryProtocol, RecoveryTrigger
        protocol = SystemRecoveryProtocol()
        snapshot = protocol.capture_snapshot(
            RecoveryTrigger.MANUAL,
            {"organs": {}, "metrics": {}, "pending": [], "errors": []}
        )
        result = protocol._find_last_stable_checkpoint()
        assert result == snapshot.snapshot_id

    def test_get_checkpoint_by_id(self):
        """Test get_checkpoint() returns checkpoint (line 322)."""
        protocol, snapshot_id = self._make_protocol()
        result = protocol.get_checkpoint(snapshot_id)
        assert result is not None
        assert result.snapshot_id == snapshot_id

    def test_get_recovery_log(self):
        """Test get_recovery_log() returns log entries (line 330)."""
        from rege.protocols.recovery import SystemRecoveryProtocol
        protocol = SystemRecoveryProtocol()
        # Execute something to create log entry
        try:
            protocol.full_rollback("NONEXISTENT", confirm=True)
        except Exception:
            pass
        log = protocol.get_recovery_log()
        assert isinstance(log, list)

    def test_create_manual_checkpoint(self):
        """Test create_manual_checkpoint (lines 347-352)."""
        from rege.protocols.recovery import SystemRecoveryProtocol
        protocol = SystemRecoveryProtocol()
        snapshot = protocol.create_manual_checkpoint(
            name="test_checkpoint",
            system_state={"organs": {}, "metrics": {}, "pending": [], "errors": []}
        )
        assert snapshot is not None
        assert snapshot.system_state.get("checkpoint_name") == "test_checkpoint"


# ==================== FusionProtocol Tests ====================

class TestFusionProtocolMissingPaths:
    """Tests for uncovered FusionProtocol paths."""

    def _make_fragments(self, charge=75, tags=None):
        from rege.core.models import Fragment
        if tags is None:
            tags = ["CANON+", "RITUAL+"]
        frags = []
        for i in range(2):
            f = Fragment(
                id=f"FRAG_TEST_{i:03d}",
                name=f"frag_{i}",
                tags=tags[:],
                charge=charge,
            )
            frags.append(f)
        return frags

    def test_check_eligibility_insufficient_overlap(self):
        """Test check_eligibility returns False for insufficient overlap (line 84)."""
        from rege.protocols.fuse01 import FusionProtocol, FusionMode
        from rege.core.models import Fragment
        protocol = FusionProtocol()
        # Fragments with no common tags - AUTO mode should fail
        f1 = Fragment(id="F001", name="f1", tags=["CANON+"], charge=80)
        f2 = Fragment(id="F002", name="f2", tags=["RITUAL+"], charge=80)
        eligible, reason = protocol.check_eligibility([f1, f2], FusionMode.AUTO)
        assert eligible is False
        assert "overlap" in reason.lower()

    def test_execute_fusion_raises_not_eligible(self):
        """Test execute_fusion raises FusionNotEligible (line 115)."""
        from rege.protocols.fuse01 import FusionProtocol, FusionMode
        from rege.core.exceptions import FusionNotEligible
        from rege.core.models import Fragment
        protocol = FusionProtocol()
        # Low charge fragments (below threshold)
        frags = [
            Fragment(id="F001", name="f1", tags=["CANON+"], charge=30),
            Fragment(id="F002", name="f2", tags=["CANON+"], charge=30),
        ]
        with pytest.raises(FusionNotEligible):
            protocol.execute_fusion(frags, FusionMode.AUTO)

    def test_rollback_fusion_not_found(self):
        """Test rollback() when fusion not found (lines 164-169)."""
        from rege.protocols.fuse01 import FusionProtocol
        protocol = FusionProtocol()
        result = protocol.rollback("NONEXISTENT_FUSE_ID")
        assert result["status"] == "failed"
        assert "not found" in result["reason"]

    def test_rollback_fusion_unavailable(self):
        """Test rollback() when rollback not available (lines 173-178)."""
        from rege.protocols.fuse01 import FusionProtocol, FusionMode
        protocol = FusionProtocol()
        frags = self._make_fragments(charge=80)
        fused = protocol.execute_fusion(frags, FusionMode.FORCED)
        fused.rollback_available = False
        result = protocol.rollback(fused.fused_id)
        assert result["status"] == "failed"
        assert "not available" in result["reason"]

    def test_rollback_window_expired(self):
        """Test rollback() when deadline passed (lines 180-185)."""
        from rege.protocols.fuse01 import FusionProtocol, FusionMode
        protocol = FusionProtocol()
        frags = self._make_fragments(charge=80)
        fused = protocol.execute_fusion(frags, FusionMode.FORCED)
        # Set deadline to past
        fused.rollback_deadline = datetime.now() - timedelta(hours=1)
        result = protocol.rollback(fused.fused_id)
        assert result["status"] == "failed"
        assert "expired" in result["reason"]

    def test_rollback_canonized_fusion(self):
        """Test rollback() when fusion is canonized (lines 188-193)."""
        from rege.protocols.fuse01 import FusionProtocol, FusionMode
        protocol = FusionProtocol()
        frags = self._make_fragments(charge=80)
        fused = protocol.execute_fusion(frags, FusionMode.FORCED)
        fused.tags.append("CANON+")
        result = protocol.rollback(fused.fused_id)
        assert result["status"] == "failed"
        assert "canonized" in result["reason"]

    def test_route_output(self):
        """Test route_output() (line 231)."""
        from rege.protocols.fuse01 import FusionProtocol, FusionMode
        protocol = FusionProtocol()
        frags = self._make_fragments(charge=80)
        fused = protocol.execute_fusion(frags, FusionMode.FORCED)
        result = protocol.route_output(fused)
        assert result["action"] == "route"
        assert "destination" in result

    def test_calculate_charge_averaged(self):
        """Test _calculate_charge with AVERAGED method (line 258)."""
        from rege.protocols.fuse01 import FusionProtocol, ChargeCalculation
        from rege.core.models import Fragment
        protocol = FusionProtocol()
        frags = [
            Fragment(id="F001", name="f1", tags=[], charge=60),
            Fragment(id="F002", name="f2", tags=[], charge=80),
        ]
        result = protocol._calculate_charge(frags, ChargeCalculation.AVERAGED)
        assert result == 70  # (60 + 80) // 2

    def test_calculate_charge_summed_capped(self):
        """Test _calculate_charge with SUMMED_CAPPED method (lines 259-260)."""
        from rege.protocols.fuse01 import FusionProtocol, ChargeCalculation
        from rege.core.models import Fragment
        protocol = FusionProtocol()
        frags = [
            Fragment(id="F001", name="f1", tags=[], charge=70),
            Fragment(id="F002", name="f2", tags=[], charge=70),
        ]
        result = protocol._calculate_charge(frags, ChargeCalculation.SUMMED_CAPPED)
        assert result == 100  # sum=140, capped at 100

    def test_calculate_charge_default(self):
        """Test _calculate_charge with unknown method falls back (line 262)."""
        from rege.protocols.fuse01 import FusionProtocol, ChargeCalculation
        from rege.core.models import Fragment
        protocol = FusionProtocol()
        frags = [
            Fragment(id="F001", name="f1", tags=[], charge=60),
            Fragment(id="F002", name="f2", tags=[], charge=80),
        ]
        # Use a value that doesn't match any case
        result = protocol._calculate_charge(frags, "unknown_method")
        assert result == 80  # falls back to max

    def test_get_rollback_log(self):
        """Test get_rollback_log() returns copy (line 295)."""
        from rege.protocols.fuse01 import FusionProtocol, FusionMode
        from rege.core.models import Fragment
        protocol = FusionProtocol()
        # Use fragments without CANON+ so rollback can succeed
        frags = [
            Fragment(id="F001", name="f1", tags=["RITUAL+", "ECHO+"], charge=80),
            Fragment(id="F002", name="f2", tags=["RITUAL+", "ECHO+"], charge=80),
        ]
        fused = protocol.execute_fusion(frags, FusionMode.FORCED)
        result = protocol.rollback(fused.fused_id)
        assert result["status"] == "rolled_back"
        log = protocol.get_rollback_log()
        assert isinstance(log, list)
        assert len(log) == 1

    def test_get_eligible_fragments_from_rollback(self):
        """Test get_eligible_fragments() from rolled-back fusions (lines 309-313)."""
        from rege.protocols.fuse01 import FusionProtocol, FusionMode
        from rege.core.models import Fragment
        protocol = FusionProtocol()
        # Use fragments without CANON+ so rollback succeeds
        frags = [
            Fragment(id="F001", name="f1", tags=["RITUAL+", "ECHO+"], charge=80),
            Fragment(id="F002", name="f2", tags=["RITUAL+", "ECHO+"], charge=80),
        ]
        fused = protocol.execute_fusion(frags, FusionMode.FORCED)
        protocol.rollback(fused.fused_id)
        eligible = protocol.get_eligible_fragments()
        # Rolled-back fragments with high charge should be eligible
        assert isinstance(eligible, list)
        assert len(eligible) >= 2
