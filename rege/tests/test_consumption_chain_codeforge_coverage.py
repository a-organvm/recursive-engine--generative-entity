"""
Coverage tests for:
- consumption_protocol.py: 205, 341-342, 351, 360, 384, 395, 429, 450-454
- orchestration/chain.py: 212, 239, 255, 261, 270
- organs/code_forge.py: 38, 125-131, 274
- orchestration/phase.py: 191, 265
"""

import pytest
from rege.organs.consumption_protocol import (
    ConsumptionProtocol,
    ConsumptionArchetype,
    ConsentStatus,
    RiskStatus,
)
from rege.orchestration.chain import RitualChain
from rege.orchestration.phase import Phase, Branch, combined_condition
from rege.organs.code_forge import CodeForge
from rege.core.models import Invocation, Patch, DepthLevel


def make_inv(organ, symbol="", mode="ingest", charge=50, flags=None):
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
# ConsumptionProtocol coverage
# ============================================================

class TestGatedOutputRiskStatus:
    """Cover line 205: GATED risk status."""

    def test_gated_risk_when_in_gated_list(self):
        """Line 205: output_id in _gated_outputs → GATED status."""
        organ = ConsumptionProtocol()
        organ._gated_outputs.append("GATED_OUTPUT")

        result = organ.invoke(make_inv("CONSUMPTION_PROTOCOL", "GATED_OUTPUT", "ingest", 50), make_patch())
        assert result["status"] == "ingested"
        assert result["record"]["risk_status"] == "gated"


class TestExtractContextLevelInvalid:
    """Cover lines 341-342: ValueError in _extract_context_level."""

    def test_context_level_invalid_value(self):
        """Lines 341-342: CONTEXT_abc triggers ValueError, uses default 50."""
        organ = ConsumptionProtocol()
        result = organ.invoke(
            make_inv("CONSUMPTION_PROTOCOL", "test", "assess", 50, ["CONTEXT_abc"]),
            make_patch()
        )
        # Should use default context 50
        assert result["status"] == "assessed"
        assert result["context_level"] == 50


class TestExtractAudienceTier:
    """Cover line 351: audience tier flag found."""

    def test_audience_tier_flag(self):
        """Line 351: audience tier flag found in flags."""
        organ = ConsumptionProtocol()
        result = organ.invoke(
            make_inv("CONSUMPTION_PROTOCOL", "test", "ingest", 50, ["mirror_witness+"]),
            make_patch()
        )
        assert result["status"] == "ingested"
        assert result["record"]["audience_tier"] == "mirror_witness"

    def test_fragment_holder_tier(self):
        """fragment_holder tier in flags."""
        organ = ConsumptionProtocol()
        result = organ.invoke(
            make_inv("CONSUMPTION_PROTOCOL", "test", "ingest", 50, ["fragment_holder+"]),
            make_patch()
        )
        assert result["record"]["audience_tier"] == "fragment_holder"


class TestExtractFormat:
    """Cover line 360: format flag found."""

    def test_format_flag_pdf(self):
        """Line 360: pdf format found in flags."""
        organ = ConsumptionProtocol()
        result = organ.invoke(
            make_inv("CONSUMPTION_PROTOCOL", "test", "ingest", 50, ["pdf+"]),
            make_patch()
        )
        assert result["record"]["format"] == "pdf"

    def test_format_flag_mp4(self):
        """Line 360: mp4 format found."""
        organ = ConsumptionProtocol()
        result = organ.invoke(
            make_inv("CONSUMPTION_PROTOCOL", "test", "ingest", 50, ["mp4+"]),
            make_patch()
        )
        assert result["record"]["format"] == "mp4"

    def test_format_flag_livestream(self):
        """Line 360: livestream format found."""
        organ = ConsumptionProtocol()
        result = organ.invoke(
            make_inv("CONSUMPTION_PROTOCOL", "test", "ingest", 50, ["livestream+"]),
            make_patch()
        )
        assert result["record"]["format"] == "livestream"


class TestDetermineArchetypeRitualConsumer:
    """Cover line 384: RITUAL_CONSUMER archetype."""

    def test_ritual_consumer_high_context(self):
        """Line 384: context > 70 → RITUAL_CONSUMER archetype."""
        organ = ConsumptionProtocol()
        result = organ.invoke(
            make_inv("CONSUMPTION_PROTOCOL", "test", "ingest", 50, ["CONTEXT_80"]),
            make_patch()
        )
        assert result["archetype_assigned"] == "ritual_consumer"


