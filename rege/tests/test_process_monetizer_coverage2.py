"""
Coverage tests for process_monetizer.py uncovered lines:
315-316, 325-326, 350, 355, 359, 361, 367, 369, 375, 389, 396, 401, 420-422
"""

import pytest
from rege.organs.process_monetizer import (
    ProcessMonetizer,
    MonetizableProduct,
    ProductFormat,
    PricingStatus,
    MonetizationType,
)
from rege.core.models import Invocation, Patch, DepthLevel


def make_inv(symbol="", mode="monetize", charge=80, flags=None):
    return Invocation(
        organ="PROCESS_MONETIZER",
        symbol=symbol,
        mode=mode,
        depth=DepthLevel.STANDARD,
        expect="output",
        charge=charge,
        flags=flags or [],
    )


def make_patch():
    return Patch(input_node="test", output_node="PROCESS_MONETIZER", tags=[], charge=80)


class TestExtractCountsWithInvalidFlags:
    """Cover lines 315-316, 325-326: ValueError in extract helpers."""

    def test_extract_loop_count_invalid_value(self):
        """Lines 315-316: LOOPS_ with non-integer triggers ValueError."""
        organ = ProcessMonetizer()
        patch = make_patch()

        # LOOPS_abc is not a valid int
        result = organ.invoke(make_inv("test", "value", 80, ["LOOPS_abc"]), patch)
        # Should fall through to default loop count = 1
        assert result["loop_count"] == 1

    def test_extract_witness_count_invalid_value(self):
        """Lines 325-326: WITNESSES_ with non-integer triggers ValueError."""
        organ = ProcessMonetizer()
        patch = make_patch()

        # WITNESSES_xyz is not a valid int
        result = organ.invoke(make_inv("test", "value", 80, ["WITNESSES_xyz"]), patch)
        # Should fall through to default witness count = 1
        assert result["witness_count"] == 1


class TestDetermineFormatPDFDefault:
    """Cover line 350: PDF format for low integrity."""

    def test_format_pdf_default_below_71(self):
        """Line 350: integrity < 71 defaults to PDF in _determine_format."""
        organ = ProcessMonetizer()
        # Need to test _determine_format directly
        # It's called internally via _monetize_process, but we need to hit the PDF branch.
        # Since monetize requires >= 71, we test _determine_format directly.
        result = organ._determine_format([], 50)
        assert result == ProductFormat.PDF


class TestDeterminePricingStatus:
    """Cover lines 355, 359, 361: pricing status flags."""

    def test_free_flag(self):
        """Line 355: FREE+ flag returns FREE."""
        organ = ProcessMonetizer()
        patch = make_patch()

        result = organ.invoke(make_inv("test", "monetize", 80, ["FREE+"]), patch)
        assert result["product"]["pricing_status"] == "free"

    def test_timed_flag(self):
        """Line 359: TIMED+ flag returns TIMED."""
        organ = ProcessMonetizer()
        patch = make_patch()

        result = organ.invoke(make_inv("test", "monetize", 80, ["TIMED+"]), patch)
        assert result["product"]["pricing_status"] == "timed"

    def test_sacred_flag(self):
        """Line 361: SACRED+ flag returns SACRED."""
        organ = ProcessMonetizer()
        patch = make_patch()

        result = organ.invoke(make_inv("test", "monetize", 80, ["SACRED+"]), patch)
        assert result["product"]["pricing_status"] == "sacred"


class TestDetermineMonetizationType:
    """Cover lines 367, 369, 375: monetization type flags."""

    def test_visibility_flag(self):
        """Line 367: VISIBILITY+ flag returns VISIBILITY."""
        organ = ProcessMonetizer()
        patch = make_patch()

        result = organ.invoke(make_inv("test", "monetize", 80, ["VISIBILITY+"]), patch)
        assert result["product"]["monetization_type"] == "visibility"

    def test_access_flag(self):
        """Line 369: ACCESS+ flag returns ACCESS."""
        organ = ProcessMonetizer()
        patch = make_patch()

        result = organ.invoke(make_inv("test", "monetize", 80, ["ACCESS+"]), patch)
        assert result["product"]["monetization_type"] == "access"

    def test_offering_flag(self):
        """Line 375: OFFERING+ flag returns OFFERING."""
        organ = ProcessMonetizer()
        patch = make_patch()

        result = organ.invoke(make_inv("test", "monetize", 80, ["OFFERING+"]), patch)
        assert result["product"]["monetization_type"] == "offering"


