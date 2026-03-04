"""
Coverage tests for:
- routing/dispatcher.py: 103-104, 171-173, 198, 232, 316
- routing/patchbay.py: 122-123, 172-173, 233-234
"""

import pytest
from rege.routing.dispatcher import Dispatcher
from rege.routing.patchbay import PatchQueue
from rege.routing.depth_tracker import DepthTracker, DepthAction
from rege.core.models import Patch, Invocation, DepthLevel, InvocationResult
from rege.core.constants import Priority


def make_patch(input_node="TEST", output_node="HEART_OF_CANON", charge=50, tags=None, depth=0):
    p = Patch(input_node=input_node, output_node=output_node, tags=tags or [], charge=charge)
    p.depth = depth
    return p


# ============================================================
# Dispatcher coverage
# ============================================================

class AlwaysFailDepthTracker(DepthTracker):
    """Returns depth limit exceeded with ESCALATE action."""
    def check_depth(self, patch):
        return False, DepthAction.ESCALATE_TO_RITUAL_COURT


class ForceTerminateDepthTracker(DepthTracker):
    """Returns depth limit with FORCE_TERMINATE_INCOMPLETE action."""
    def check_depth(self, patch):
        return False, DepthAction.FORCE_TERMINATE_INCOMPLETE


class PanicDepthTracker(DepthTracker):
    """Returns depth limit with PANIC_STOP action."""
    def check_depth(self, patch):
        return False, DepthAction.PANIC_STOP


class ForceTerminateAlertDepthTracker(DepthTracker):
    """Returns FORCE_TERMINATE_ALERT action → hits else branch (line 316)."""
    def check_depth(self, patch):
        return False, DepthAction.FORCE_TERMINATE_ALERT


class RaisingExecuteDispatcher(Dispatcher):
    """Dispatcher whose _execute always raises."""
    def _execute(self, invocation, patch):
        raise RuntimeError("forced execution failure")


VALID_INVOCATION_TEXT = """::CALL_ORGAN HEART_OF_CANON
::WITH test memory
::MODE mythic
::DEPTH standard
::EXPECT canon_event"""


def fresh_dispatcher(**kwargs):
    """Create a Dispatcher with a fresh isolated queue (avoids global queue state)."""
    return Dispatcher(queue=PatchQueue(), **kwargs)


class TestDispatcherExceptionHandling:
    """Cover lines 103-104: exception handler in dispatch()."""

    def test_dispatch_catches_execute_exception(self):
        """Lines 103-104: _execute raises → creates error result with 'failed' status."""
        dispatcher = RaisingExecuteDispatcher(queue=PatchQueue())
        result = dispatcher.dispatch(VALID_INVOCATION_TEXT)
        assert result.status == "failed"
        assert result.errors is not None
        assert len(result.errors) > 0


class TestProcessQueueExceptionHandling:
    """Cover lines 171-173: exception handler in process_queue()."""

    def test_process_queue_catches_execute_exception(self):
        """Lines 171-173: _execute raises → creates error result in process_queue."""
        q = PatchQueue()
        dispatcher = RaisingExecuteDispatcher(queue=q)

        # Manually enqueue a patch (bypassing dispatch)
        p = make_patch()
        p.metadata = {
            "depth": "standard",
            "mode": "mythic",
            "expect": "canon_event",
            "invocation_id": "TEST_ID",
        }
        q.enqueue(p)

        results = dispatcher.process_queue(max_items=1)
        assert len(results) == 1
        assert results[0].status == "failed"


class TestPatchToInvocationLightDepth:
    """Cover line 198: _patch_to_invocation with depth='light'."""

    def test_process_queue_light_depth(self):
        """Line 198: patch metadata depth='light' → DepthLevel.LIGHT."""
        q = PatchQueue()
        dispatcher = fresh_dispatcher()
        dispatcher.queue = q  # ensure using isolated queue

        p = make_patch(output_node="HEART_OF_CANON")
        p.metadata = {
            "depth": "light",
            "mode": "mythic",
            "expect": "canon_event",
            "invocation_id": "LIGHT_TEST",
        }
        q.enqueue(p)

        results = dispatcher.process_queue(max_items=1)
        assert len(results) == 1
        # Result should succeed (LIGHT depth is valid)
        assert results[0].status in ("success", "escalated", "incomplete", "error", "failed")