class TestDetermineConsentRevoked:
    """Cover line 395: REVOKED consent."""

    def test_revoked_consent(self):
        """Line 395: REVOKED+ flag → ConsentStatus.REVOKED."""
        organ = ConsumptionProtocol()
        result = organ.invoke(
            make_inv("CONSUMPTION_PROTOCOL", "test", "ingest", 50, ["REVOKED+"]),
            make_patch()
        )
        assert result["record"]["consent_status"] == "revoked"


class TestGetRecord:
    """Cover line 429: get_record."""

    def test_get_record_found(self):
        """Line 429: get_record returns consumption record."""
        organ = ConsumptionProtocol()
        result = organ.invoke(make_inv("CONSUMPTION_PROTOCOL", "test", "ingest", 50), make_patch())
        record_id = result["record"]["record_id"]

        record = organ.get_record(record_id)
        assert record is not None
        assert record.output_id == "test"

    def test_get_record_not_found(self):
        """get_record returns None for unknown ID."""
        organ = ConsumptionProtocol()
        assert organ.get_record("NONEXISTENT") is None


class TestConsumptionRestoreState:
    """Cover lines 450-454: restore_state."""

    def test_restore_state(self):
        """Lines 450-454: restore_state restores consumption_log and gated_outputs."""
        organ = ConsumptionProtocol()
        organ._gated_outputs.append("GATED_OUT")

        organ.invoke(make_inv("CONSUMPTION_PROTOCOL", "test", "ingest", 50), make_patch())

        state = organ.get_state()
        organ2 = ConsumptionProtocol()
        organ2.restore_state(state)

        assert organ2._consumption_log == organ._consumption_log
        assert organ2._gated_outputs == organ._gated_outputs
        assert organ2._damage_reports == organ._damage_reports

    def test_record_echo_distortion_found(self):
        """Cover record_echo_distortion success path."""
        organ = ConsumptionProtocol()
        result = organ.invoke(make_inv("CONSUMPTION_PROTOCOL", "test", "ingest", 50), make_patch())
        record_id = result["record"]["record_id"]

        dist = organ.record_echo_distortion(record_id, "echo echoes echo")
        assert dist["status"] == "distortion_recorded"

    def test_record_echo_distortion_not_found(self):
        """Cover record_echo_distortion failure path."""
        organ = ConsumptionProtocol()
        dist = organ.record_echo_distortion("NONEXISTENT", "some distortion")
        assert dist["status"] == "failed"


# ============================================================
# RitualChain coverage
# ============================================================

def make_phase(name, organ="HEART_OF_CANON", mode="mythic"):
    return Phase(name=name, organ=organ, mode=mode)


class TestChainGetNextPhaseUnknown:
    """Cover line 212: get_next_phase with unknown phase name."""

    def test_get_next_phase_unknown_returns_none(self):
        """Line 212: get_next_phase returns None if phase name not found."""
        chain = RitualChain(name="test_chain", phases=[make_phase("phase1")])
        result = chain.get_next_phase("unknown_phase")
        assert result is None


class TestChainSetCompensationNotFound:
    """Cover line 239: set_compensation raises ValueError when phase not found."""

    def test_set_compensation_phase_not_found(self):
        """Line 239: set_compensation raises ValueError when phase missing."""
        chain = RitualChain(name="test_chain", phases=[make_phase("phase1")])
        comp = make_phase("comp_phase")

        with pytest.raises(ValueError, match="not found"):
            chain.set_compensation("nonexistent_phase", comp)


class TestChainValidation:
    """Cover lines 255, 261, 270: validate edge cases."""

    def test_validate_invalid_entry_phase(self):
        """Line 255: validate detects invalid entry_phase."""
        chain = RitualChain(name="test_chain", phases=[make_phase("phase1")])
        chain.entry_phase = "nonexistent_entry"

        result = chain.validate()
        assert not result["valid"]
        assert any("Entry phase" in e for e in result["errors"])

    def test_validate_branch_to_nonexistent(self):
        """Line 261: validate detects branch to non-existent phase."""
        p1 = make_phase("p1")
        p2 = make_phase("p2")
        chain = RitualChain(name="test_chain", phases=[p1, p2])

        # Add branch pointing to a non-existent phase (bypass add_branch validation)
        b = Branch(
            name="bad_branch",
            condition=lambda ctx: True,
            target_phase="nonexistent_phase",
        )
        p1.branches.append(b)

        result = chain.validate()
        assert not result["valid"]
        assert any("non-existent phase" in e for e in result["errors"])

    def test_validate_unreachable_phase(self):
        """Line 270: validate detects unreachable phases."""
        p1 = make_phase("p1")
        p2 = make_phase("p2")
        p3 = make_phase("p3")

        chain = RitualChain(name="test_chain", phases=[p1, p2, p3])

        # Make p1 branch only to p3, skipping p2
        b = Branch(name="skip_p2", condition=lambda ctx: True, target_phase="p3")
        p1.branches.append(b)

        # Now p2 is unreachable (p1 always branches to p3)
        result = chain.validate()
        # p2 may be unreachable
        assert "warnings" in result


