"""
Tests for Interlocutor Engine organ.

Based on: RE-GE_AAW_CORE_09_INTERLOCUTOR_PROTOCOLS.md

Covers all 5 dialogue modes, consent management, law enforcement
(LAW_61–LAW_64), state management, and enum values.
"""

import pytest
from datetime import datetime

from rege.organs.interlocutor import (
    InterlocutorEngine,
    DialogueEntry,
    ConsentRecord,
    InterlocutionMode,
    IntentionType,
    RiskLevel,
    ConsentLevel,
)
from rege.core.models import Invocation, Patch, DepthLevel


@pytest.fixture
def engine():
    """Create a fresh InterlocutorEngine instance."""
    return InterlocutorEngine()


@pytest.fixture
def patch():
    """Create a test patch."""
    return Patch(
        input_node="TEST",
        output_node="INTERLOCUTOR",
        tags=["TEST+"],
        depth=5,
    )


def make_invocation(symbol="", mode="default", charge=50, flags=None):
    """Helper to create test invocations."""
    return Invocation(
        organ="INTERLOCUTOR",
        symbol=symbol,
        mode=mode,
        charge=charge,
        depth=DepthLevel.STANDARD,
        expect="dialogue_entry",
        flags=flags or [],
    )


# ---------------------------------------------------------------------------
# Basics
# ---------------------------------------------------------------------------

class TestInterlocutorEngineBasics:

    def test_name(self, engine):
        assert engine.name == "INTERLOCUTOR"

    def test_description(self, engine):
        desc = engine.description.lower()
        assert "ghost" in desc or "dialogue" in desc

    def test_valid_modes(self, engine):
        modes = engine.get_valid_modes()
        for mode in ["possession", "summoning", "mirroring", "mask-shift", "multiplicity", "consent"]:
            assert mode in modes

    def test_output_types(self, engine):
        types = engine.get_output_types()
        for t in ["dialogue_entry", "possession_log", "ghost_response"]:
            assert t in types


# ---------------------------------------------------------------------------
# DialogueEntry dataclass
# ---------------------------------------------------------------------------

class TestDialogueEntryDataclass:

    def test_auto_id_generation(self):
        entry = DialogueEntry(
            entry_id="",
            subject="TestSubject",
            mode=InterlocutionMode.POSSESSION,
            intention=IntentionType.ASK,
            risk_level=RiskLevel.LOW,
            entry_timestamp=datetime.now(),
        )
        assert entry.entry_id.startswith("DIAL_")
        assert len(entry.entry_id) > 5

    def test_to_dict_fields(self):
        entry = DialogueEntry(
            entry_id="DIAL_TEST",
            subject="TestGhost",
            mode=InterlocutionMode.SUMMONING,
            intention=IntentionType.CLARIFY,
            risk_level=RiskLevel.MEDIUM,
            entry_timestamp=datetime.now(),
        )
        d = entry.to_dict()
        assert d["entry_id"] == "DIAL_TEST"
        assert d["mode"] == "summoning"
        assert d["risk_level"] == "medium"
        assert d["status"] == "active"
        assert d["echoed_back"] is False
        assert d["log_required"] is False

    def test_close_sets_fields(self):
        entry = DialogueEntry(
            entry_id="DIAL_CLOSE",
            subject="ClosingGhost",
            mode=InterlocutionMode.MIRRORING,
            intention=IntentionType.DECODE,
            risk_level=RiskLevel.LOW,
            entry_timestamp=datetime.now(),
        )
        entry.close("output text", echoed=True)
        assert entry.status == "closed"
        assert entry.exit_timestamp is not None
        assert entry.echoed_back is True
        assert entry.resulting_output == "output text"

    def test_seal_sets_status(self):
        entry = DialogueEntry(
            entry_id="DIAL_SEAL",
            subject="SealedGhost",
            mode=InterlocutionMode.MASK_SHIFT,
            intention=IntentionType.EMBODY,
            risk_level=RiskLevel.VOLATILE,
            entry_timestamp=datetime.now(),
        )
        entry.seal()
        assert entry.status == "sealed"


# ---------------------------------------------------------------------------
# ConsentRecord dataclass
# ---------------------------------------------------------------------------

