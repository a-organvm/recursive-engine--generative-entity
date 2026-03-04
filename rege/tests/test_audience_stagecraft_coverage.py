"""
Coverage tests for audience_engine.py and stagecraft_module.py uncovered lines.

audience_engine.py: 201, 222-224, 336, 355-359, 415-418
stagecraft_module.py: 265-266, 391-392, 409, 454, 458, 480-485
"""

import pytest
from rege.organs.audience_engine import AudienceEngine, AudienceNode, AudienceTier, RiskLevel
from rege.organs.stagecraft_module import StagecraftModule
from rege.core.models import Invocation, Patch, DepthLevel


def make_inv(organ, symbol="", mode="default", charge=50, flags=None):
    return Invocation(
        organ=organ,
        symbol=symbol,
        mode=mode,
        depth=DepthLevel.STANDARD,
        expect="output",
        charge=charge,
        flags=flags or [],
    )


def make_patch():
    p = Patch(input_node="test", output_node="TEST", tags=[], charge=50)
    p.depth = 5
    return p


# ============================================================
# AudienceEngine coverage
# ============================================================

class TestAudienceTierAssignment:
    """Cover _assign_tier paths (lines 201, 222-224)."""

    def test_assign_tier_no_id_fails(self):
        """Line 201: tier assignment with no node_id returns failed."""
        organ = AudienceEngine()
        result = organ.invoke(make_inv("AUDIENCE_ENGINE", "", "tier", 50), make_patch())
        assert result["status"] == "failed"
        assert "required" in result["error"].lower()

    def test_assign_tier_node_not_found(self):
        """Line 201: tier assignment with unknown node ID fails."""
        organ = AudienceEngine()
        result = organ.invoke(make_inv("AUDIENCE_ENGINE", "NONEXISTENT_NODE_ID", "tier", 50), make_patch())
        assert result["status"] == "failed"
        assert "not found" in result["error"].lower()

    def test_assign_tier_triggers_change(self):
        """Lines 222-224: tier change updates distribution."""
        organ = AudienceEngine()
        patch = make_patch()

        # Create a node with low resonance (SILENT_ECHO tier)
        organ.invoke(make_inv("AUDIENCE_ENGINE", "TierChangeNode", "cultivate", 20), patch)

        # Find the node
        node = organ._find_node_by_name("TierChangeNode")
        assert node is not None
        old_tier = node.tier

        # Now reassign with higher resonance
        node.resonance_score = 65  # Will become MIRROR_WITNESS

        result = organ.invoke(make_inv("AUDIENCE_ENGINE", node.node_id, "tier", 65), patch)
        assert result["status"] == "tier_assigned"
        assert result["tier"] == "mirror_witness"
        assert result["tier_changed"] is True
        assert result["previous_tier"] == old_tier.value


class TestCalculateTierFragmentHolder:
    """Cover line 336: FRAGMENT_HOLDER tier."""

    def test_fragment_holder_tier(self):
        """Line 336: score >= 90 with ritual_participation → FRAGMENT_HOLDER."""
        organ = AudienceEngine()
        tier = organ._calculate_tier(95, ["ritual_participation"])
        assert tier == AudienceTier.FRAGMENT_HOLDER