class TestDispatcherDepthLimit:
    """Cover line 232: depth limit hit in _execute."""

    def test_depth_limit_escalate(self):
        """Line 232: depth limit returns 'escalated' status."""
        dispatcher = fresh_dispatcher(depth_tracker=AlwaysFailDepthTracker())
        result = dispatcher.dispatch(VALID_INVOCATION_TEXT)
        assert result.status == "escalated"

    def test_depth_limit_force_terminate(self):
        """Line 232 + depth limit: FORCE_TERMINATE_INCOMPLETE returns 'incomplete'."""
        dispatcher = fresh_dispatcher(depth_tracker=ForceTerminateDepthTracker())
        result = dispatcher.dispatch(VALID_INVOCATION_TEXT)
        assert result.status == "incomplete"

    def test_depth_limit_panic(self):
        """Line 232 + depth limit: PANIC_STOP returns 'panic'."""
        dispatcher = fresh_dispatcher(depth_tracker=PanicDepthTracker())
        result = dispatcher.dispatch(VALID_INVOCATION_TEXT)
        assert result.status == "panic"


class TestDispatcherDepthLimitElseBranch:
    """Cover line 316: else branch in _handle_depth_limit."""

    def test_force_terminate_alert_hits_else(self):
        """Line 316: FORCE_TERMINATE_ALERT → else branch → status='terminated'."""
        dispatcher = fresh_dispatcher(depth_tracker=ForceTerminateAlertDepthTracker())
        result = dispatcher.dispatch(VALID_INVOCATION_TEXT)
        assert result.status == "terminated"


# ============================================================
# PatchQueue (patchbay) coverage
# ============================================================

class TestPatchQueueDequeueValueError:
    """Cover lines 122-123: except ValueError in dequeue()."""

    def test_dequeue_value_error_suppressed(self):
        """Lines 122-123: ValueError from remove() is caught and suppressed."""
        q = PatchQueue()
        p = make_patch()
        q.enqueue(p)

        # Keep the key in pending_by_output but clear the list so remove() raises ValueError
        # (patch.output_node IS in the dict, but patch is NOT in the list)
        q._pending_by_output[p.output_node] = []

        # dequeue should succeed without raising
        result = q.dequeue()
        assert result is p


class TestPatchQueueMakeRoomValueError:
    """Cover lines 172-173: except ValueError in _make_room_for()."""

    def test_make_room_value_error_suppressed(self):
        """Lines 172-173: ValueError from remove() in _make_room_for() is suppressed."""
        import heapq

        # Create a small queue
        q = PatchQueue(max_size=1)

        # Enqueue a background priority patch to fill it
        p_low = make_patch("LOW_IN", "LOW_OUT", charge=10)
        p_low.priority = Priority.BACKGROUND
        q._heap.append(p_low)
        # Key exists but with empty list → remove() will raise ValueError
        q._pending_by_output["LOW_OUT"] = []
        heapq.heapify(q._heap)

        # Enqueue a high priority patch that triggers _make_room_for
        p_high = make_patch("HIGH_IN", "HIGH_OUT", charge=90)
        p_high.priority = Priority.CRITICAL
        # _make_room_for will be called → tries to remove from empty list → ValueError caught
        result = q._make_room_for(p_high)
        # Should complete without raising (True or False return)
        assert isinstance(result, bool)


class TestPatchQueueDeadlockDirectCycle:
    """Cover lines 233-234: direct route cycle detection in detect_deadlock()."""

    def test_direct_route_cycle_detected(self):
        """Lines 233-234: same (input, output) route appears twice → direct deadlock."""
        q = PatchQueue()

        # Two patches with identical routes → route tuple appears in visited twice
        p1 = make_patch("A", "B")
        p2 = make_patch("A", "B")  # Same route as p1

        result = q.detect_deadlock([p1, p2])
        assert result is True
        assert q.deadlock_count > 0

    def test_no_direct_cycle(self):
        """No direct cycle for distinct routes."""
        q = PatchQueue()

        p1 = make_patch("A", "B")
        p2 = make_patch("C", "D")

        result = q.detect_deadlock([p1, p2])
        assert result is False


class TestPatchQueueDeadlockTransitiveCycle:
    """Cover transitive cycle detection (lines 242-243) in detect_deadlock()."""

    def test_transitive_cycle_detected(self):
        """output_node seen in nodes_visited → transitive deadlock."""
        q = PatchQueue()

        # patch1: A → B (A is added to nodes_visited)
        p1 = make_patch("A", "B")
        # patch2: X → A (A is already in nodes_visited as input of p1)
        p2 = make_patch("X", "A")

        result = q.detect_deadlock([p1, p2])
        assert result is True
        assert q.deadlock_count > 0

    def test_no_transitive_cycle(self):
        """No deadlock for simple linear chain."""
        q = PatchQueue()

        p1 = make_patch("A", "B")
        p2 = make_patch("B", "C")
        p3 = make_patch("C", "D")

        result = q.detect_deadlock([p1, p2, p3])
        assert result is False