class TestConsentRecordDataclass:

    def test_auto_id_generation(self):
        record = ConsentRecord(
            record_id="",
            subject_name="Test Friend",
            consent_level=ConsentLevel.FULL,
        )
        assert record.record_id.startswith("CONSENT_")

    def test_revoke_sets_fields(self):
        record = ConsentRecord(
            record_id="CONSENT_TEST",
            subject_name="Revoked Friend",
            consent_level=ConsentLevel.FULL,
        )
        record.revoke("Testing revocation")
        assert record.consent_level == ConsentLevel.REVOKED
        assert record.withdrawn_at is not None
        assert "REVOKED" in record.notes

    def test_to_dict(self):
        record = ConsentRecord(
            record_id="CONSENT_DICT",
            subject_name="DictFriend",
            consent_level=ConsentLevel.LIMITED,
        )
        d = record.to_dict()
        assert d["record_id"] == "CONSENT_DICT"
        assert d["consent_level"] == "limited"
        assert d["withdrawn_at"] is None


# ---------------------------------------------------------------------------
# POSSESSION mode
# ---------------------------------------------------------------------------

class TestPossessionMode:

    def test_possession_basic(self, engine, patch):
        inv = make_invocation("TestGhost", "possession", charge=60)
        result = engine.invoke(inv, patch)
        assert result["status"] == "possession_active"
        assert result["entry"]["subject"] == "TestGhost"
        assert result["entry"]["mode"] == "possession"

    def test_possession_volatile_enforces_law64(self, engine, patch):
        inv = make_invocation("VolatileGhost", "possession", charge=90, flags=["VOLATILE+"])
        result = engine.invoke(inv, patch)
        assert result["law_64_enforced"] is True
        assert result["entry"]["log_required"] is True
        assert engine._volatile_possession_count == 1
        assert len(engine._possession_history) == 1

    def test_possession_volatile_log_contains_law_field(self, engine, patch):
        inv = make_invocation("LogGhost", "possession", charge=90, flags=["VOLATILE+"])
        engine.invoke(inv, patch)
        assert engine._possession_history[0]["law"] is not None

    def test_possession_non_volatile_no_log(self, engine, patch):
        inv = make_invocation("SafeGhost", "possession", charge=90)
        result = engine.invoke(inv, patch)
        assert result["law_64_enforced"] is False
        assert result["entry"]["log_required"] is False
        assert engine._volatile_possession_count == 0
        assert len(engine._possession_history) == 0

    def test_possession_full_embodiment_critical(self, engine, patch):
        inv = make_invocation("DeepGhost", "possession", charge=90)
        result = engine.invoke(inv, patch)
        assert result["embodiment_depth"] == "full_possession"

    def test_possession_deep_embodiment_intense(self, engine, patch):
        inv = make_invocation("IntenseGhost", "possession", charge=75)
        result = engine.invoke(inv, patch)
        assert result["embodiment_depth"] == "deep_embodiment"

    def test_possession_standard_active(self, engine, patch):
        inv = make_invocation("StdGhost", "possession", charge=60)
        result = engine.invoke(inv, patch)
        assert result["embodiment_depth"] == "standard_dialogue"

    def test_possession_light_low_charge(self, engine, patch):
        inv = make_invocation("LightGhost", "possession", charge=30)
        result = engine.invoke(inv, patch)
        assert result["embodiment_depth"] == "light_contact"

    def test_possession_increments_both_counters(self, engine, patch):
        inv = make_invocation("CountGhost", "possession", charge=50)
        engine.invoke(inv, patch)
        assert engine._total_dialogues == 1
        assert engine._total_possessions == 1

    def test_possession_adds_to_active_dialogues(self, engine, patch):
        inv = make_invocation("ActiveGhost", "possession", charge=50)
        result = engine.invoke(inv, patch)
        assert result["active_dialogue_id"] in engine._active_dialogues


# ---------------------------------------------------------------------------
# SUMMONING mode
# ---------------------------------------------------------------------------