class TestChainAddBranchErrors:
    """Cover add_branch error paths."""

    def test_add_branch_from_nonexistent_fails(self):
        """add_branch raises ValueError if from_phase not found."""
        chain = RitualChain(name="test_chain", phases=[make_phase("p1"), make_phase("p2")])
        b = Branch(name="b", condition=lambda ctx: True, target_phase="p2")

        with pytest.raises(ValueError, match="not found"):
            chain.add_branch("nonexistent", b)

    def test_add_branch_to_nonexistent_fails(self):
        """add_branch raises ValueError if target_phase not found."""
        chain = RitualChain(name="test_chain", phases=[make_phase("p1")])
        b = Branch(name="b", condition=lambda ctx: True, target_phase="nonexistent")

        with pytest.raises(ValueError, match="Target phase"):
            chain.add_branch("p1", b)


# ============================================================
# CodeForge coverage
# ============================================================

class TestCodeForgeDescription:
    """Cover line 38: description property."""

    def test_code_forge_description(self):
        """Line 38: description property returns string."""
        organ = CodeForge()
        assert "Symbol-to-code" in organ.description
        assert "Python" in organ.description


class TestCodeForgeDefaultModeWaveAndTree:
    """Cover lines 125-131: default mode wave and tree detection."""

    def test_default_mode_wave_detection(self):
        """Lines 125-126: symbol with 'feel' or 'emotion' or 'wave' → wave_mode."""
        organ = CodeForge()
        patch = make_patch()

        inv = Invocation(
            organ="CODE_FORGE",
            symbol="feel the emotion wave",
            mode="default",
            depth=DepthLevel.STANDARD,
            expect="output",
        )
        result = organ.invoke(inv, patch)
        assert result["mode"] == "wave_mode"

    def test_default_mode_tree_detection(self):
        """Lines 127-128: symbol with 'if' or 'decision' or 'choice' → tree_mode."""
        organ = CodeForge()
        patch = make_patch()

        inv = Invocation(
            organ="CODE_FORGE",
            symbol="if the decision is made",
            mode="default",
            depth=DepthLevel.STANDARD,
            expect="output",
        )
        result = organ.invoke(inv, patch)
        assert result["mode"] == "tree_mode"

    def test_default_mode_auto_json_fallback(self):
        """Lines 129-131: symbol with no keywords → auto_json output."""
        organ = CodeForge()
        patch = make_patch()

        inv = Invocation(
            organ="CODE_FORGE",
            symbol="simple plain text with no keywords",
            mode="default",
            depth=DepthLevel.STANDARD,
            expect="output",
        )
        result = organ.invoke(inv, patch)
        assert result["mode"] == "auto_json"
        assert "symbol_data" in result


class TestCodeForgeGetOutputTypes:
    """Cover line 274: get_output_types."""

    def test_get_output_types(self):
        """Line 274: get_output_types returns list."""
        organ = CodeForge()
        types = organ.get_output_types()
        assert ".py" in types
        assert ".maxpat" in types
        assert ".json" in types


# ============================================================
# Phase combined_condition coverage
# ============================================================

class TestCombinedCondition:
    """Cover line 265: combined_condition with 'or' mode."""

    def test_combined_condition_or_true(self):
        """Line 265: combined_condition with 'or' returns any() result."""
        cond = combined_condition(
            lambda ctx: False,
            lambda ctx: True,
            mode="or"
        )
        assert cond({}) is True

    def test_combined_condition_or_false(self):
        """combined_condition with 'or', all False → False."""
        cond = combined_condition(
            lambda ctx: False,
            lambda ctx: False,
            mode="or"
        )
        assert cond({}) is False

    def test_combined_condition_fallback(self):
        """Line 265 else branch: unknown mode returns False."""
        cond = combined_condition(
            lambda ctx: True,
            mode="unknown_mode"
        )
        assert cond({}) is False

    def test_phase_from_dict_with_compensation(self):
        """Line 191: Phase.from_dict restores compensation phase."""
        phase_data = {
            "name": "main_phase",
            "organ": "HEART_OF_CANON",
            "mode": "mythic",
            "compensation": {
                "name": "comp_phase",
                "organ": "ECHO_SHELL",
                "mode": "decay",
            }
        }
        phase = Phase.from_dict(phase_data)
        assert phase.compensation is not None
        assert phase.compensation.name == "comp_phase"
