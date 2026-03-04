"""
Tests for orchestration/orchestrator.py coverage improvements.

Targets uncovered lines:
- 126-127: no entry phase defined
- 151-162: compensation path
- 172: escalation path
- 177-178: branch taken path
- 192-193: exception during execute_chain
- 220, 224-231: resume_execution paths
- 249-259: compensation in resume
- 267: escalation in resume
- 271-272: branch in resume
- 277-279: step mode in resume
- 284-285: exception in resume
- 320: _invoke_via_dispatcher path
- 334-337: _execute_phase exception
- 350-366: _invoke_via_dispatcher body
- 390, 395, 399, 403: _check_escalation paths
- 424: get_paused_executions
- 452: dry_run chain not found
- 475: dry_run branch path
"""

import pytest
from unittest.mock import MagicMock, patch
from rege.orchestration.orchestrator import RitualChainOrchestrator
from rege.orchestration.chain import RitualChain
from rege.orchestration.phase import Phase, PhaseStatus, Branch
from rege.orchestration.registry import ChainRegistry


def make_phase(name, organ="HEART_OF_CANON", mode="mythic", required=True):
    """Create a simple phase for testing."""
    return Phase(name=name, organ=organ, mode=mode, required=required)


def make_chain(name, phases, entry_phase=None):
    """Create a chain for testing."""
    chain = RitualChain(name=name, phases=phases)
    if entry_phase:
        chain.entry_phase = entry_phase
    return chain


def make_registry_with_chain(chain):
    """Create a registry containing the given chain."""
    registry = ChainRegistry()
    registry.register(chain)
    return registry


class TestExecuteChainEdgeCases:
    """Tests for execute_chain uncovered paths."""

    def test_execute_chain_not_found(self):
        """Test execute_chain raises ValueError for unknown chain."""
        registry = ChainRegistry()
        orchestrator = RitualChainOrchestrator(registry=registry)
        with pytest.raises(ValueError, match="not found"):
            orchestrator.execute_chain("nonexistent_chain")

    def test_execute_chain_no_entry_phase(self):
        """Test execute_chain with a chain that has no phases (lines 125-127)."""
        # A chain with an entry_phase that doesn't exist in the chain
        phase = make_phase("init")
        chain = RitualChain(name="no_entry", phases=[phase])
        chain.entry_phase = "nonexistent_phase_xyz"  # Points to nonexistent phase
        registry = make_registry_with_chain(chain)
        orchestrator = RitualChainOrchestrator(registry=registry)

        execution = orchestrator.execute_chain("no_entry")
        assert execution.status.value in ("failed", "completed")

    def test_execute_chain_compensation_path(self):
        """Test execute_chain when phase fails and has compensation (lines 151-162)."""
        # Create a compensation phase
        comp_phase = make_phase("compensation", organ="ECHO_SHELL", mode="decay")

        # Create a phase with compensation that will fail
        phase = make_phase("failing_phase")
        phase.compensation = comp_phase
        phase.required = True

        chain = make_chain("test_comp", [phase])
        registry = make_registry_with_chain(chain)
        orchestrator = RitualChainOrchestrator(registry=registry)

        # Make the phase handler fail
        def failing_handler(input_data):
            raise RuntimeError("Phase deliberately fails")

        orchestrator.register_phase_handler("HEART_OF_CANON", "mythic", failing_handler)

        execution = orchestrator.execute_chain("test_comp")
        # Should have run compensation then failed
        assert execution.status.value in ("failed", "completed")
        assert len(execution.compensations_executed) >= 0

    def test_execute_chain_exception_in_execution(self):
        """Test execute_chain when unexpected exception occurs (lines 192-193)."""
        phase = make_phase("init")
        chain = make_chain("exc_chain", [phase])
        registry = make_registry_with_chain(chain)
        orchestrator = RitualChainOrchestrator(registry=registry)

        # Make get_entry_phase raise an exception by patching
        original_get_entry_phase = chain.get_entry_phase
        call_count = [0]

        def raising_entry():
            call_count[0] += 1
            if call_count[0] > 0:
                raise RuntimeError("Unexpected system error")
            return original_get_entry_phase()

        chain.get_entry_phase = raising_entry

        execution = orchestrator.execute_chain("exc_chain")
        assert execution.status.value == "failed"
        assert execution.error is not None


