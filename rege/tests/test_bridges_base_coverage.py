"""
Coverage tests for:
- bridges/base.py: 188, 274-276, 287-289, 304-306, 309-310
"""

import pytest
from rege.bridges.base import MockBridge, BridgeStatus


class TestMockBridgeLogOverflow:
    """Cover line 188: operations_log truncation when > 1000 entries."""

    def test_log_overflow_truncates_to_500(self):
        """Line 188: adding 1001 operations triggers truncation to 500."""
        bridge = MockBridge("overflow_test")

        # Add 1001 log operations (each _log_operation call appends one)
        for i in range(1001):
            bridge._log_operation("test_op", status="success")

        # Line 188: truncated to last 500
        assert len(bridge._operations_log) == 500


class TestMockBridgeFailDisconnect:
    """Cover lines 274-276: should_fail=True in disconnect()."""

    def test_disconnect_fail_returns_false(self):
        """Lines 274-276: should_fail=True → sets error, logs failure, returns False."""
        bridge = MockBridge("fail_bridge", should_fail=True)
        bridge.connect()  # connect fails too, but we can still try disconnect
        result = bridge.disconnect()

        # Lines 274-276: _set_error called, log failure, return False
        assert result is False
        assert bridge._last_error is not None
        assert bridge._status == BridgeStatus.ERROR


class TestMockBridgeFailSend:
    """Cover lines 287-289: should_fail=True in send()."""

    def test_send_fail_returns_error_dict(self):
        """Lines 287-289: should_fail=True → sets error, logs failure, returns failed dict."""
        bridge = MockBridge("fail_bridge", should_fail=True)
        result = bridge.send({"key": "value"})

        # Lines 287-289: _set_error called, log failure, return failed
        assert result["status"] == "failed"
        assert "error" in result
        assert bridge._last_error is not None


class TestMockBridgeFailReceive:
    """Cover lines 304-306: should_fail=True in receive()."""

    def test_receive_fail_returns_none(self):
        """Lines 304-306: should_fail=True → sets error, logs failure, returns None."""
        bridge = MockBridge("fail_bridge", should_fail=True)
        result = bridge.receive()

        # Lines 304-306: _set_error called, return None
        assert result is None
        assert bridge._last_error is not None


class TestMockBridgeReceiveNotConnected:
    """Cover lines 309-310: receive() when not connected (no should_fail)."""

    def test_receive_when_not_connected_returns_none(self):
        """Lines 309-310: not connected → log failure, return None (not via should_fail)."""
        bridge = MockBridge("disconnected_bridge", should_fail=False)
        # Not connected (status = DISCONNECTED, should_fail = False)
        # receive() checks: should_fail? No. is_connected? No → lines 309-310
        result = bridge.receive()

        # Lines 309-310: return None when not connected
        assert result is None
