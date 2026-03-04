"""
Coverage tests for:
- organs/bloom_engine.py: 261, 287, 289, 291
- organs/consumption_protocol.py: 384
- organs/publishing_temple.py: 369-370, 429
- organs/archive_order.py: 106
- bridges/registry.py: 96, 140
- organs/interlocutor.py: 558, 573, 593, 633, 676, 714, 716, 718, 766-772
- formatting.py: 57
"""

import pytest
import importlib
from unittest.mock import patch, MagicMock

from rege.organs.bloom_engine import BloomEngine
from rege.organs.consumption_protocol import ConsumptionProtocol, ConsumptionArchetype
from rege.organs.publishing_temple import PublishingTemple
from rege.organs.archive_order import ArchiveOrder
from rege.organs.interlocutor import InterlocutorEngine, RiskLevel, IntentionType, ConsentLevel
from rege.bridges.registry import BridgeRegistry
from rege.bridges.base import ExternalBridge, BridgeStatus
from rege.core.models import Invocation, Patch, DepthLevel


def make_inv(organ, symbol="test", mode="default", charge=50, flags=None):
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
# BloomEngine coverage
# ============================================================

class TestBloomBranchConsolidated:
    """Cover line 261: else branch when branch_version() returns False."""

    def test_branch_returns_consolidated_when_max_reached(self):
        """Line 261: branch 6 times (max=5) → consolidated status."""
        organ = BloomEngine()
        cycle = organ.initiate_bloom("test_phase", "trigger_event", "STANDARD", 7)
        cycle_id = cycle.cycle_id

        # Exhaust max branches (MAX_VERSION_BRANCHES = 5)
        for _ in range(5):
            result = organ.branch_version(cycle_id)
            assert result["status"] == "branched"

        # 6th branch → False → consolidated (line 261)
        result = organ.branch_version(cycle_id)
        assert result["status"] == "consolidated"
        assert "Max branches reached" in result["reason"]
        assert "consolidation" in result


class TestBloomSeasons:
    """Cover lines 287, 289, 291: SPRING, SUMMER, AUTUMN in _get_current_season."""

    def test_get_current_season_spring(self):
        """Line 287: month in [3, 4, 5] → SPRING."""
        organ = BloomEngine()
        with patch("rege.organs.bloom_engine.datetime") as mock_dt:
            mock_dt.now.return_value.month = 4  # April
            season = organ._get_current_season()
        assert season == "SPRING"

    def test_get_current_season_summer(self):
        """Line 289: month in [6, 7, 8] → SUMMER."""
        organ = BloomEngine()
        with patch("rege.organs.bloom_engine.datetime") as mock_dt:
            mock_dt.now.return_value.month = 7  # July
            season = organ._get_current_season()
        assert season == "SUMMER"

    def test_get_current_season_autumn(self):
        """Line 291: month in [9, 10, 11] → AUTUMN."""
        organ = BloomEngine()
        with patch("rege.organs.bloom_engine.datetime") as mock_dt:
            mock_dt.now.return_value.month = 10  # October
            season = organ._get_current_season()
        assert season == "AUTUMN"

    def test_get_current_season_winter(self):
        """Else branch: month not in 3-11 → WINTER."""
        organ = BloomEngine()
        with patch("rege.organs.bloom_engine.datetime") as mock_dt:
            mock_dt.now.return_value.month = 1  # January
            season = organ._get_current_season()
        assert season == "WINTER"


# ============================================================
# ConsumptionProtocol coverage
# ============================================================

class TestConsumptionGhostObserver:
    """Cover line 384: GHOST_OBSERVER archetype when intensity < 30."""

    def test_ingest_low_charge_assigns_ghost_observer(self):
        """Line 384: charge < 30, no special flags → GHOST_OBSERVER archetype."""
        organ = ConsumptionProtocol()
        patch = make_patch()

        result = organ.invoke(
            make_inv("CONSUMPTION_PROTOCOL", "quiet observation", "ingest", 20),
            patch
        )

        assert result["status"] == "ingested"
        assert result["archetype_assigned"] == ConsumptionArchetype.GHOST_OBSERVER.value

    def test_determine_archetype_ghost_observer_directly(self):
        """Line 384: _determine_archetype with intensity=15, context=50 → GHOST_OBSERVER."""
        organ = ConsumptionProtocol()
        archetype = organ._determine_archetype([], 15, 50)
        assert archetype == ConsumptionArchetype.GHOST_OBSERVER