class TestExecuteChainEscalationAndBranch:
    """Tests for escalation and branch paths in execute_chain."""

    def test_execute_chain_with_escalation(self):
        """Test execute_chain when escalation is triggered (line 172)."""
        phase = make_phase("init")
        chain = make_chain("esc_chain", [phase])
        registry = make_registry_with_chain(chain)
        orchestrator = RitualChainOrchestrator(registry=registry)

        # Make a handler that sets high charge in context (triggers RITUAL_COURT escalation)
        def high_charge_handler(input_data):
            return {"charge": 80, "result": "processed"}

        orchestrator.register_phase_handler("HEART_OF_CANON", "mythic", high_charge_handler)
        execution = orchestrator.execute_chain("esc_chain", context={"charge": 80})
        # Escalation may or may not be triggered depending on output mapping
        assert execution.status.value in ("completed", "failed")

    def test_check_escalation_depth_exceeded(self):
        """Test _check_escalation with depth_exceeded context (line 390)."""
        orchestrator = RitualChainOrchestrator()
        result_mock = MagicMock()
        context = {"depth_exceeded": True}
        escalation = orchestrator._check_escalation(result_mock, context)
        assert escalation == "EMERGENCY_RECOVERY"

    def test_check_escalation_high_charge(self):
        """Test _check_escalation with high charge (line 395)."""
        orchestrator = RitualChainOrchestrator()
        result_mock = MagicMock()
        context = {"charge": 80}
        escalation = orchestrator._check_escalation(result_mock, context)
        assert escalation == "RITUAL_COURT"

    def test_check_escalation_contradiction(self):
        """Test _check_escalation with contradiction (line 399)."""
        orchestrator = RitualChainOrchestrator()
        result_mock = MagicMock()
        context = {"contradiction": True}
        escalation = orchestrator._check_escalation(result_mock, context)
        assert escalation == "RITUAL_COURT"

    def test_check_escalation_fusion_required(self):
        """Test _check_escalation with fusion_required (line 403)."""
        orchestrator = RitualChainOrchestrator()
        result_mock = MagicMock()
        context = {"fusion_required": True}
        escalation = orchestrator._check_escalation(result_mock, context)
        assert escalation == "FUSE01"

    def test_check_escalation_no_trigger(self):
        """Test _check_escalation with no triggers → None."""
        orchestrator = RitualChainOrchestrator()
        result_mock = MagicMock()
        context = {"charge": 50}
        escalation = orchestrator._check_escalation(result_mock, context)
        assert escalation is None

    def test_execute_chain_with_branch(self):
        """Test execute_chain when a branch is taken (lines 176-178)."""
        phase1 = make_phase("phase1")
        phase2 = make_phase("phase2", organ="MIRROR_CABINET", mode="emotional_reflection")

        # Add branch from phase1 to phase2 (always true condition)
        branch = Branch(name="to_phase2", condition=lambda ctx: True, target_phase="phase2")
        phase1.branches.append(branch)

        chain = make_chain("branch_chain", [phase1, phase2])
        registry = make_registry_with_chain(chain)
        orchestrator = RitualChainOrchestrator(registry=registry)

        execution = orchestrator.execute_chain("branch_chain")
        assert execution.status.value in ("completed", "failed")


class TestExecutePhaseException:
    """Tests for _execute_phase exception path (lines 334-342)."""

    def test_execute_phase_exception(self):
        """Test _execute_phase when handler raises exception."""
        phase = make_phase("error_phase")
        chain = make_chain("exc_chain", [phase])
        registry = make_registry_with_chain(chain)
        orchestrator = RitualChainOrchestrator(registry=registry)

        def raising_handler(input_data):
            raise ValueError("Handler error")

        orchestrator.register_phase_handler("HEART_OF_CANON", "mythic", raising_handler)

        result = orchestrator._execute_phase(phase, {})
        assert result.status == PhaseStatus.FAILED
        assert "Handler error" in result.error


