"""
RE:GE Orchestration - RitualChainOrchestrator.

The main orchestrator for executing ritual chains.
"""

from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from rege.orchestration.phase import Phase, PhaseResult, PhaseStatus
from rege.orchestration.chain import RitualChain, ChainExecution, ChainStatus
from rege.orchestration.registry import ChainRegistry, get_chain_registry


class RitualChainOrchestrator:
    """
    Orchestrator for executing ritual chains.

    Handles phase execution, branching, escalation, and compensation.
    """

    # Escalation triggers
    ESCALATION_TRIGGERS = {
        "depth_limit_exceeded": "EMERGENCY_RECOVERY",
        "canon_candidate": "RITUAL_COURT",
        "contradiction_detected": "RITUAL_COURT",
        "fusion_required": "FUSE01",
        "recovery_needed": "RECOVERY",
    }

    def __init__(
        self,
        registry: Optional[ChainRegistry] = None,
        dispatcher: Optional[Any] = None,
    ):
        """
        Initialize the orchestrator.

        Args:
            registry: Chain registry (uses global if not provided)
            dispatcher: Dispatcher for invoking organs (optional)
        """
        self._registry = registry or get_chain_registry()
        self._dispatcher = dispatcher
        self._phase_handlers: Dict[str, Callable] = {}
        self._current_execution: Optional[ChainExecution] = None
        self._paused_executions: Dict[str, ChainExecution] = {}

    def define_chain(self, name: str, phases: List[Phase]) -> RitualChain:
        """
        Define and register a new chain.

        Args:
            name: Chain name
            phases: List of phases

        Returns:
            The created chain
        """
        chain = RitualChain(name=name)
        for phase in phases:
            chain.add_phase(phase)

        self._registry.register(chain)
        return chain

    def get_chain(self, name: str) -> Optional[RitualChain]:
        """Get a chain by name."""
        return self._registry.get(name)

    def list_chains(self) -> List[str]:
        """List all registered chains."""
        return self._registry.list_chains()

    def register_phase_handler(
        self,
        organ: str,
        mode: str,
        handler: Callable[[Dict[str, Any]], Dict[str, Any]],
    ) -> None:
        """
        Register a custom handler for an organ/mode combination.

        Args:
            organ: Organ name
            mode: Mode name
            handler: Callable that takes context and returns result
        """
        key = f"{organ}:{mode}"
        self._phase_handlers[key] = handler

    def execute_chain(
        self,
        name: str,
        context: Optional[Dict[str, Any]] = None,
        step_mode: bool = False,
    ) -> ChainExecution:
        """
        Execute a ritual chain.

        Args:
            name: Chain name
            context: Initial context for the chain
            step_mode: If True, pause after each phase

        Returns:
            ChainExecution with results
        """
        chain = self._registry.get(name)
        if not chain:
            raise ValueError(f"Chain '{name}' not found")

        # Create execution tracker
        execution = ChainExecution(
            chain_name=name,
            context=context.copy() if context else {},
        )

        self._current_execution = execution
        execution.mark_running(chain.entry_phase or chain.phases[0].name)

        try:
            # Get entry phase
            current_phase = chain.get_entry_phase()
            if not current_phase:
                execution.mark_failed("No entry phase defined")
                return execution

            # Execute phases
            while current_phase:
                execution.mark_running(current_phase.name)

                # Check phase condition
                if not current_phase.should_execute(execution.context):
                    result = PhaseResult(
                        phase_name=current_phase.name,
                        status=PhaseStatus.SKIPPED,
                    )
                    execution.add_phase_result(result)

                    # Move to next phase
                    current_phase = chain.get_next_phase(current_phase.name)
                    continue

                # Execute the phase
                result = self._execute_phase(current_phase, execution.context)
                execution.add_phase_result(result)

                # Handle failure
                if result.status == PhaseStatus.FAILED:
                    if current_phase.compensation:
                        # Execute compensation
                        execution.mark_compensating()
                        comp_result = self._execute_phase(
                            current_phase.compensation, execution.context
                        )
                        execution.add_phase_result(comp_result)
                        execution.add_compensation(current_phase.name)

                    if current_phase.required:
                        execution.mark_failed(result.error or "Phase failed")
                        break

                # Update context with output
                if result.output:
                    mapped_output = current_phase.map_output(result.output)
                    execution.context.update(mapped_output)

                # Check for escalation
                escalation = self._check_escalation(result, execution.context)
                if escalation:
                    execution.add_escalation(escalation)

                # Select branch or next phase
                branch = current_phase.select_branch(execution.context)
                if branch:
                    result.branch_taken = branch.name
                    current_phase = chain.get_phase(branch.target_phase)
                else:
                    current_phase = chain.get_next_phase(current_phase.name)

                # Pause in step mode
                if step_mode and current_phase:
                    execution.mark_paused()
                    self._paused_executions[execution.execution_id] = execution
                    break

            # Mark completed if not paused or failed
            if execution.status == ChainStatus.RUNNING:
                execution.mark_completed()

        except Exception as e:
            execution.mark_failed(str(e))

        finally:
            self._current_execution = None

        # Record in history
        self._registry.add_execution(execution)

        return execution

    def resume_execution(
        self,
        execution_id: str,
        step_mode: bool = False,
    ) -> Optional[ChainExecution]:
        """
        Resume a paused execution.

        Args:
            execution_id: ID of the paused execution
            step_mode: Continue in step mode

        Returns:
            The resumed execution, or None if not found
        """
        execution = self._paused_executions.get(execution_id)
        if not execution:
            return None

        chain = self._registry.get(execution.chain_name)
        if not chain:
            execution.mark_failed("Chain no longer exists")
            return execution

        # Get the phase we paused at
        paused_phase = chain.get_phase(execution.current_phase)
        if not paused_phase:
            execution.mark_failed("Current phase not found")
            return execution

        # Continue execution from the NEXT phase (we already completed the paused phase)
        del self._paused_executions[execution_id]
        self._current_execution = execution

        # Move to next phase since we completed the current one before pausing
        current_phase = chain.get_next_phase(paused_phase.name)

        try:
            while current_phase:
                execution.mark_running(current_phase.name)

                # Execute phase
                result = self._execute_phase(current_phase, execution.context)
                execution.add_phase_result(result)

                if result.status == PhaseStatus.FAILED:
                    if current_phase.compensation:
                        execution.mark_compensating()
                        comp_result = self._execute_phase(
                            current_phase.compensation, execution.context
                        )
                        execution.add_phase_result(comp_result)
                        execution.add_compensation(current_phase.name)

                    if current_phase.required:
                        execution.mark_failed(result.error or "Phase failed")
                        break

                if result.output:
                    mapped_output = current_phase.map_output(result.output)
                    execution.context.update(mapped_output)

                escalation = self._check_escalation(result, execution.context)
                if escalation:
                    execution.add_escalation(escalation)

                branch = current_phase.select_branch(execution.context)
                if branch:
                    result.branch_taken = branch.name
                    current_phase = chain.get_phase(branch.target_phase)
                else:
                    current_phase = chain.get_next_phase(current_phase.name)

                if step_mode and current_phase:
                    execution.mark_paused()
                    self._paused_executions[execution_id] = execution
                    break

            if execution.status == ChainStatus.RUNNING:
                execution.mark_completed()

        except Exception as e:
            execution.mark_failed(str(e))

        finally:
            self._current_execution = None

        return execution

    def _execute_phase(
        self,
        phase: Phase,
        context: Dict[str, Any],
    ) -> PhaseResult:
        """
        Execute a single phase.

        Args:
            phase: Phase to execute
            context: Current execution context

        Returns:
            PhaseResult with outcome
        """
        start_time = datetime.now()

        try:
            # Get input for phase
            phase_input = phase.get_input(context)

            # Check for custom handler
            handler_key = f"{phase.organ}:{phase.mode}"
            if handler_key in self._phase_handlers:
                handler = self._phase_handlers[handler_key]
                output = handler(phase_input)
            elif self._dispatcher:
                # Use dispatcher
                output = self._invoke_via_dispatcher(phase, phase_input)
            else:
                # Mock execution for testing
                output = self._mock_execute(phase, phase_input)

            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            return PhaseResult(
                phase_name=phase.name,
                status=PhaseStatus.COMPLETED,
                output=output,
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            return PhaseResult(
                phase_name=phase.name,
                status=PhaseStatus.FAILED,
                error=str(e),
                duration_ms=duration_ms,
            )

    def _invoke_via_dispatcher(
        self,
        phase: Phase,
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Invoke an organ via the dispatcher."""
        from rege.core.models import Invocation, DepthLevel
        from rege.parser.invocation_parser import InvocationParser

        # Build invocation
        invocation = Invocation(
            organ=phase.organ,
            mode=phase.mode,
            symbol=input_data.get("symbol", ""),
            depth=DepthLevel.STANDARD,
            expect=input_data.get("expect", ""),
            flags=input_data.get("flags", []),
            charge=input_data.get("charge", 50),
        )

        # Execute via dispatcher
        result = self._dispatcher.dispatch(invocation)

        return result

    def _mock_execute(
        self,
        phase: Phase,
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Mock execution for testing."""
        return {
            "phase": phase.name,
            "organ": phase.organ,
            "mode": phase.mode,
            "input": input_data,
            "status": "mock_completed",
        }

    def _check_escalation(
        self,
        result: PhaseResult,
        context: Dict[str, Any],
    ) -> Optional[str]:
        """Check if an escalation should be triggered."""
        # Check depth limit
        if context.get("depth_exceeded"):
            return "EMERGENCY_RECOVERY"

        # Check for canon candidate
        charge = context.get("charge", 50)
        if charge >= 71:
            return "RITUAL_COURT"

        # Check for contradiction
        if context.get("contradiction"):
            return "RITUAL_COURT"

        # Check for fusion trigger
        if context.get("fusion_required"):
            return "FUSE01"

        return None

    def get_execution_history(
        self,
        chain_name: Optional[str] = None,
        limit: int = 100,
    ) -> List[ChainExecution]:
        """Get execution history."""
        return self._registry.get_executions(chain_name, limit)

    def get_execution_stats(
        self,
        chain_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get execution statistics."""
        return self._registry.get_execution_stats(chain_name)

    def get_paused_executions(self) -> Dict[str, ChainExecution]:
        """Get all paused executions."""
        return self._paused_executions.copy()

    def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a paused execution."""
        if execution_id in self._paused_executions:
            execution = self._paused_executions[execution_id]
            execution.mark_failed("Cancelled by user")
            del self._paused_executions[execution_id]
            return True
        return False

    def dry_run(
        self,
        name: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Perform a dry run of a chain without execution.

        Args:
            name: Chain name
            context: Initial context

        Returns:
            Dictionary with planned execution path
        """
        chain = self._registry.get(name)
        if not chain:
            return {"error": f"Chain '{name}' not found"}

        context = context or {}
        planned_phases = []
        current_phase = chain.get_entry_phase()

        visited = set()
        while current_phase and current_phase.name not in visited:
            visited.add(current_phase.name)

            would_execute = current_phase.should_execute(context)
            branch = current_phase.select_branch(context) if would_execute else None

            planned_phases.append({
                "name": current_phase.name,
                "organ": current_phase.organ,
                "mode": current_phase.mode,
                "would_execute": would_execute,
                "has_compensation": current_phase.compensation is not None,
                "branch_selected": branch.name if branch else None,
            })

            if branch:
                current_phase = chain.get_phase(branch.target_phase)
            else:
                current_phase = chain.get_next_phase(current_phase.name)

        return {
            "chain": name,
            "planned_phases": planned_phases,
            "phase_count": len(planned_phases),
        }