# ============================================================
# PublishingTemple coverage
# ============================================================

class TestPublishingTempleDefaultStatusWithExports:
    """Cover lines 369-370: status_counts iteration over exports."""

    def test_default_status_iterates_exports(self):
        """Lines 369-370: sanctify creates exports, default mode iterates over them."""
        organ = PublishingTemple()
        patch = make_patch()

        # Sanctify creates export with status 'sanctified' or 'risk_blocked'
        organ.invoke(
            make_inv("PUBLISHING_TEMPLE", "my_source_001", "sanctify", 80, ["CANON+"]),
            patch
        )

        # Default mode: iterates exports._values() → lines 369-370
        result = organ.invoke(
            make_inv("PUBLISHING_TEMPLE", "", "default", 50),
            patch
        )

        assert result["status"] == "temple_status"
        assert result["total_exports"] >= 1
        # Lines 369-370: status_counts updated from exports
        breakdown = result["status_breakdown"]
        total = sum(breakdown.values())
        assert total >= 1  # At least one export counted


class TestPublishingTemplePrintFlagLowCharge:
    """Cover line 429: continue when PRINT+ flag but charge < min_charge_for_print."""

    def test_print_flag_with_low_charge_continues_to_next_format(self):
        """Line 429: PRINT+ flag with charge < 71 → continue (skip PRINT), fall to DIGITAL."""
        organ = PublishingTemple()
        patch = make_patch()

        # PRINT+ requires charge >= 71 (min_charge_for_print)
        # With charge=50, the PRINT+ flag is skipped (line 429 continue)
        # No other format flags → falls through to default based on charge
        result = organ.invoke(
            make_inv("PUBLISHING_TEMPLE", "my_source_002", "sanctify", 50, ["PRINT+"]),
            patch
        )

        assert result["status"] in ("sanctified", "risk_blocked")
        # Format should NOT be PRINT (charge too low); should fall to DIGITAL
        assert result["export"]["format"] != "print"

    def test_nft_flag_with_insufficient_charge_skipped(self):
        """NFT+ flag with charge < 86 → continue, falls to charge-based format."""
        organ = PublishingTemple()
        patch = make_patch()

        result = organ.invoke(
            make_inv("PUBLISHING_TEMPLE", "nft_attempt", "sanctify", 70, ["NFT+"]),
            patch
        )

        assert result["status"] in ("sanctified", "risk_blocked")
        # Format should NOT be NFT (charge 70 < 86 required)
        assert result["export"]["format"] != "nft"


# ============================================================
# ArchiveOrder coverage
# ============================================================

class TestArchiveOrderDescription:
    """Cover line 106: description property."""

    def test_description_property(self):
        """Line 106: description returns meaningful string."""
        organ = ArchiveOrder()
        desc = organ.description
        assert isinstance(desc, str)
        assert len(desc) > 0
        assert "storage" in desc.lower() or "retrieval" in desc.lower() or "symbolic" in desc.lower()


# ============================================================
# BridgeRegistry coverage
# ============================================================

class MockBridge(ExternalBridge):
    """Minimal concrete bridge for testing."""

    def connect(self) -> bool:
        self._status = BridgeStatus.CONNECTED
        self._connected_at = __import__("datetime").datetime.now()
        return True

    def disconnect(self) -> bool:
        self._status = BridgeStatus.DISCONNECTED
        return True

    def send(self, data):
        return {"sent": True}

    def receive(self):
        return {}