class TestSummoningMode:

    def test_summoning_basic(self, engine, patch):
        inv = make_invocation("SummonedEntity", "summoning", charge=60)
        result = engine.invoke(inv, patch)
        assert result["status"] == "summoned"
        assert result["entry"]["subject"] == "SummonedEntity"
        assert result["law_62_enforced"] is True

    def test_summoning_provides_ghost_response(self, engine, patch):
        inv = make_invocation("ResponseGhost", "summoning", charge=60)
        result = engine.invoke(inv, patch)
        assert "ResponseGhost" in result["ghost_response"]

    def test_summoning_first_call_loop_valid(self, engine, patch):
        inv = make_invocation("LoopGhost", "summoning", charge=60)
        result = engine.invoke(inv, patch)
        assert result["loop_validated"] is True

    def test_summoning_duplicate_detects_loop(self, engine, patch):
        """LAW_62: Same ghost summoned twice should flag loop."""
        engine.invoke(make_invocation("DupGhost", "summoning", charge=60), patch)
        result = engine.invoke(make_invocation("DupGhost", "summoning", charge=60), patch)
        assert result["loop_validated"] is False
        assert "LOOP WARNING" in result["ghost_response"]

    def test_summoning_echoed_back_true(self, engine, patch):
        inv = make_invocation("EchoGhost", "summoning", charge=60)
        result = engine.invoke(inv, patch)
        assert result["entry"]["echoed_back"] is True

    def test_summoning_critical_response(self, engine, patch):
        inv = make_invocation("CritGhost", "summoning", charge=90)
        result = engine.invoke(inv, patch)
        assert "critical" in result["ghost_response"].lower()

    def test_summoning_low_charge_whispers(self, engine, patch):
        inv = make_invocation("WhisperGhost", "summoning", charge=20)
        result = engine.invoke(inv, patch)
        resp = result["ghost_response"].lower()
        assert "whispers" in resp or "faint" in resp


# ---------------------------------------------------------------------------
# MIRRORING mode
# ---------------------------------------------------------------------------

class TestMirroringMode:

    def test_mirroring_basic(self, engine, patch):
        inv = make_invocation("MirrorSubject", "mirroring", charge=60)
        result = engine.invoke(inv, patch)
        assert result["status"] == "mirroring_active"

    def test_mirroring_self_altered_invariant(self, engine, patch):
        """LAW_63: self_altered is always True regardless of charge."""
        for charge in [10, 30, 50, 70, 90]:
            inv = make_invocation("AnySub", "mirroring", charge=charge)
            result = engine.invoke(inv, patch)
            assert result["self_altered"] is True
            assert result["law_63_enforced"] is True

    def test_mirroring_reflection_contains_subject(self, engine, patch):
        inv = make_invocation("ReflectSubject", "mirroring", charge=60)
        result = engine.invoke(inv, patch)
        assert "ReflectSubject" in result["reflection"]

    def test_mirroring_distortion_levels(self, engine, patch):
        cases = [
            (90, "critical_distortion"),
            (75, "intense_distortion"),
            (60, "moderate_distortion"),
            (30, "low_distortion"),
        ]
        for charge, expected in cases:
            inv = make_invocation("DistSub", "mirroring", charge=charge)
            result = engine.invoke(inv, patch)
            assert result["emotional_distortion"] == expected

    def test_mirroring_remix_flag(self, engine, patch):
        inv = make_invocation("RemixSub", "mirroring", charge=60, flags=["REMIX+"])
        result = engine.invoke(inv, patch)
        assert "REMIX+" in result["symbolic_distortion"]

    def test_mirroring_echo_flag(self, engine, patch):
        inv = make_invocation("EchoSub", "mirroring", charge=60, flags=["ECHO+"])
        result = engine.invoke(inv, patch)
        assert "ECHO+" in result["symbolic_distortion"]

    def test_mirroring_fuse_flag(self, engine, patch):
        inv = make_invocation("FuseSub", "mirroring", charge=60, flags=["FUSE+"])
        result = engine.invoke(inv, patch)
        assert "FUSE+" in result["symbolic_distortion"]


# ---------------------------------------------------------------------------
# MASK-SHIFT mode
# ---------------------------------------------------------------------------

