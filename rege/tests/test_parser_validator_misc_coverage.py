"""
Coverage tests for:
- parser/invocation_parser.py: 66, 165-166, 171-172, 214, 228, 267-268
- parser/validator.py: 244
- core/models.py: 222, 224
- organs/registry.py: 76
- organs/base.py: 129
- protocols/enforcement.py: 139-145
"""

import pytest
from datetime import datetime
from rege.parser.invocation_parser import InvocationParser, parse_invocation, parse_invocation_chain
from rege.parser.validator import InvocationValidator
from rege.core.models import Invocation, Patch, DepthLevel
from rege.organs.registry import OrganRegistry
from rege.organs.base import OrganHandler
from rege.organs.heart_of_canon import HeartOfCanon
from rege.protocols.enforcement import LawEnforcer, Law
from rege.core.exceptions import OrganNotFoundError


def make_inv(organ="HEART_OF_CANON", symbol="test", mode="mythic", depth=DepthLevel.STANDARD):
    return Invocation(
        organ=organ,
        symbol=symbol,
        mode=mode,
        depth=depth,
        expect="output",
        charge=50,
    )


# ============================================================
# InvocationParser coverage
# ============================================================

class TestParserReturnsNoneWithoutOrganOrProtocol:
    """Cover line 66: parse() processes protocol invocation."""

    def test_parse_protocol_invocation(self):
        """Line 66: ::CALL_PROTOCOL (no CALL_ORGAN) → organ = 'PROTOCOL_xxx'."""
        parser = InvocationParser()
        text = "::CALL_PROTOCOL FUSE01"
        result = parser.parse(text)
        assert result is not None
        assert "PROTOCOL_FUSE01" in result.organ

    def test_parse_returns_none_no_organ_no_protocol(self):
        """Line 68: text with no ::CALL_ORGAN and no ::CALL_PROTOCOL → None."""
        parser = InvocationParser()
        result = parser.parse("This is just regular text without any invocation syntax")
        assert result is None

    def test_parse_returns_none_empty_string(self):
        """Line 68: empty text → None."""
        parser = InvocationParser()
        result = parser.parse("")
        assert result is None


class TestParserExtractCharge:
    """Cover lines 165-166: _extract_charge when CHARGE is present."""

    def test_extract_charge_from_text(self):
        """Lines 165-166: ::CHARGE 80 extracts charge value."""
        parser = InvocationParser()
        text = """::CALL_ORGAN HEART_OF_CANON
::WITH test symbol
::MODE mythic
::DEPTH standard
::EXPECT output
::CHARGE 80"""
        result = parser.parse(text)
        assert result is not None
        assert result.charge == 80

    def test_extract_charge_clamped_to_100(self):
        """Lines 165-166: charge > 100 is clamped to 100."""
        parser = InvocationParser()
        text = """::CALL_ORGAN HEART_OF_CANON
::WITH test
::MODE mythic
::DEPTH standard
::EXPECT output
::CHARGE 150"""
        result = parser.parse(text)
        assert result.charge == 100

    def test_extract_charge_clamped_to_0(self):
        """Lines 165-166: charge 0 stays at 0."""
        parser = InvocationParser()
        text = """::CALL_ORGAN HEART_OF_CANON
::WITH test
::MODE mythic
::DEPTH standard
::EXPECT output
::CHARGE 0"""
        result = parser.parse(text)
        assert result.charge == 0


class TestParserExtractOutputTo:
    """Cover lines 171-172: _extract_output_to."""

    def test_extract_output_to_present(self):
        """Lines 171-172: _extract_output_to finds OUTPUT_TO directive."""
        parser = InvocationParser()
        text = "::CALL_ORGAN HEART_OF_CANON ::OUTPUT_TO MIRROR_CABINET"
        result = parser._extract_output_to(text)
        assert result == "MIRROR_CABINET"

    def test_extract_output_to_absent(self):
        """Lines 171-172: _extract_output_to returns None when missing."""
        parser = InvocationParser()
        result = parser._extract_output_to("no output directive here")
        assert result is None


class TestParserExtractFragmentRefs:
    """Cover line 214: extract_fragment_refs with list pattern."""

    def test_extract_list_pattern_refs(self):
        """Line 214: extract_fragment_refs finds ["id1", "id2"] patterns."""
        parser = InvocationParser()
        text = 'Merge fragments: ["frag_alpha", "frag_beta"] into one'
        refs = parser.extract_fragment_refs(text)
        assert "frag_alpha" in refs
        assert "frag_beta" in refs

    def test_extract_version_refs(self):
        """Line 214: extract_fragment_refs finds Fragment_vX.Y patterns."""
        parser = InvocationParser()
        text = "Using Fragment_v2.6 and Memory_v1.0 as sources"
        refs = parser.extract_fragment_refs(text)
        assert "Fragment_v2.6" in refs
        assert "Memory_v1.0" in refs


class TestParserToPatchParams:
    """Cover line 228: to_patch_params."""

    def test_to_patch_params_returns_dict(self):
        """Line 228: to_patch_params returns valid patch parameters."""
        parser = InvocationParser()
        inv = make_inv()
        params = parser.to_patch_params(inv)
        assert "input_node" in params
        assert "output_node" in params
        assert "tags" in params
        assert "charge" in params
        assert params["output_node"] == "HEART_OF_CANON"