class TestBridgeRegistryRemoveConnected:
    """Cover line 96: bridge.disconnect() called when removing a connected bridge."""

    def test_remove_connected_bridge_calls_disconnect(self):
        """Line 96: bridge.is_connected → bridge.disconnect() before removal."""
        registry = BridgeRegistry()
        registry.register_type("mock", MockBridge)

        bridge = registry.create_bridge("mock", "my_mock_bridge")
        assert bridge is not None

        # Connect the bridge
        bridge.connect()
        assert bridge.is_connected is True

        # Remove while connected → line 96: bridge.disconnect() called
        result = registry.remove_bridge("my_mock_bridge")
        assert result is True
        assert registry.get_bridge("my_mock_bridge") is None
        # Verify bridge was disconnected (status changed)
        assert bridge.is_connected is False

    def test_remove_disconnected_bridge_skips_disconnect(self):
        """Removing a disconnected bridge → no disconnect call (is_connected=False)."""
        registry = BridgeRegistry()
        registry.register_type("mock", MockBridge)

        bridge = registry.create_bridge("mock", "disconnected_bridge")
        assert bridge.is_connected is False  # Not connected

        result = registry.remove_bridge("disconnected_bridge")
        assert result is True
        assert registry.get_bridge("disconnected_bridge") is None

    def test_remove_nonexistent_bridge_returns_false(self):
        """remove_bridge returns False for unknown bridge names."""
        registry = BridgeRegistry()
        result = registry.remove_bridge("NONEXISTENT_BRIDGE")
        assert result is False


class TestBridgeRegistryConnectAllAlreadyConnected:
    """Cover line 140: results[name] = True when bridge is already connected."""

    def test_connect_all_already_connected_returns_true(self):
        """Line 140: bridge.is_connected → results[name] = True (no reconnect attempt)."""
        registry = BridgeRegistry()
        registry.register_type("mock", MockBridge)

        bridge = registry.create_bridge("mock", "pre_connected_bridge")
        bridge.connect()  # Pre-connect
        assert bridge.is_connected is True

        # connect_all: bridge already connected → results[name] = True (line 140)
        results = registry.connect_all()
        assert "pre_connected_bridge" in results
        assert results["pre_connected_bridge"] is True

    def test_connect_all_disconnected_bridge_calls_connect(self):
        """connect_all calls bridge.connect() when not connected."""
        registry = BridgeRegistry()
        registry.register_type("mock", MockBridge)

        registry.create_bridge("mock", "fresh_bridge")

        results = registry.connect_all()
        assert "fresh_bridge" in results
        assert results["fresh_bridge"] is True  # MockBridge.connect() returns True


# ============================================================
# InterlocutorEngine coverage
# ============================================================

class TestInterlocutorRiskMedium:
    """Cover line 558: RiskLevel.MEDIUM from RISK_MEDIUM+ flag."""

    def test_possession_with_risk_medium_flag(self):
        """Line 558: RISK_MEDIUM+ flag → risk_level = 'medium' in result."""
        organ = InterlocutorEngine()
        patch = make_patch()

        result = organ.invoke(
            make_inv("INTERLOCUTOR", "some entity", "possession", 60, ["RISK_MEDIUM+"]),
            patch
        )

        assert result["status"] == "possession_active"
        assert result["entry"]["risk_level"] == "medium"

    def test_extract_risk_level_medium_directly(self):
        """Line 558: _extract_risk_level with RISK_MEDIUM+ returns MEDIUM."""
        organ = InterlocutorEngine()
        risk = organ._extract_risk_level(["RISK_MEDIUM+"])
        assert risk == RiskLevel.MEDIUM


class TestInterlocutorIntentionExtract:
    """Cover line 573: return intention in _extract_intention."""

    def test_possession_with_clarify_flag(self):
        """Line 573: CLARIFY+ flag → intention = 'clarify'."""
        organ = InterlocutorEngine()
        patch = make_patch()

        result = organ.invoke(
            make_inv("INTERLOCUTOR", "some concept", "possession", 60, ["CLARIFY+"]),
            patch
        )

        assert result["status"] == "possession_active"
        assert result["entry"]["intention"] == "clarify"

    def test_extract_intention_directly_all_flags(self):
        """Line 573: all intention flags return the right type."""
        organ = InterlocutorEngine()
        assert organ._extract_intention(["DECODE+"]) == IntentionType.DECODE
        assert organ._extract_intention(["RITUALIZE+"]) == IntentionType.RITUALIZE
        assert organ._extract_intention(["EMBODY+"]) == IntentionType.EMBODY
        assert organ._extract_intention(["CHALLENGE+"]) == IntentionType.CHALLENGE