class TestMaskShiftMode:

    def test_mask_shift_basic(self, engine, patch):
        inv = make_invocation("ShiftSubject", "mask-shift", charge=60)
        result = engine.invoke(inv, patch)
        assert result["status"] == "mask_shift_active"

    def test_mask_shift_underscore_alias(self, engine, patch):
        """mask_shift (underscore) should be treated identically to mask-shift."""
        inv = make_invocation("UnderSub", "mask_shift", charge=60)
        result = engine.invoke(inv, patch)
        assert result["status"] == "mask_shift_active"

    def test_mask_shift_extracts_mask_name(self, engine, patch):
        inv = make_invocation("MaskSub", "mask-shift", charge=60,
                              flags=["MASK_NAME_The_Jester"])
        result = engine.invoke(inv, patch)
        assert result["active_mask"] == "The Jester"
        assert "The Jester" in result["message"]

    def test_mask_shift_default_mask_name(self, engine, patch):
        inv = make_invocation("NoMaskSub", "mask-shift", charge=60)
        result = engine.invoke(inv, patch)
        assert result["active_mask"] == "Unnamed Mask"

    def test_mask_shift_interpretation_contains_subject(self, engine, patch):
        inv = make_invocation("InterpSub", "mask-shift", charge=75,
                              flags=["MASK_NAME_The_Sage"])
        result = engine.invoke(inv, patch)
        assert "InterpSub" in result["interpretation"]
        assert "The Sage" in result["interpretation"]

    def test_mask_shift_symbolic_distortion_set(self, engine, patch):
        inv = make_invocation("DistSub", "mask-shift", charge=60,
                              flags=["MASK_NAME_Shadow"])
        result = engine.invoke(inv, patch)
        assert "Shadow" in result["symbolic_distortion"]


# ---------------------------------------------------------------------------
# MULTIPLICITY mode
# ---------------------------------------------------------------------------

class TestMultiplicityMode:

    def test_multiplicity_basic(self, engine, patch):
        inv = make_invocation("MultiSubject", "multiplicity", charge=60)
        result = engine.invoke(inv, patch)
        assert result["status"] == "multiplicity_active"
        assert result["law_61_enforced"] is True

    def test_multiplicity_agent_count_by_charge(self, engine, patch):
        cases = [(90, 4), (75, 3), (60, 2), (30, 1)]
        for charge, expected in cases:
            inv = make_invocation("AgentSub", "multiplicity", charge=charge)
            result = engine.invoke(inv, patch)
            assert result["agent_count"] == expected, f"charge={charge}"

    def test_multiplicity_explicit_agents(self, engine, patch):
        inv = make_invocation("ExplicitSub", "multiplicity", charge=60,
                              flags=["AGENT_Ghost_Voice", "AGENT_Shadow_Self"])
        result = engine.invoke(inv, patch)
        assert result["agent_count"] == 2
        assert "Ghost Voice" in result["agents"]
        assert "Shadow Self" in result["agents"]

    def test_multiplicity_voices_match_agent_count(self, engine, patch):
        inv = make_invocation("VoiceSub", "multiplicity", charge=75)
        result = engine.invoke(inv, patch)
        assert len(result["voices"]) == result["agent_count"]

    def test_multiplicity_echoed_back_when_agents(self, engine, patch):
        inv = make_invocation("EchoMulti", "multiplicity", charge=60)
        result = engine.invoke(inv, patch)
        assert result["entry"]["echoed_back"] is True

    def test_multiplicity_law61_any_subject(self, engine, patch):
        """LAW_61: Any symbol is a valid subject."""
        for subject in ["a rock", "the number 7", "silence", "yesterday"]:
            inv = make_invocation(subject, "multiplicity", charge=60)
            result = engine.invoke(inv, patch)
            assert result["status"] == "multiplicity_active"


# ---------------------------------------------------------------------------
# CONSENT mode
# ---------------------------------------------------------------------------