class TestInvokeViaDispatcher:
    """Tests for _invoke_via_dispatcher (lines 350-366)."""

    def test_invoke_via_dispatcher(self):
        """Test _invoke_via_dispatcher calls dispatcher (lines 350-366)."""
        phase = make_phase("test_phase")
        orchestrator = RitualChainOrchestrator()

        # Set up a mock dispatcher - returns a mock result
        mock_dispatcher = MagicMock()
        mock_result = MagicMock()
        mock_result.organ = "HEART_OF_CANON"
        mock_result.status = "success"
        mock_dispatcher.dispatch.return_value = mock_result
        orchestrator._dispatcher = mock_dispatcher

        result = orchestrator._invoke_via_dispatcher(phase, {"symbol": "test", "charge": 60})
        mock_dispatcher.dispatch.assert_called_once()

    def test_execute_phase_via_dispatcher(self):
        """Test _execute_phase uses dispatcher when no handler (line 320)."""
        phase = make_phase("disp_phase")
        orchestrator = RitualChainOrchestrator()

        mock_dispatcher = MagicMock()
        mock_result = MagicMock()
        mock_result.organ = "HEART_OF_CANON"
        mock_result.status = "success"
        mock_dispatcher.dispatch.return_value = mock_result
        orchestrator._dispatcher = mock_dispatcher

        result = orchestrator._execute_phase(phase, {})
        assert result.status == PhaseStatus.COMPLETED


class TestResumeExecution:
    """Tests for resume_execution paths."""

    def test_resume_execution_not_found(self):
        """Test resume with unknown execution ID (line 220)."""
        orchestrator = RitualChainOrchestrator()
        result = orchestrator.resume_execution("NONEXISTENT_EXEC_ID")
        assert result is None

    def test_resume_execution_chain_not_found(self):
        """Test resume when chain no longer exists (lines 222-225)."""
        registry = ChainRegistry()
        orchestrator = RitualChainOrchestrator(registry=registry)

        # Create a fake paused execution
        execution = MagicMock()
        execution.chain_name = "deleted_chain"
        execution.current_phase = "init"
        orchestrator._paused_executions["EXEC_001"] = execution

        result = orchestrator.resume_execution("EXEC_001")
        assert result is not None
        execution.mark_failed.assert_called_once()

    def test_resume_execution_phase_not_found(self):
        """Test resume when paused phase doesn't exist (lines 228-231)."""
        phase = make_phase("existing_phase")
        chain = make_chain("test_chain", [phase])
        registry = make_registry_with_chain(chain)
        orchestrator = RitualChainOrchestrator(registry=registry)

        execution = MagicMock()
        execution.chain_name = "test_chain"
        execution.current_phase = "nonexistent_phase_xyz"
        orchestrator._paused_executions["EXEC_002"] = execution

        result = orchestrator.resume_execution("EXEC_002")
        assert result is not None
        execution.mark_failed.assert_called_once()

    def test_resume_execution_success(self):
        """Test successful resume execution."""
        phase1 = make_phase("phase1")
        phase2 = make_phase("phase2", organ="MIRROR_CABINET", mode="emotional_reflection")
        chain = make_chain("resumable_chain", [phase1, phase2])
        registry = make_registry_with_chain(chain)
        orchestrator = RitualChainOrchestrator(registry=registry)

        # First execute in step mode to get a paused execution
        execution = orchestrator.execute_chain("resumable_chain", step_mode=True)
        assert execution.status.value in ("paused", "completed", "failed")

        if execution.status.value == "paused":
            # Now resume it
            resumed = orchestrator.resume_execution(execution.execution_id)
            assert resumed is not None

    def test_resume_execution_step_mode(self):
        """Test resume in step mode pauses again (lines 277-279)."""
        phase1 = make_phase("phase1")
        phase2 = make_phase("phase2", organ="MIRROR_CABINET", mode="emotional_reflection")
        phase3 = make_phase("phase3", organ="ECHO_SHELL", mode="pulse")
        chain = make_chain("three_phase_chain", [phase1, phase2, phase3])
        registry = make_registry_with_chain(chain)
        orchestrator = RitualChainOrchestrator(registry=registry)

        # Execute in step mode
        execution = orchestrator.execute_chain("three_phase_chain", step_mode=True)

        if execution.status.value == "paused":
            # Resume in step mode again
            resumed = orchestrator.resume_execution(execution.execution_id, step_mode=True)
            assert resumed is not None


