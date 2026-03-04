"""
Coverage tests for publishing_temple.py uncovered lines:
217, 224, 273, 310, 316, 369-370, 397, 429, 451-453, 455, 461, 466, 473-474,
500, 504-511, 515-519
"""

import pytest
from rege.organs.publishing_temple import (
    PublishingTemple,
    RitualExport,
    PublicationFormat,
    ScarcityLevel,
    PUBLICATION_CONFIG,
)
from rege.core.models import Invocation, Patch, DepthLevel


def make_inv(symbol="", mode="default", charge=80, flags=None):
    return Invocation(
        organ="PUBLISHING_TEMPLE",
        symbol=symbol,
        mode=mode,
        depth=DepthLevel.STANDARD,
        expect="output",
        charge=charge,
        flags=flags or [],
    )


def make_patch(charge=80, depth=7):
    patch = Patch(input_node="test", output_node="PUBLISHING_TEMPLE", tags=[], charge=charge)
    patch.depth = depth
    return patch


class TestPublishFailurePaths:
    """Cover publish failure paths (lines 217, 224)."""

    def test_publish_already_withdrawn_fails(self):
        """Line 217: export status not in sanctified/pending."""
        organ = PublishingTemple()
        patch = make_patch()

        # Create and sanctify
        sanctify_result = organ.invoke(make_inv("test", "sanctify", 80), patch)
        export_id = sanctify_result["export"]["export_id"]

        # Withdraw it
        organ.invoke(make_inv(export_id, "withdraw", 80), patch)

        # Now try to publish a withdrawn export
        result = organ.invoke(make_inv(export_id, "publish", 80), patch)
        assert result["status"] == "failed"
        assert "not ready" in result["error"].lower()

    def test_publish_already_published_fails(self):
        """Line 217: publishing an already published export fails."""
        organ = PublishingTemple()
        patch = make_patch()

        # Sanctify and publish
        sanctify_result = organ.invoke(make_inv("test", "sanctify", 80), patch)
        export_id = sanctify_result["export"]["export_id"]
        organ.invoke(make_inv(export_id, "publish", 80), patch)

        # Try publishing again
        result = organ.invoke(make_inv(export_id, "publish", 80), patch)
        assert result["status"] == "failed"

    def test_publish_high_risk_blocked(self):
        """Line 224: export with risk > threshold is blocked at publish time."""
        organ = PublishingTemple()
        patch = make_patch(charge=40, depth=1)

        # First set up a high-risk export manually by directly adding it to exports
        from datetime import datetime
        import uuid
        export = RitualExport(
            export_id=f"EXPORT_{uuid.uuid4().hex[:8].upper()}",
            source_id="risky",
            format=PublicationFormat.DIGITAL,
            scarcity=ScarcityLevel.UNLIMITED,
            scarcity_count=None,
            metadata={},
            sealed_at=None,
            published_at=None,
            risk_score=80,  # Above max_risk_score (75)
            status="sanctified",  # Force sanctified status
        )
        organ._exports[export.export_id] = export

        result = organ.invoke(make_inv(export.export_id, "publish", 50), make_patch())
        assert result["status"] == "blocked"
        assert "Risk score exceeds threshold" in result["error"]


class TestSealFailurePath:
    """Cover seal not-found path (line 273)."""

    def test_seal_nonexistent_export_fails(self):
        """Line 273: sealing an export that doesn't exist."""
        organ = PublishingTemple()
        result = organ.invoke(make_inv("NONEXISTENT_EXPORT", "seal", 70), make_patch())
        assert result["status"] == "failed"
        assert "not found" in result["error"].lower()


class TestWithdrawFailurePaths:
    """Cover withdraw failure paths (lines 310, 316)."""

    def test_withdraw_no_id_fails(self):
        """Line 310: withdrawing without export ID fails."""
        organ = PublishingTemple()
        result = organ.invoke(make_inv("", "withdraw", 50), make_patch())
        assert result["status"] == "failed"
        assert "required" in result["error"].lower()

    def test_withdraw_nonexistent_fails(self):
        """Line 316: withdrawing non-existent export fails."""
        organ = PublishingTemple()
        result = organ.invoke(make_inv("NONEXISTENT_ID", "withdraw", 50), make_patch())
        assert result["status"] == "failed"
        assert "not found" in result["error"].lower()

    def test_withdraw_from_queue_removes_it(self):
        """Line 316: withdrawing from queue removes it."""
        organ = PublishingTemple()
        patch = make_patch()

        # Sanctify to add to queue
        sanctify_result = organ.invoke(make_inv("queue test", "sanctify", 80), patch)
        export_id = sanctify_result["export"]["export_id"]

        # Verify in queue
        assert export_id in organ._publication_queue

        # Withdraw removes from queue
        result = organ.invoke(make_inv(export_id, "withdraw", 50), patch)
        assert result["status"] == "withdrawn"
        assert export_id not in organ._publication_queue