class TestParserConvenienceFunctions:
    """Cover lines 267-268: parse_invocation_chain convenience function."""

    def test_parse_invocation_chain_returns_list(self):
        """Lines 267-268: parse_invocation_chain parses chained text."""
        text = """::CALL_ORGAN HEART_OF_CANON
::WITH memory one
::MODE mythic
::DEPTH standard
::EXPECT output
::CALL_ORGAN MIRROR_CABINET
::WITH reflection
::MODE emotional_reflection
::DEPTH standard
::EXPECT fragment_map"""
        result = parse_invocation_chain(text)
        assert isinstance(result, list)
        assert len(result) == 2

    def test_parse_invocation_chain_empty(self):
        """Lines 267-268: empty text returns empty list."""
        result = parse_invocation_chain("no invocations here")
        assert result == []

    def test_parse_invocation_convenience(self):
        """parse_invocation (line ~253) convenience function."""
        text = """::CALL_ORGAN HEART_OF_CANON
::WITH test
::MODE mythic
::DEPTH standard
::EXPECT output"""
        result = parse_invocation(text)
        assert result is not None
        assert result.organ == "HEART_OF_CANON"


# ============================================================
# Validator coverage
# ============================================================

class TestValidatorInvalidDepth:
    """Cover line 244: invalid depth in validate()."""

    def test_invalid_depth_adds_error(self):
        """Line 244: depth not in DepthLevel → error added."""
        validator = InvocationValidator()
        inv = make_inv()
        # Manually set depth to an invalid value (bypass type system)
        object.__setattr__(inv, 'depth', "not_a_valid_depth")

        valid, errors = validator.validate(inv)
        # Should detect the invalid depth
        assert not valid or any("depth" in e.lower() or "Invalid" in e for e in errors)


# ============================================================
# Patch.from_dict coverage
# ============================================================

class TestPatchFromDictWithDates:
    """Cover lines 222, 224: Patch.from_dict with enqueued_at and processed_at."""

    def test_from_dict_with_enqueued_at(self):
        """Line 222: from_dict restores enqueued_at datetime."""
        now = datetime.now()
        data = {
            "input_node": "SRC",
            "output_node": "DST",
            "tags": [],
            "charge": 50,
            "enqueued_at": now.isoformat(),
        }
        patch = Patch.from_dict(data)
        assert patch.enqueued_at is not None
        assert abs((patch.enqueued_at - now).total_seconds()) < 1

    def test_from_dict_with_processed_at(self):
        """Line 224: from_dict restores processed_at datetime."""
        now = datetime.now()
        data = {
            "input_node": "SRC",
            "output_node": "DST",
            "tags": [],
            "charge": 50,
            "processed_at": now.isoformat(),
        }
        patch = Patch.from_dict(data)
        assert patch.processed_at is not None

    def test_from_dict_with_both_dates(self):
        """Lines 222+224: from_dict with both enqueued_at and processed_at."""
        now = datetime.now()
        data = {
            "input_node": "SRC",
            "output_node": "DST",
            "tags": [],
            "charge": 75,
            "enqueued_at": now.isoformat(),
            "processed_at": now.isoformat(),
        }
        patch = Patch.from_dict(data)
        assert patch.enqueued_at is not None
        assert patch.processed_at is not None


# ============================================================
# OrganRegistry coverage
# ============================================================

class TestOrganRegistryGetOrRaise:
    """Cover line 76: get_or_raise raises when organ not found."""

    def test_get_or_raise_raises_when_not_found(self):
        """Line 76: get_or_raise raises OrganNotFoundError for unknown organ."""
        registry = OrganRegistry()
        with pytest.raises(OrganNotFoundError):
            registry.get_or_raise("NONEXISTENT_ORGAN")

    def test_get_or_raise_returns_when_found(self):
        """get_or_raise returns handler when registered."""
        registry = OrganRegistry()
        organ = HeartOfCanon()
        registry.register(organ)
        result = registry.get_or_raise("HEART_OF_CANON")
        assert result is organ


# ============================================================
# OrganHandler base.py coverage
# ============================================================

class TestOrganBaseRestoreStateWithLastInvocation:
    """Cover line 129: restore_state with last_invocation present."""

    def test_restore_state_with_last_invocation(self):
        """Line 129: restore_state restores last_invocation datetime."""
        organ = HeartOfCanon()

        # Build state with last_invocation
        now = datetime.now()
        state = {
            "invocation_count": 5,
            "last_invocation": now.isoformat(),
            "state": {},
        }
        organ.restore_state(state)

        assert organ._invocation_count == 5
        assert organ._last_invocation is not None
        assert abs((organ._last_invocation - now).total_seconds()) < 1

    def test_restore_state_without_last_invocation(self):
        """restore_state without last_invocation doesn't set it."""
        organ = HeartOfCanon()
        state = {
            "invocation_count": 3,
            "state": {},
        }
        organ.restore_state(state)
        assert organ._invocation_count == 3
        assert organ._last_invocation is None


# ============================================================
# LawEnforcer enforcement.py coverage
# ============================================================

class ViolatingLaw(Law):
    """A law that always detects a violation."""
    def check(self, context):
        return f"Test violation detected in context"


class TestLawEnforcerDetectViolation:
    """Cover lines 139-145: violations.append in detect_violation."""

    def test_detect_violation_with_custom_law(self):
        """Lines 139-145: custom law returns violation → appended to violations."""
        enforcer = LawEnforcer()
        violating_law = ViolatingLaw(
            "LAW_TEST", "Test Law",
            "Test law description",
            "Test consequence",
        )
        enforcer.register_law(violating_law)

        result = enforcer.detect_violation("test_action", {"some": "context"})
        assert result is not None
        assert "violations" in result
        assert len(result["violations"]) > 0
        assert result["violations"][0]["law_id"] == "LAW_TEST"
        assert violating_law.violations_count == 1

    def test_detect_violation_no_violation(self):
        """No violation when laws return None."""
        enforcer = LawEnforcer()
        result = enforcer.detect_violation("normal_action", {})
        assert result is None
