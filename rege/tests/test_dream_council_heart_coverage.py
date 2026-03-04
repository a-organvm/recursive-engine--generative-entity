"""
Coverage tests for:
- dream_council.py: 68, 207, 211, 222, 224, 287, 310, 313
- heart_of_canon.py: 44, 62, 122, 247
"""

import pytest
from rege.organs.dream_council import DreamCouncil
from rege.organs.heart_of_canon import HeartOfCanon
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
# DreamCouncil coverage
# ============================================================

class TestDreamCouncilDescription:
    """Cover line 68: description property."""

    def test_description_property(self):
        """Line 68: description returns string with dream/prophecy content."""
        organ = DreamCouncil()
        desc = organ.description
        assert isinstance(desc, str)
        assert len(desc) > 0


class TestSynthesizeMeaningsEdgeCases:
    """Cover lines 207, 211: _synthesize_meanings edge cases."""

    def test_synthesize_empty_decodings(self):
        """Line 207: _synthesize_meanings with empty dict returns 'No symbols decoded'."""
        organ = DreamCouncil()
        result = organ._synthesize_meanings({})
        assert result == "No symbols decoded"

    def test_synthesize_single_meaning(self):
        """Line 211: _synthesize_meanings with one meaning returns it directly."""
        organ = DreamCouncil()
        result = organ._synthesize_meanings({"water": "emotion, unconscious"})
        assert result == "emotion, unconscious"

    def test_synthesize_multiple_meanings(self):
        """Multiple meanings combines them."""
        organ = DreamCouncil()
        result = organ._synthesize_meanings({
            "water": "emotion",
            "fire": "passion",
        })
        assert "Combined meaning" in result


class TestInterpretationWithHighCharge:
    """Cover lines 222, 224: _generate_interpretation with high charge."""

    def test_interpretation_critical_charge(self):
        """Line 222: charge >= 86 → 'critical urgency' in interpretation."""
        organ = DreamCouncil()
        result = organ.invoke(
            make_inv("DREAM_COUNCIL", "water fire mirror", "interpretation", 90),
            make_patch()
        )
        assert result["dream"]["interpretation"] is not None
        assert "critical urgency" in result["dream"]["interpretation"]

    def test_interpretation_intense_charge(self):
        """Line 224: charge >= 71 (but < 86) → 'demands attention' in interpretation."""
        organ = DreamCouncil()
        result = organ.invoke(
            make_inv("DREAM_COUNCIL", "water mirror fire", "interpretation", 75),
            make_patch()
        )
        assert "demands attention" in result["dream"]["interpretation"]

    def test_interpretation_low_charge(self):
        """Charge < 71 → 'gentle guidance' in interpretation."""
        organ = DreamCouncil()
        result = organ.invoke(
            make_inv("DREAM_COUNCIL", "water mirror", "interpretation", 50),
            make_patch()
        )
        assert "gentle guidance" in result["dream"]["interpretation"]


class TestProposeNullLawFromDream:
    """Cover line 287: _propose_law_from_dream returns None when no symbols."""

    def test_law_proposal_with_symbols(self):
        """Line 287: prophetic_lawmaking with symbols generates law."""
        organ = DreamCouncil()
        result = organ.invoke(
            make_inv("DREAM_COUNCIL", "water and fire speak", "prophetic_lawmaking", 80),
            make_patch()
        )
        # charge >= 71 triggers law proposal
        assert result["law_proposal"] is not None

    def test_law_proposal_none_when_no_symbols_match(self):
        """Line 287: _propose_law_from_dream returns None when dream.symbols is empty.

        We trigger this by passing a symbol with no known dictionary words,
        then prophetic_lawmaking tries to propose a law — but _extract_symbols
        returns ["unknown_glyph"] by default, which has a length, so proposal works.

        Instead, directly test _propose_law_from_dream with a dream that has no symbols.
        """
        organ = DreamCouncil()
        # Create a dream and clear its symbols manually
        from rege.organs.dream_council import Dream
        dream = Dream(content="xyz", charge=80)
        dream.symbols = []  # Empty symbols list
        result = organ._propose_law_from_dream(dream)
        assert result is None

    def test_low_charge_no_law_proposal(self):
        """Charge < 71 → no law proposal."""
        organ = DreamCouncil()
        result = organ.invoke(
            make_inv("DREAM_COUNCIL", "water and fire", "prophetic_lawmaking", 50),
            make_patch()
        )
        assert result["law_proposal"] is None