class TestConsentMode:

    def test_consent_grant_full(self, engine, patch):
        inv = make_invocation("FriendNode", "consent", flags=["GRANT+", "CONSENT_FULL+"])
        result = engine.invoke(inv, patch)
        assert result["status"] == "consent_granted"
        assert result["record"]["consent_level"] == "full"
        assert "friendnode" in engine._consent_registry

    def test_consent_grant_limited(self, engine, patch):
        inv = make_invocation("LimitedFriend", "consent", flags=["GRANT+", "CONSENT_LIMITED+"])
        result = engine.invoke(inv, patch)
        assert result["record"]["consent_level"] == "limited"

    def test_consent_grant_defaults_to_symbolic_only(self, engine, patch):
        """Without explicit level flag, should default to conservative symbolic_only."""
        inv = make_invocation("CautiousFriend", "consent", flags=["GRANT+"])
        result = engine.invoke(inv, patch)
        assert result["record"]["consent_level"] == "symbolic_only"

    def test_consent_revoke(self, engine, patch):
        engine.invoke(make_invocation("RevokedFriend", "consent", flags=["GRANT+", "CONSENT_FULL+"]), patch)
        result = engine.invoke(make_invocation("RevokedFriend", "consent", flags=["REVOKE+"]), patch)
        assert result["status"] == "consent_revoked"
        assert engine._consent_registry["revokedfriend"].consent_level == ConsentLevel.REVOKED

    def test_consent_revoke_seals_active_dialogues(self, engine, patch):
        engine.invoke(make_invocation("SealFriend", "possession", charge=60), patch)
        engine.invoke(make_invocation("SealFriend", "consent", flags=["GRANT+"]), patch)
        result = engine.invoke(make_invocation("SealFriend", "consent", flags=["REVOKE+"]), patch)
        assert result["sealed_dialogues"] == 1

    def test_consent_revoke_not_found(self, engine, patch):
        inv = make_invocation("NoOneThere", "consent", flags=["REVOKE+"])
        result = engine.invoke(inv, patch)
        assert result["status"] == "not_found"

    def test_consent_check_full_can_possess(self, engine, patch):
        engine.invoke(make_invocation("FullFriend", "consent", flags=["GRANT+", "CONSENT_FULL+"]), patch)
        result = engine.invoke(make_invocation("FullFriend", "consent", flags=["CHECK+"]), patch)
        assert result["status"] == "consent_found"
        assert result["can_possess"] is True
        assert result["can_summon"] is True

    def test_consent_check_limited_cannot_possess(self, engine, patch):
        engine.invoke(make_invocation("LimFriend", "consent", flags=["GRANT+", "CONSENT_LIMITED+"]), patch)
        result = engine.invoke(make_invocation("LimFriend", "consent", flags=["CHECK+"]), patch)
        assert result["can_possess"] is False
        assert result["can_summon"] is True

    def test_consent_check_not_found(self, engine, patch):
        inv = make_invocation("UnknownFriend", "consent", flags=["CHECK+"])
        result = engine.invoke(inv, patch)
        assert result["status"] == "no_consent_record"

    def test_consent_list(self, engine, patch):
        engine.invoke(make_invocation("Friend1", "consent", flags=["GRANT+"]), patch)
        engine.invoke(make_invocation("Friend2", "consent", flags=["GRANT+"]), patch)
        result = engine.invoke(make_invocation("", "consent"), patch)
        assert result["status"] == "consent_registry"
        assert result["total"] == 2


# ---------------------------------------------------------------------------
# DEFAULT mode
# ---------------------------------------------------------------------------

class TestDefaultMode:

    def test_default_empty_engine(self, engine, patch):
        result = engine.invoke(make_invocation("", "default"), patch)
        assert result["status"] == "engine_status"
        assert result["total_dialogues"] == 0
        assert result["total_possessions"] == 0
        assert result["active_dialogues"] == 0

    def test_default_shows_active_count(self, engine, patch):
        engine.invoke(make_invocation("Ghost1", "possession", charge=60), patch)
        result = engine.invoke(make_invocation("", "default"), patch)
        assert result["total_dialogues"] == 1
        assert result["active_dialogues"] == 1

    def test_default_shows_laws(self, engine, patch):
        result = engine.invoke(make_invocation("", "default"), patch)
        laws = result["laws_active"]
        for law in ["LAW_61", "LAW_62", "LAW_63", "LAW_64"]:
            assert law in laws

    def test_default_mode_breakdown_present(self, engine, patch):
        result = engine.invoke(make_invocation("", "default"), patch)
        assert "mode_breakdown" in result
        assert "possession" in result["mode_breakdown"]


# ---------------------------------------------------------------------------
# Law enforcement (dedicated tests)
# ---------------------------------------------------------------------------