class TestAssessParasocialRisk:
    """Cover lines 355-359: parasocial risk levels."""

    def test_elevated_risk(self):
        """Line 355-356: ELEVATED risk when engagement > 25 without participation."""
        organ = AudienceEngine()
        node = AudienceNode(
            node_id="TEST",
            name="ElevatedRisk",
            resonance_score=50,
            tier=AudienceTier.ORBITAL_WITNESS,
            echo_actions=[],
            engagement_count=30,  # > 25 = ELEVATED
        )
        risk = organ._assess_parasocial_risk(node)
        assert risk == RiskLevel.ELEVATED

    def test_mild_risk(self):
        """Line 357-358: MILD risk when engagement > 10 without participation."""
        organ = AudienceEngine()
        node = AudienceNode(
            node_id="TEST",
            name="MildRisk",
            resonance_score=50,
            tier=AudienceTier.ORBITAL_WITNESS,
            echo_actions=[],
            engagement_count=15,  # > 10 = MILD
        )
        risk = organ._assess_parasocial_risk(node)
        assert risk == RiskLevel.MILD

    def test_safe_low_engagement(self):
        """Line 359: SAFE when engagement <= 10 without participation."""
        organ = AudienceEngine()
        node = AudienceNode(
            node_id="TEST",
            name="SafeNode",
            resonance_score=50,
            tier=AudienceTier.ORBITAL_WITNESS,
            echo_actions=[],
            engagement_count=5,  # <= 10 = SAFE
        )
        risk = organ._assess_parasocial_risk(node)
        assert risk == RiskLevel.SAFE

    def test_safe_with_participation(self):
        """Line 350: SAFE when ritual_participation in actions."""
        organ = AudienceEngine()
        node = AudienceNode(
            node_id="TEST",
            name="Participant",
            resonance_score=90,
            tier=AudienceTier.FRAGMENT_HOLDER,
            echo_actions=["ritual_participation"],
            engagement_count=100,  # High but has participation
        )
        risk = organ._assess_parasocial_risk(node)
        assert risk == RiskLevel.SAFE

    def test_high_risk(self):
        """HIGH risk when engagement > 50 without participation."""
        organ = AudienceEngine()
        node = AudienceNode(
            node_id="TEST",
            name="HighRisk",
            resonance_score=50,
            tier=AudienceTier.ORBITAL_WITNESS,
            echo_actions=[],
            engagement_count=55,  # > 50 = HIGH
        )
        risk = organ._assess_parasocial_risk(node)
        assert risk == RiskLevel.HIGH


class TestAudienceRestoreState:
    """Cover lines 415-418: restore_state."""

    def test_restore_state(self):
        """Lines 415-418: restore_state restores echo_log and tier_distribution."""
        organ = AudienceEngine()
        patch = make_patch()

        # Create some state
        organ.invoke(make_inv("AUDIENCE_ENGINE", "RestoreNode", "cultivate", 50), patch)
        organ.invoke(make_inv("AUDIENCE_ENGINE", "RestoreNode2", "cultivate", 70), patch)

        # Get and restore state
        state = organ.get_state()
        organ2 = AudienceEngine()
        organ2.restore_state(state)

        assert organ2._echo_log == organ._echo_log
        assert organ2._tier_distribution == organ._tier_distribution

    def test_cultivate_updates_existing_node_tier(self):
        """Cover tier change in _cultivate_node when tier changes."""
        organ = AudienceEngine()
        patch = make_patch()

        # Create node with low resonance
        organ.invoke(make_inv("AUDIENCE_ENGINE", "TierTest", "cultivate", 20), patch)

        # Update to high resonance - this triggers tier change
        result = organ.invoke(make_inv("AUDIENCE_ENGINE", "TierTest", "cultivate", 70), patch)
        assert result["status"] == "node_updated"
        assert result["tier_changed"] is True


# ============================================================
# StagecraftModule coverage
# ============================================================

class TestEnactCharacterWithActivePerformance:
    """Cover lines 265-266: enact character updates active performance."""

    def test_enact_updates_active_performance(self):
        """Lines 265-266: enact with active performance updates character."""
        organ = StagecraftModule()
        patch = make_patch()

        # Start a performance first
        organ.invoke(make_inv("STAGECRAFT_MODULE", "Hero", "perform", 60), patch)
        assert organ._active_performance is not None

        # Now enact a new character - should update the active performance
        result = organ.invoke(make_inv("STAGECRAFT_MODULE", "Villain", "enact", 80), patch)
        assert result["status"] == "character_enacted"
        assert result["character"] == "Villain"

        # Active performance should have updated character
        perf = organ._performances[organ._active_performance]
        assert perf.character == "Villain"


class TestExtractAudienceSizeInvalid:
    """Cover lines 391-392: ValueError in _extract_audience_size."""

    def test_audience_size_invalid_int(self):
        """Lines 391-392: AUDIENCE_abc triggers ValueError, uses default 10."""
        organ = StagecraftModule()
        patch = make_patch()

        # AUDIENCE_abc is not a valid integer
        result = organ.invoke(
            make_inv("STAGECRAFT_MODULE", "Mask", "perform", 60, ["AUDIENCE_abc"]),
            patch
        )
        # Should use default audience size 10
        assert result["performance"]["audience_size"] == 10