class TestInterlocutorConsentSymbolicOnly:
    """Cover line 593: CONSENT_SYMBOLIC+ → ConsentLevel.SYMBOLIC_ONLY."""

    def test_grant_consent_with_symbolic_flag(self):
        """Line 593: GRANT+ + CONSENT_SYMBOLIC+ → consent_level = 'symbolic_only'."""
        organ = InterlocutorEngine()
        patch = make_patch()

        result = organ.invoke(
            make_inv("INTERLOCUTOR", "friend_node", "consent", 50, ["GRANT+", "CONSENT_SYMBOLIC+"]),
            patch
        )

        assert result["status"] == "consent_granted"
        assert result["record"]["consent_level"] == "symbolic_only"

    def test_extract_consent_level_symbolic_directly(self):
        """Line 593: _extract_consent_level with CONSENT_SYMBOLIC+ returns SYMBOLIC_ONLY."""
        organ = InterlocutorEngine()
        level = organ._extract_consent_level(["CONSENT_SYMBOLIC+"])
        assert level == ConsentLevel.SYMBOLIC_ONLY


class TestInterlocutorGhostIntense:
    """Cover line 633: ghost response with intensity charge 71-85."""

    def test_summoning_charge_75_intense_response(self):
        """Line 633: 71 <= charge < 86 → 'speaks with intensity' ghost response."""
        organ = InterlocutorEngine()
        patch = make_patch()

        result = organ.invoke(
            make_inv("INTERLOCUTOR", "Artaud", "summoning", 75),
            patch
        )

        assert result["status"] == "summoned"
        assert "intensity" in result["ghost_response"] or "intense" in result["ghost_response"].lower()

    def test_generate_ghost_response_intense_directly(self):
        """Line 633: _generate_ghost_response with 71 <= charge < 86."""
        organ = InterlocutorEngine()
        response = organ._generate_ghost_response("Test", 75, True)
        assert "intensity" in response


class TestInterlocutorMaskLightContact:
    """Cover line 676: mask interpretation with charge < 51."""

    def test_mask_shift_low_charge_light_contact(self):
        """Line 676: charge < 51 → 'light mask contact' interpretation."""
        organ = InterlocutorEngine()
        patch = make_patch()

        result = organ.invoke(
            make_inv("INTERLOCUTOR", "symbol subject", "mask-shift", 40),
            patch
        )

        assert result["status"] == "mask_shift_active"
        assert "light" in result["interpretation"].lower()

    def test_generate_mask_interpretation_light_directly(self):
        """Line 676: _generate_mask_interpretation with charge < 51."""
        organ = InterlocutorEngine()
        interp = organ._generate_mask_interpretation("Subject", "Hero Mask", 40)
        assert "light" in interp.lower()