class TestCalculateRisk:
    """Cover _calculate_risk paths (lines 369-370, 397, etc.)."""

    def test_risk_with_volatile_flag(self):
        """Line ~400: VOLATILE+ increases risk."""
        organ = PublishingTemple()
        patch = make_patch(charge=80, depth=7)

        # Use VOLATILE+ flag - should increase risk
        result = organ.invoke(make_inv("volatile", "sanctify", 80, ["VOLATILE+"]), patch)
        # With VOLATILE+ (+20), charge 80 (-10), depth 7 (-10), CANON- = 50 + 10 - 10 + 20 - 10 = 60
        assert result["risk_assessment"]["score"] >= 50

    def test_risk_with_archive_flag(self):
        """Line ~397: ARCHIVE+ reduces risk."""
        organ = PublishingTemple()
        patch = make_patch(charge=80, depth=7)

        result = organ.invoke(make_inv("archive", "sanctify", 80, ["ARCHIVE+"]), patch)
        # ARCHIVE+ reduces risk
        assert result["risk_assessment"]["score"] < 50

    def test_risk_high_charge_reduces(self):
        """Line ~392: charge >= 86 reduces risk by 15."""
        organ = PublishingTemple()
        patch = make_patch(charge=90, depth=7)

        result_high = organ.invoke(make_inv("high charge", "sanctify", 90), patch)
        result_std = organ.invoke(make_inv("std charge", "sanctify", 75), patch)

        # Higher charge should mean lower risk
        assert result_high["risk_assessment"]["score"] < result_std["risk_assessment"]["score"]

    def test_risk_low_depth_increases(self):
        """Line ~406-407: depth < 3 increases risk."""
        organ = PublishingTemple()
        patch_low = make_patch(charge=80, depth=1)
        patch_high = make_patch(charge=80, depth=8)

        result_low = organ.invoke(make_inv("low depth", "sanctify", 80), patch_low)
        result_high = organ.invoke(make_inv("high depth", "sanctify", 80), patch_high)

        assert result_low["risk_assessment"]["score"] > result_high["risk_assessment"]["score"]

    def test_risk_with_incomplete_flag(self):
        """INCOMPLETE+ increases risk."""
        organ = PublishingTemple()
        patch = make_patch(charge=80, depth=7)

        result = organ.invoke(make_inv("incomplete", "sanctify", 80, ["INCOMPLETE+"]), patch)
        # INCOMPLETE+ increases risk by 15
        assert result["risk_assessment"]["score"] > 40


class TestDetermineScarcity:
    """Cover _determine_scarcity paths (lines 451-455)."""

    def test_scarcity_timed(self):
        """Line 455: TIMED+ scarcity returns (TIMED, None)."""
        organ = PublishingTemple()
        patch = make_patch()

        result = organ.invoke(make_inv("timed", "sanctify", 80, ["TIMED+"]), patch)
        assert result["export"]["scarcity"] == "timed"
        assert result["export"]["scarcity_count"] is None

    def test_scarcity_limited_no_count(self):
        """Line 453: LIMITED+ without COUNT_ uses default 100."""
        organ = PublishingTemple()
        patch = make_patch()

        result = organ.invoke(make_inv("limited", "sanctify", 80, ["LIMITED+"]), patch)
        assert result["export"]["scarcity"] == "limited"
        assert result["export"]["scarcity_count"] == 100

    def test_scarcity_limited_invalid_count(self):
        """Line 451-452: LIMITED+ with invalid COUNT_ tries except ValueError."""
        organ = PublishingTemple()
        patch = make_patch()

        # COUNT_abc is not a valid int — triggers ValueError exception
        result = organ.invoke(make_inv("limited", "sanctify", 80, ["LIMITED+", "COUNT_abc"]), patch)
        assert result["export"]["scarcity"] == "limited"
        assert result["export"]["scarcity_count"] == 100  # falls through to default