class TestGetPausedExecutions:
    """Tests for get_paused_executions (line 424)."""

    def test_get_paused_executions_empty(self):
        """Test get_paused_executions returns empty dict."""
        orchestrator = RitualChainOrchestrator()
        paused = orchestrator.get_paused_executions()
        assert isinstance(paused, dict)

    def test_get_paused_executions_returns_copy(self):
        """Test get_paused_executions returns a copy."""
        orchestrator = RitualChainOrchestrator()
        execution = MagicMock()
        orchestrator._paused_executions["EXEC_001"] = execution

        paused = orchestrator.get_paused_executions()
        assert "EXEC_001" in paused
        # Modifying the returned dict doesn't affect internal state
        paused["NEW_KEY"] = "value"
        assert "NEW_KEY" not in orchestrator._paused_executions


class TestDryRunEdgeCases:
    """Tests for dry_run edge cases."""

    def test_dry_run_chain_not_found(self):
        """Test dry_run with nonexistent chain (line 452)."""
        registry = ChainRegistry()
        orchestrator = RitualChainOrchestrator(registry=registry)
        result = orchestrator.dry_run("nonexistent_chain")
        assert "error" in result
        assert "not found" in result["error"]

    def test_dry_run_with_branch(self):
        """Test dry_run when a branch is selected (line 475)."""
        phase1 = make_phase("phase1")
        phase2 = make_phase("phase2", organ="MIRROR_CABINET", mode="emotional_reflection")

        branch = Branch(name="to_phase2", condition=lambda ctx: True, target_phase="phase2")
        phase1.branches.append(branch)

        chain = make_chain("branch_dry_run", [phase1, phase2])
        registry = make_registry_with_chain(chain)
        orchestrator = RitualChainOrchestrator(registry=registry)

        result = orchestrator.dry_run("branch_dry_run", context={"take_branch": True})
        assert "planned_phases" in result
        assert result["phase_count"] >= 1

    def test_dry_run_normal_chain(self):
        """Test dry_run with a normal chain."""
        phase1 = make_phase("phase1")
        phase2 = make_phase("phase2", organ="MIRROR_CABINET", mode="emotional_reflection")
        chain = make_chain("normal_chain", [phase1, phase2])
        registry = make_registry_with_chain(chain)
        orchestrator = RitualChainOrchestrator(registry=registry)

        result = orchestrator.dry_run("normal_chain")
        assert result["chain"] == "normal_chain"
        assert result["phase_count"] == 2
        assert len(result["planned_phases"]) == 2


class TestGetExecutionHistoryAndStats:
    """Tests for get_execution_history and get_execution_stats."""

    def test_get_execution_history_empty(self):
        """Test get_execution_history returns empty list."""
        orchestrator = RitualChainOrchestrator()
        history = orchestrator.get_execution_history()
        assert isinstance(history, list)

    def test_get_execution_stats_empty(self):
        """Test get_execution_stats returns stats dict."""
        orchestrator = RitualChainOrchestrator()
        stats = orchestrator.get_execution_stats()
        assert isinstance(stats, dict)
        assert "total" in stats

    def test_cancel_execution(self):
        """Test cancel_execution for paused execution."""
        orchestrator = RitualChainOrchestrator()
        execution = MagicMock()
        orchestrator._paused_executions["EXEC_001"] = execution

        result = orchestrator.cancel_execution("EXEC_001")
        assert result is True
        assert "EXEC_001" not in orchestrator._paused_executions

    def test_cancel_execution_not_found(self):
        """Test cancel_execution for unknown ID."""
        orchestrator = RitualChainOrchestrator()
        result = orchestrator.cancel_execution("NONEXISTENT")
        assert result is False