class TestInterlocutorAgentVoiceIntentions:
    """Cover lines 714, 716, 718: CHALLENGE, EMBODY, DECODE agent voice lines."""

    def test_multiplicity_challenge_intention(self):
        """Line 714: CHALLENGE+ flag → agent voices contain 'contest'."""
        organ = InterlocutorEngine()
        patch = make_patch()

        result = organ.invoke(
            make_inv("INTERLOCUTOR", "idea", "multiplicity", 60, ["CHALLENGE+"]),
            patch
        )

        assert result["status"] == "multiplicity_active"
        voices = result["voices"]
        # All agents use CHALLENGE branch
        assert any("contest" in v for v in voices.values())

    def test_multiplicity_embody_intention(self):
        """Line 716: EMBODY+ flag → agent voices contain 'I am the'."""
        organ = InterlocutorEngine()
        patch = make_patch()

        result = organ.invoke(
            make_inv("INTERLOCUTOR", "concept", "multiplicity", 60, ["EMBODY+"]),
            patch
        )

        assert result["status"] == "multiplicity_active"
        voices = result["voices"]
        assert any("I am the" in v for v in voices.values())

    def test_multiplicity_decode_intention(self):
        """Line 718: DECODE+ flag → agent voices contain 'encodes this'."""
        organ = InterlocutorEngine()
        patch = make_patch()

        result = organ.invoke(
            make_inv("INTERLOCUTOR", "signal", "multiplicity", 60, ["DECODE+"]),
            patch
        )

        assert result["status"] == "multiplicity_active"
        voices = result["voices"]
        assert any("encodes this" in v for v in voices.values())

    def test_generate_agent_voice_all_intentions_directly(self):
        """Lines 714, 716, 718: _generate_agent_voice for all non-default intentions."""
        from rege.organs.interlocutor import IntentionType
        organ = InterlocutorEngine()

        challenge = organ._generate_agent_voice("Shadow", "idea", IntentionType.CHALLENGE)
        assert "contest" in challenge  # line 714

        embody = organ._generate_agent_voice("Echo", "idea", IntentionType.EMBODY)
        assert "I am the" in embody  # line 716

        decode = organ._generate_agent_voice("Origin", "idea", IntentionType.DECODE)
        assert "encodes this" in decode  # line 718


class TestInterlocutorRestoreState:
    """Cover lines 766-772: restore_state() method."""

    def test_restore_state_restores_all_fields(self):
        """Lines 766-772: restore_state restores dialogue_log, possession_history, totals."""
        organ = InterlocutorEngine()
        patch = make_patch()

        # Create some state via invocations
        organ.invoke(make_inv("INTERLOCUTOR", "entity", "possession", 60, ["VOLATILE+"]), patch)
        organ.invoke(make_inv("INTERLOCUTOR", "ghost", "summoning", 50), patch)

        state = organ.get_state()

        # Verify state has the expected fields
        assert "state" in state
        assert "dialogue_log" in state["state"]
        assert "possession_history" in state["state"]
        assert state["state"]["total_dialogues"] == 2
        assert state["state"]["total_possessions"] == 1

        # Restore into fresh organ (lines 766-772)
        organ2 = InterlocutorEngine()
        organ2.restore_state(state)

        # Verify restored correctly
        assert organ2._dialogue_log == organ._dialogue_log
        assert organ2._possession_history == organ._possession_history
        assert organ2._total_dialogues == 2
        assert organ2._total_possessions == 1
        assert organ2._volatile_possession_count == 1

    def test_restore_state_empty(self):
        """Lines 766-772: restore_state with empty state dict uses defaults."""
        organ = InterlocutorEngine()
        organ.restore_state({"state": {}})
        assert organ._dialogue_log == []
        assert organ._possession_history == []
        assert organ._total_dialogues == 0
        assert organ._total_possessions == 0
        assert organ._volatile_possession_count == 0


# ============================================================
# formatting.py coverage
# ============================================================

class TestFormattingNoColor:
    """Cover line 57: Colors.disable() when NO_COLOR env var is set."""

    def test_no_color_env_triggers_disable(self, monkeypatch):
        """Line 57: module reload with NO_COLOR=1 → Colors.disable() called → attrs empty."""
        import importlib
        import rege.formatting as fmt

        # Verify colors are non-empty before disabling
        assert fmt.Colors.GREEN != ""

        monkeypatch.setenv("NO_COLOR", "1")
        importlib.reload(fmt)

        # Line 57 executed: Colors.disable() was called
        assert fmt.Colors.GREEN == ""
        assert fmt.Colors.RED == ""

        # Cleanup: restore module without NO_COLOR
        monkeypatch.delenv("NO_COLOR", raising=False)
        importlib.reload(fmt)
        assert fmt.Colors.GREEN != ""  # Restored
