"""
Coverage tests for time_rules.py uncovered lines:
197-198, 309, 311, 346-351, 405
"""

import pytest
from rege.organs.time_rules import TimeRulesEngine, BloomCycleRecord, BloomSeason, SEASON_CONFIG
from rege.core.models import Invocation, Patch, DepthLevel
from datetime import datetime


def make_inv(symbol="", mode="default", charge=50, flags=None):
    return Invocation(
        organ="TIME_RULES",
        symbol=symbol,
        mode=mode,
        depth=DepthLevel.STANDARD,
        expect="output",
        charge=charge,
        flags=flags or [],
    )


def make_patch():
    p = Patch(input_node="test", output_node="TIME_RULES", tags=[], charge=50)
    p.depth = 5
    return p


class TestScheduleBloomInvalidDays:
    """Cover lines 197-198: ValueError in DAYS_ flag parsing."""

    def test_days_invalid_int_uses_default(self):
        """Lines 197-198: DAYS_abc → ValueError → default 7 days used."""
        organ = TimeRulesEngine()
        patch = make_patch()

        result = organ.invoke(make_inv("my symbol", "schedule", 60, ["DAYS_abc"]), patch)
        assert result["status"] == "bloom_scheduled"
        assert result["days_until_bloom"] == 7  # Default value


class TestDefaultTemporalWithCycleAndRecurrence:
    """Cover lines 309, 311: symbol_cycle and symbol_recurrence in default mode."""

    def test_default_mode_shows_symbol_cycle(self):
        """Line 309: default mode includes symbol_cycle when cycle exists."""
        organ = TimeRulesEngine()
        patch = make_patch()

        # Create a cycle for "mysymbol"
        organ.invoke(make_inv("mysymbol", "cycle", 70), patch)

        # Now call default mode with same symbol
        result = organ.invoke(make_inv("mysymbol", "default", 50), patch)
        assert result["status"] == "temporal_state"
        assert "symbol_cycle" in result

    def test_default_mode_shows_symbol_recurrence(self):
        """Line 311: default mode includes symbol_recurrence when recurrence tracked."""
        organ = TimeRulesEngine()
        patch = make_patch()

        # Track recurrence for symbol
        organ.invoke(make_inv("recurrsym", "recurrence", 50), patch)

        # Now call default mode with same symbol
        result = organ.invoke(make_inv("recurrsym", "default", 50), patch)
        assert result["status"] == "temporal_state"
        assert "symbol_recurrence" in result
        assert result["symbol_recurrence"] == 1

    def test_default_mode_both_cycle_and_recurrence(self):
        """Lines 309+311: both cycle and recurrence present."""
        organ = TimeRulesEngine()
        patch = make_patch()

        # Create cycle and track recurrence for same symbol
        organ.invoke(make_inv("combosym", "cycle", 70), patch)
        organ.invoke(make_inv("combosym", "recurrence", 70), patch)

        result = organ.invoke(make_inv("combosym", "default", 70), patch)
        assert "symbol_cycle" in result
        assert "symbol_recurrence" in result


class TestBackwardSeasonTransition:
    """Cover lines 346-351: backward season transition in _check_season_transition."""

    def test_backward_transition_flowering_to_dormant(self):
        """Lines 346-351: charge drops below FLOWERING range → backward season transition."""
        organ = TimeRulesEngine()
        patch = make_patch()

        # Create cycle in FLOWERING season (charge=70 → FLOWERING)
        organ.invoke(make_inv("flowtoseed", "cycle", 70), patch)
        cycle = organ._cycles["FLOWTOSEED"]
        assert cycle.season == BloomSeason.FLOWERING

        # Apply charge=10 (below FLOWERING's charge_range[0]=51) → backward transition
        result = organ._check_season_transition(cycle, 10)
        assert result["transitioned"] is True
        assert cycle.season == BloomSeason.DORMANT

    def test_backward_transition_via_cycle_mode(self):
        """Lines 346-351: cycle mode with very low charge triggers backward transition."""
        organ = TimeRulesEngine()
        patch = make_patch()

        # First create cycle in FLOWERING
        organ.invoke(make_inv("backtransym", "cycle", 70), patch)

        # Then call cycle with charge=10 → triggers backward transition
        result = organ.invoke(make_inv("backtransym", "cycle", 10), patch)
        assert result["status"] == "cycle_advanced"
        assert result["previous_season"] == "flowering"
        assert result["new_season"] in ("dormant", "sprouting")

    def test_backward_transition_same_season_no_change(self):
        """Lines 346-351: if new_season equals current, no transition."""
        organ = TimeRulesEngine()
        now = datetime.now()

        # Create a DORMANT cycle, apply charge=10 (still DORMANT)
        cycle = BloomCycleRecord(
            cycle_id="TEST",
            season=BloomSeason.DORMANT,
            recurrence=1,
            charge_threshold=20,
            started_at=now,
            last_transition=now,
        )
        # charge=10 → DORMANT, same as current → no transition
        result = organ._check_season_transition(cycle, 10)
        assert result["transitioned"] is False


class TestNormalizeKeyEmpty:
    """Cover line 405: _normalize_key with empty symbol."""

    def test_normalize_empty_string_returns_unnamed(self):
        """Line 405: empty symbol string → 'UNNAMED'."""
        organ = TimeRulesEngine()
        result = organ._normalize_key("")
        assert result == "UNNAMED"

    def test_normalize_empty_via_schedule_mode(self):
        """Line 405: calling schedule mode with empty symbol triggers _normalize_key('')."""
        organ = TimeRulesEngine()
        patch = make_patch()

        # Empty symbol triggers _normalize_key("") → "UNNAMED"
        result = organ.invoke(make_inv("", "schedule", 60), patch)
        assert result["status"] == "bloom_scheduled"
        assert result["schedule"]["symbol"] == "UNNAMED"