class TestDreamCouncilValidModes:
    """Cover lines 310, 313: get_valid_modes and get_output_types."""

    def test_get_valid_modes(self):
        """Line 310: get_valid_modes returns list."""
        organ = DreamCouncil()
        modes = organ.get_valid_modes()
        assert "prophetic_lawmaking" in modes
        assert "glyph_decode" in modes
        assert "interpretation" in modes

    def test_get_output_types(self):
        """Line 313: get_output_types returns list."""
        organ = DreamCouncil()
        types = organ.get_output_types()
        assert "law_proposal" in types
        assert "archive_symbol" in types
        assert "dream_map" in types


class TestDreamCouncilGlyphDecode:
    """Cover glyph_decode mode."""

    def test_glyph_decode_with_known_symbols(self):
        """Decode known symbols from content."""
        organ = DreamCouncil()
        result = organ.invoke(
            make_inv("DREAM_COUNCIL", "I saw water and fire in the mirror", "glyph_decode", 50),
            make_patch()
        )
        assert "decodings" in result
        assert "water" in result["decodings"] or "fire" in result["decodings"]
        assert result["synthesis"] != "No symbols decoded"

    def test_glyph_decode_no_known_symbols(self):
        """Decode with unknown content gives default."""
        organ = DreamCouncil()
        result = organ.invoke(
            make_inv("DREAM_COUNCIL", "xyzzy quux frobble", "glyph_decode", 50),
            make_patch()
        )
        assert "unknown_glyph" in result["symbols_found"]


# ============================================================
# HeartOfCanon coverage
# ============================================================

class TestHeartOfCanonDescription:
    """Cover line 44: description property."""

    def test_description_property(self):
        """Line 44: description returns meaningful string."""
        organ = HeartOfCanon()
        desc = organ.description
        assert "emotional" in desc.lower() or "canon" in desc.lower()
        assert isinstance(desc, str)


class TestHeartOfCanonDefaultMode:
    """Cover lines 62 and 122: default mode dispatch and _default_process."""

    def test_default_mode_calls_pulse_check(self):
        """Lines 62+122: invoke with unknown mode falls through to _default_process → pulse_check."""
        organ = HeartOfCanon()
        result = organ.invoke(
            make_inv("HEART_OF_CANON", "my sacred memory", "unknown_mode", 75),
            make_patch()
        )
        # pulse_check returns status field
        assert "status" in result
        assert result["status"] in ("emergent_canon", "canon_candidate", "echo", "glowing")

    def test_default_mode_low_charge(self):
        """Default mode with low charge returns echo."""
        organ = HeartOfCanon()
        result = organ.invoke(
            make_inv("HEART_OF_CANON", "faint memory", "default", 30),
            make_patch()
        )
        assert result["status"] == "echo"

    def test_default_mode_intense_charge(self):
        """Default mode with intense charge returns canon_candidate."""
        organ = HeartOfCanon()
        result = organ.invoke(
            make_inv("HEART_OF_CANON", "intense memory", "default", 80),
            make_patch()
        )
        assert result["status"] == "canon_candidate"


class TestHeartOfCanonOutputTypes:
    """Cover line 247: get_output_types."""

    def test_get_output_types(self):
        """Line 247: get_output_types returns list."""
        organ = HeartOfCanon()
        types = organ.get_output_types()
        assert "canon_event" in types
        assert "pulse_check" in types
        assert "archive_entry" in types