class TestLawEnforcement:

    def test_law_61_any_object_may_speak(self, engine, patch):
        """LAW_61: Every symbol contains a potential voice."""
        for subject in ["a rock", "the void", "my first bicycle", "grief"]:
            inv = make_invocation(subject, "multiplicity", charge=60)
            result = engine.invoke(inv, patch)
            assert result["status"] == "multiplicity_active"

    def test_law_62_loop_detected_on_duplicate_summon(self, engine, patch):
        """LAW_62: Ghost speech validated for recursive loops."""
        engine.invoke(make_invocation("LoopEntity", "summoning", charge=60), patch)
        result = engine.invoke(make_invocation("LoopEntity", "summoning", charge=60), patch)
        assert result["loop_validated"] is False

    def test_law_63_mirror_always_alters_self(self, engine, patch):
        """LAW_63: self_altered is invariant True for all mirroring."""
        for charge in [10, 50, 90]:
            inv = make_invocation("AnySub", "mirroring", charge=charge)
            result = engine.invoke(inv, patch)
            assert result["self_altered"] is True

    def test_law_64_volatile_possession_archived(self, engine, patch):
        """LAW_64: volatile possession must be logged to possession_history."""
        inv = make_invocation("LoggedEntity", "possession", charge=90, flags=["VOLATILE+"])
        engine.invoke(inv, patch)
        assert len(engine._possession_history) == 1

    def test_law_64_non_volatile_not_archived(self, engine, patch):
        """LAW_64: non-volatile possession must NOT appear in possession_history."""
        inv = make_invocation("SafeEntity", "possession", charge=90)
        engine.invoke(inv, patch)
        assert len(engine._possession_history) == 0

    def test_law_64_multiple_volatile_all_logged(self, engine, patch):
        for i in range(3):
            inv = make_invocation(f"Ghost{i}", "possession", charge=90, flags=["VOLATILE+"])
            engine.invoke(inv, patch)
        assert len(engine._possession_history) == 3
        assert engine._volatile_possession_count == 3


# ---------------------------------------------------------------------------
# State management
# ---------------------------------------------------------------------------

class TestStateManagement:

    def test_get_state_fields(self, engine, patch):
        engine.invoke(make_invocation("StateGhost", "possession", charge=60), patch)
        state = engine.get_state()
        for key in ["active_dialogues", "total_dialogues", "possession_history", "consent_registry"]:
            assert key in state["state"]

    def test_reset_clears_everything(self, engine, patch):
        engine.invoke(make_invocation("ResetGhost", "possession", charge=60, flags=["VOLATILE+"]), patch)
        engine.invoke(make_invocation("ResetFriend", "consent", flags=["GRANT+"]), patch)
        engine.reset()
        assert engine._total_dialogues == 0
        assert engine._total_possessions == 0
        assert len(engine._active_dialogues) == 0
        assert len(engine._possession_history) == 0
        assert len(engine._consent_registry) == 0
        assert engine._volatile_possession_count == 0

    def test_get_dialogue_by_id(self, engine, patch):
        inv = make_invocation("LookupGhost", "possession", charge=60)
        result = engine.invoke(inv, patch)
        entry_id = result["active_dialogue_id"]
        entry = engine.get_dialogue(entry_id)
        assert entry is not None
        assert entry.subject == "LookupGhost"


# ---------------------------------------------------------------------------
# Enum values
# ---------------------------------------------------------------------------

class TestEnumValues:

    def test_interlocution_modes(self):
        assert InterlocutionMode.POSSESSION.value == "possession"
        assert InterlocutionMode.SUMMONING.value == "summoning"
        assert InterlocutionMode.MIRRORING.value == "mirroring"
        assert InterlocutionMode.MASK_SHIFT.value == "mask-shift"
        assert InterlocutionMode.MULTIPLICITY.value == "multiplicity"

    def test_risk_levels(self):
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.MEDIUM.value == "medium"
        assert RiskLevel.VOLATILE.value == "volatile"

    def test_consent_levels(self):
        assert ConsentLevel.FULL.value == "full"
        assert ConsentLevel.LIMITED.value == "limited"
        assert ConsentLevel.SYMBOLIC_ONLY.value == "symbolic_only"
        assert ConsentLevel.REVOKED.value == "revoked"

    def test_intention_types(self):
        assert IntentionType.CLARIFY.value == "clarify"
        assert IntentionType.CHALLENGE.value == "challenge"
        assert IntentionType.EMBODY.value == "embody"