class TestRecordDistribution:
    """Cover record_distribution failure paths (lines 461, 466, 473-474)."""

    def test_distribution_export_not_found(self):
        """Line 461: distributing non-existent export fails."""
        organ = PublishingTemple()
        result = organ.record_distribution("NONEXISTENT_EXPORT")
        assert result["status"] == "failed"
        assert "Export not found" in result["error"]

    def test_distribution_not_published(self):
        """Line 466: distributing unpublished export fails."""
        organ = PublishingTemple()
        patch = make_patch()

        # Sanctify but don't publish
        sanctify_result = organ.invoke(make_inv("unpublished", "sanctify", 80), patch)
        export_id = sanctify_result["export"]["export_id"]

        result = organ.record_distribution(export_id)
        assert result["status"] == "failed"
        assert "not published" in result["error"]

    def test_distribution_limited_exhausted(self):
        """Lines 473-474: limited quantity exhaustion."""
        organ = PublishingTemple()
        patch = make_patch()

        # Create and publish limited edition (count=2)
        sanctify_result = organ.invoke(
            make_inv("limited ed", "sanctify", 80, ["LIMITED+", "COUNT_2"]), patch
        )
        export_id = sanctify_result["export"]["export_id"]
        organ.invoke(make_inv(export_id, "publish", 80), patch)

        # Distribute twice (fills limit)
        dist1 = organ.record_distribution(export_id, "A")
        dist2 = organ.record_distribution(export_id, "B")
        assert dist1["status"] == "distributed"
        assert dist2["status"] == "distributed"

        # Third distribution should fail
        dist3 = organ.record_distribution(export_id, "C")
        assert dist3["status"] == "failed"
        assert "exhausted" in dist3["error"].lower()


class TestOutputTypesAndState:
    """Cover get_output_types, get_state, restore_state (lines 500, 504-519)."""

    def test_get_output_types(self):
        """Line 500: get_output_types returns list."""
        organ = PublishingTemple()
        types = organ.get_output_types()
        assert "sanctification" in types
        assert "temple_status" in types

    def test_get_state(self):
        """Lines 504-511: get_state includes exports."""
        organ = PublishingTemple()
        patch = make_patch()

        # Add an export
        organ.invoke(make_inv("state test", "sanctify", 80), patch)

        state = organ.get_state()
        assert "exports" in state["state"]
        assert "publication_queue" in state["state"]
        assert "publication_history" in state["state"]
        assert "distribution_log" in state["state"]

    def test_restore_state(self):
        """Lines 515-519: restore_state restores temple state."""
        organ = PublishingTemple()
        patch = make_patch()

        # Create state
        organ.invoke(make_inv("restore test", "sanctify", 80), patch)

        # Capture and restore state
        state = organ.get_state()
        organ2 = PublishingTemple()
        organ2.restore_state(state)

        # Restored organ should have the same queue
        assert organ2._publication_queue == organ._publication_queue
        assert organ2._publication_history == organ._publication_history

    def test_determine_format_nft_flag_with_high_charge(self):
        """Cover NFT format with sufficient charge."""
        organ = PublishingTemple()
        patch = make_patch(charge=90)

        result = organ.invoke(make_inv("nft", "sanctify", 90, ["NFT+"]), patch)
        assert result["export"]["format"] == "nft"

    def test_determine_format_ritual_flag(self):
        """Cover RITUAL+ flag format."""
        organ = PublishingTemple()
        patch = make_patch(charge=80)

        result = organ.invoke(make_inv("ritual", "sanctify", 80, ["RITUAL+"]), patch)
        assert result["export"]["format"] == "ritual"

    def test_determine_format_print_with_sufficient_charge(self):
        """Cover PRINT+ flag with sufficient charge."""
        organ = PublishingTemple()
        patch = make_patch(charge=80)

        result = organ.invoke(make_inv("print", "sanctify", 80, ["PRINT+"]), patch)
        assert result["export"]["format"] == "print"

    def test_view_queue_empty(self):
        """Test queue view with no exports."""
        organ = PublishingTemple()
        result = organ.invoke(make_inv("", "queue", 50), make_patch())
        assert result["status"] == "queue_retrieved"
        assert result["queue_length"] == 0