class TestCollapseWithoutEventFlag:
    """Cover line 409: collapse event fallback."""

    def test_collapse_without_event_flag(self):
        """Line 409: _extract_collapse_event returns 'Unspecified collapse'."""
        organ = StagecraftModule()
        patch = make_patch()

        # Start a performance
        perform_result = organ.invoke(make_inv("STAGECRAFT_MODULE", "Hero", "perform", 60), patch)
        perf_id = perform_result["performance"]["performance_id"]

        # Log collapse without EVENT_ flag
        result = organ.invoke(
            make_inv("STAGECRAFT_MODULE", perf_id, "log", 60, ["COLLAPSE+"]),
            patch
        )
        assert result["status"] == "collapse_logged"
        assert "Unspecified collapse" in result["collapse_event"]


class TestCalculateDurationNone:
    """Cover line 454: _calculate_duration returns None."""

    def test_duration_none_when_no_end(self):
        """Line 454: _calculate_duration returns None when ended_at is None."""
        organ = StagecraftModule()
        from rege.organs.stagecraft_module import StagePerformance, PerformanceType, EnactmentLevel
        from datetime import datetime

        perf = StagePerformance(
            performance_id="TEST",
            character="TestChar",
            loop_depth=3,
            live_elements=["voice"],
            audience_size=10,
            performance_type=PerformanceType.LIVE,
            enactment_level=EnactmentLevel.MINOR_LOOP,
            started_at=datetime.now(),
            ended_at=None,  # No end time
        )

        duration = organ._calculate_duration(perf)
        assert duration is None


class TestGetPerformance:
    """Cover line 458: get_performance."""

    def test_get_performance_found(self):
        """Line 458: get_performance returns performance."""
        organ = StagecraftModule()
        patch = make_patch()

        result = organ.invoke(make_inv("STAGECRAFT_MODULE", "Hero", "perform", 60), patch)
        perf_id = result["performance"]["performance_id"]

        perf = organ.get_performance(perf_id)
        assert perf is not None
        assert perf.character == "Hero"

    def test_get_performance_not_found(self):
        """get_performance returns None for unknown ID."""
        organ = StagecraftModule()
        assert organ.get_performance("NONEXISTENT") is None


class TestStagecraftRestoreState:
    """Cover lines 480-485: restore_state."""

    def test_restore_state(self):
        """Lines 480-485: restore_state restores stage state."""
        organ = StagecraftModule()
        patch = make_patch()

        # Perform something
        organ.invoke(make_inv("STAGECRAFT_MODULE", "Mask", "perform", 60), patch)

        # Get and restore state
        state = organ.get_state()
        organ2 = StagecraftModule()
        organ2.restore_state(state)

        assert organ2._active_performance == organ._active_performance
        assert organ2._performance_log == organ._performance_log
        assert organ2._characters_enacted == organ._characters_enacted
        assert organ2._total_collapses == organ._total_collapses

    def test_setup_with_active_performance(self):
        """Cover _setup_stage with active performance."""
        organ = StagecraftModule()
        patch = make_patch()

        # Start a performance
        organ.invoke(make_inv("STAGECRAFT_MODULE", "Hero", "perform", 60), patch)

        # Setup with new elements
        result = organ.invoke(
            make_inv("STAGECRAFT_MODULE", "", "setup", 60, ["SOUND+", "LIGHT+", "SET_Opening_act"]),
            patch
        )
        assert result["status"] == "stage_configured"

    def test_log_outcome_completion(self):
        """Cover successful completion path in _log_outcome."""
        organ = StagecraftModule()
        patch = make_patch()

        perform_result = organ.invoke(make_inv("STAGECRAFT_MODULE", "Hero", "perform", 60), patch)
        perf_id = perform_result["performance"]["performance_id"]

        # Log successful completion
        result = organ.invoke(make_inv("STAGECRAFT_MODULE", perf_id, "log", 60), patch)
        assert result["status"] == "performance_logged"
        assert "afterloop_fragment" in result

    def test_log_with_event_flag(self):
        """Cover collapse with EVENT_ flag."""
        organ = StagecraftModule()
        patch = make_patch()

        perform_result = organ.invoke(make_inv("STAGECRAFT_MODULE", "Hero", "perform", 60), patch)
        perf_id = perform_result["performance"]["performance_id"]

        result = organ.invoke(
            make_inv("STAGECRAFT_MODULE", perf_id, "log", 60, ["COLLAPSE+", "EVENT_Mask_fell_off"]),
            patch
        )
        assert result["status"] == "collapse_logged"
        assert "Mask fell off" in result["collapse_event"]