class TestCountByMethods:
    """Cover lines 389, 396: _count_by_status and _count_by_format (via ledger and default modes)."""

    def test_ledger_calls_count_by_status(self):
        """Line 389: _count_by_status is called by _view_ledger."""
        organ = ProcessMonetizer()
        patch = make_patch()

        # Monetize a product first
        organ.invoke(make_inv("product", "monetize", 80, ["SUBSCRIPTION+"]), patch)

        # Ledger calls _count_by_status
        result = organ.invoke(make_inv("", "ledger"), patch)
        assert result["status"] == "ledger_retrieved"
        assert "products_by_status" in result

    def test_default_calls_count_by_format(self):
        """Line 396: _count_by_format is called by _default_status."""
        organ = ProcessMonetizer()
        patch = make_patch()

        organ.invoke(make_inv("product", "monetize", 80, ["SCROLL+"]), patch)

        result = organ.invoke(make_inv("", "default"), patch)
        assert result["status"] == "monetizer_status"
        assert "products_by_format" in result
        assert result["products_by_format"]["scroll"] == 1


class TestGetProduct:
    """Cover line 401: get_product."""

    def test_get_product_found(self):
        """Line 401: get_product returns product."""
        organ = ProcessMonetizer()
        patch = make_patch()

        result = organ.invoke(make_inv("my product", "monetize", 80), patch)
        product_id = result["product"]["product_id"]

        product = organ.get_product(product_id)
        assert product is not None
        assert product.title == "my product"

    def test_get_product_not_found(self):
        """get_product returns None for unknown ID."""
        organ = ProcessMonetizer()
        product = organ.get_product("NONEXISTENT_PROD")
        assert product is None


class TestRestoreState:
    """Cover lines 420-422: restore_state."""

    def test_restore_state_restores_ledger(self):
        """Lines 420-422: restore_state restores monetization_ledger."""
        organ = ProcessMonetizer()
        patch = make_patch()

        # Monetize something
        organ.invoke(make_inv("restore test", "monetize", 80), patch)

        # Capture state
        state = organ.get_state()
        assert len(state["state"]["products"]) == 1

        # Restore to new organ
        organ2 = ProcessMonetizer()
        organ2.restore_state(state)

        # Ledger should be restored
        assert organ2._monetization_ledger == organ._monetization_ledger


class TestCountByMonetizationType:
    """Cover line 396: _count_by_monetization_type via default status."""

    def test_default_calls_count_by_type(self):
        """_count_by_monetization_type is called from default status."""
        organ = ProcessMonetizer()
        patch = make_patch()

        organ.invoke(make_inv("product", "monetize", 80, ["OFFERING+"]), patch)

        result = organ.invoke(make_inv("", "default"), patch)
        assert "products_by_type" in result
        assert result["products_by_type"]["offering"] == 1

    def test_mp4_format(self):
        """Cover MP4+ flag format."""
        organ = ProcessMonetizer()
        patch = make_patch()

        result = organ.invoke(make_inv("video", "monetize", 80, ["MP4+"]), patch)
        assert result["product"]["format"] == "mp4"

    def test_live_ritual_format(self):
        """Cover LIVE+ flag format."""
        organ = ProcessMonetizer()
        patch = make_patch()

        result = organ.invoke(make_inv("live", "monetize", 80, ["LIVE+"]), patch)
        assert result["product"]["format"] == "live_ritual"

    def test_archive_bundle_format(self):
        """Cover ARCHIVE+ flag format."""
        organ = ProcessMonetizer()
        patch = make_patch()

        result = organ.invoke(make_inv("archive", "monetize", 80, ["ARCHIVE+"]), patch)
        assert result["product"]["format"] == "archive_bundle"

    def test_monetize_no_symbol_auto_title(self):
        """Monetize with empty symbol auto-generates title."""
        organ = ProcessMonetizer()
        patch = make_patch()

        result = organ.invoke(make_inv("", "monetize", 80), patch)
        assert result["status"] == "monetized"
        assert "Process_" in result["product"]["title"]
