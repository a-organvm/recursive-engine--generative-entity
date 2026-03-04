"""
Coverage tests for:
- organs/analog_digital_engine.py: 319, 324, 342-343, 400, 420-423
- organs/chamber_commerce.py: 178, 312-320, 401-402, 430, 449
- organs/place_protocols.py: 295-298, 324, 361, 370
- organs/process_product.py: 351, 382, 384, 391-394, 412
"""

import pytest
from datetime import datetime
from rege.organs.analog_digital_engine import AnalogDigitalEngine
from rege.organs.chamber_commerce import ChamberOfCommerce, SymbolicCurrency
from rege.organs.place_protocols import PlaceProtocols, RitualPlace
from rege.organs.process_product import ProcessProductConverter, VisibilityTier
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


def make_patch(depth=5):
    p = Patch(input_node="test", output_node="TEST", tags=[], charge=50)
    p.depth = depth
    return p


# ============================================================
# AnalogDigitalEngine coverage
# ============================================================

class TestAnalogDigitalDefaultStatusWithRecords:
    """Cover lines 319, 324: _default_status loops over records."""

    def test_default_status_with_records_iterates_tags_and_sources(self):
        """Lines 319, 324: tag_counts and source_counts incremented per record."""
        organ = AnalogDigitalEngine()
        patch = make_patch()

        # Create a record via encode mode
        organ.invoke(
            make_inv("ANALOG_DIGITAL", "my journal entry", "encode", 50, ["PAPER+"]),
            patch
        )

        # Now call default mode — iterates over records (hits lines 319 and 324)
        result = organ.invoke(
            make_inv("ANALOG_DIGITAL", "", "default", 50),
            patch
        )

        assert result["status"] == "engine_status"
        assert result["total_records"] >= 1
        # Lines 319/324: tag_counts and source_counts populated from records
        assert "by_sacred_tag" in result
        assert "by_source_type" in result


class TestAnalogDigitalExtractEntropyValueError:
    """Cover lines 342-343: ValueError in _extract_entropy."""

    def test_entropy_flag_with_invalid_int(self):
        """Lines 342-343: ENTROPY_abc → ValueError → default 50 used."""
        organ = AnalogDigitalEngine()
        patch = make_patch()

        # ENTROPY_abc → ValueError in int() → falls through to default 50
        result = organ.invoke(
            make_inv("ANALOG_DIGITAL", "my content", "encode", 50, ["ENTROPY_abc"]),
            patch
        )
        assert result["status"] in ("encoded", "protected")
        # Entropy defaulted to 50 (medium) — stored in record sub-dict
        assert result["record"]["entropy_level"] == 50


class TestAnalogDigitalGetRecord:
    """Cover line 400: get_record method."""

    def test_get_record_existing(self):
        """Line 400: get_record returns existing record."""
        organ = AnalogDigitalEngine()
        patch = make_patch()

        result = organ.invoke(
            make_inv("ANALOG_DIGITAL", "old notebook page", "encode", 40, ["PAPER+"]),
            patch
        )
        record_id = result["record"]["record_id"]

        # Line 400: get_record returns TranslationRecord
        record = organ.get_record(record_id)
        assert record is not None
        assert record.record_id == record_id

    def test_get_record_missing(self):
        """Line 400: get_record returns None for unknown ID."""
        organ = AnalogDigitalEngine()
        result = organ.get_record("NONEXISTENT_ID")
        assert result is None


class TestAnalogDigitalRestoreState:
    """Cover lines 420-423: restore_state method."""

    def test_restore_state_restores_protected_items_and_log(self):
        """Lines 420-423: restore_state() restores protected_items and translation_log."""
        organ = AnalogDigitalEngine()
        patch = make_patch()

        # Create some state
        organ.invoke(
            make_inv("ANALOG_DIGITAL", "precious item", "protect", 90),
            patch
        )
        state = organ.get_state()

        # Restore into fresh organ
        organ2 = AnalogDigitalEngine()
        organ2.restore_state(state)

        # Lines 420-423: protected_items and translation_log restored
        assert organ2._protected_items == organ._protected_items
        assert organ2._translation_log == organ._translation_log

    def test_restore_state_empty(self):
        """Lines 420-423: restore_state with empty state dict."""
        organ = AnalogDigitalEngine()
        organ.restore_state({"state": {}})
        assert organ._protected_items == []
        assert organ._translation_log == []


# ============================================================
# ChamberOfCommerce coverage
# ============================================================

class TestChamberCommerceCommonTier:
    """Cover line 178: tier = 'common' in _assess_value."""

    def test_value_common_tier(self):
        """Line 178: value >= 20 and < 40 → 'common' tier."""
        organ = ChamberOfCommerce()
        patch = make_patch(depth=5)  # recursion_depth = 6

        # value = (6*2 + 20) - 10 = 22 → "common" (>= 20, < 40)
        result = organ.invoke(
            make_inv("CHAMBER_COMMERCE", "small artifact", "value", 20),
            patch
        )
        assert result["status"] == "valued"
        assert result["tier"] == "common"


class TestChamberCommerceDailyMintLimit:
    """Cover lines 312-320: daily mint limit handling."""

    def test_mint_limit_reached_returns_failed(self):
        """Lines 312-316: daily_total >= max → 'Daily mint limit reached'."""
        organ = ChamberOfCommerce()
        patch = make_patch()

        # Manually fill today's mint quota to the max
        today = datetime.now().strftime("%Y-%m-%d")
        organ._daily_minted[today] = 100  # max_daily_mint = 100

        result = organ.invoke(
            make_inv("CHAMBER_COMMERCE", "SELF", "mint", 60),
            patch
        )
        # Lines 312-316: available <= 0 → status "failed"
        assert result["status"] == "failed"
        assert "Daily mint limit reached" in result["error"]

    def test_mint_limit_adjusts_amount(self):
        """Line 320: available > 0 but total would exceed → mint_amount capped."""
        organ = ChamberOfCommerce()
        patch = make_patch()

        # Set daily_minted to just below max: 99 minted, max=100
        today = datetime.now().strftime("%Y-%m-%d")
        organ._daily_minted[today] = 99

        # Mint with charge=100: base_mint = (100-50)//5 = 10 → would exceed limit
        result = organ.invoke(
            make_inv("CHAMBER_COMMERCE", "SELF", "mint", 100),
            patch
        )
        # Line 320: mint_amount adjusted to available=1
        assert result["status"] == "minted"
        assert result["mint"]["amount"] == 1


class TestChamberCommerceCirculationLoop:
    """Cover lines 401-402: currency circulation loop in _default_economy."""

    def test_default_economy_with_balances_iterates_circulation(self):
        """Lines 401-402: entity_balances.items() iteration fills circulation dict."""
        organ = ChamberOfCommerce()

        # Grant a balance so _balances is non-empty with currency entries
        organ.grant_balance("SELF", SymbolicCurrency.MIRRORCREDITS, 25)

        patch = make_patch()
        result = organ.invoke(
            make_inv("CHAMBER_COMMERCE", "", "default", 50),
            patch
        )

        assert result["status"] == "economy_status"
        # Lines 401-402: circulation populated from balances
        assert "currency_in_circulation" in result
        assert result["currency_in_circulation"].get("mirrorcredits", 0) >= 25


class TestChamberCommerceDebitNewEntity:
    """Cover line 430: _debit creates balance dict for new entity."""

    def test_debit_creates_balance_dict_for_new_entity(self):
        """Line 430: entity not in _balances → create empty dict."""
        organ = ChamberOfCommerce()
        assert "PHANTOM_ENTITY" not in organ._balances

        # Call _debit directly on a new entity
        organ._debit("PHANTOM_ENTITY", SymbolicCurrency.MIRRORCREDITS, 5)

        # Line 430: entity's balance dict created
        assert "PHANTOM_ENTITY" in organ._balances
        # Debit clamped to 0 (no existing balance)
        assert organ._balances["PHANTOM_ENTITY"].get("mirrorcredits", 0) == 0


class TestChamberCommerceGetOutputTypes:
    """Cover line 449: get_output_types."""

    def test_get_output_types(self):
        """Line 449: get_output_types returns expected list."""
        organ = ChamberOfCommerce()
        types = organ.get_output_types()
        assert "valuation" in types
        assert "trade_record" in types
        assert "mint_record" in types
        assert "economy_status" in types


# ============================================================
# PlaceProtocols coverage
# ============================================================

class TestPlaceProtocolsCustomPlaceInMap:
    """Cover lines 295-298: custom place used in _map_location."""

    def test_map_with_current_zone_as_custom_place(self):
        """Lines 295-298: current_zone in _custom_places → custom zone_config returned."""
        organ = PlaceProtocols()
        patch = make_patch()

        # Register a custom place
        custom_place = RitualPlace(
            place_id="",
            zone="MY_STUDIO",
            functions=["creation", "focus"],
            time_behavior="deep_work",
            charge_modifier=10,
        )
        organ.register_custom_place(custom_place)

        # Navigate to the custom place directly
        organ._current_place = "MY_STUDIO"

        # Map mode: current_zone = "MY_STUDIO" → in _custom_places (lines 295-296)
        result = organ.invoke(
            make_inv("PLACE_PROTOCOLS", "", "map", 50),
            patch
        )
        assert result["status"] == "mapped"
        assert result["current_zone"] == "MY_STUDIO"
        assert result["zone_config"]["zone"] == "MY_STUDIO"

    def test_map_with_unknown_current_zone_falls_to_here(self):
        """Line 298: current_zone not in CANONICAL_ZONES or custom → HERE config."""
        organ = PlaceProtocols()
        patch = make_patch()

        # Set _current_place to something not in canonical or custom zones
        organ._current_place = "UNKNOWN_ZONE_XYZ"

        # Lines 295-298: elif not found → zone_config = CANONICAL_ZONES["HERE"]
        result = organ.invoke(
            make_inv("PLACE_PROTOCOLS", "", "map", 50),
            patch
        )
        assert result["status"] == "mapped"
        # Should use HERE as fallback
        assert "zone_config" in result


class TestPlaceProtocolsCustomZoneInRules:
    """Cover line 324: custom zone config in _get_zone_rules."""

    def test_rules_for_custom_zone(self):
        """Line 324: zone in _custom_places → custom place to_dict() used."""
        organ = PlaceProtocols()
        patch = make_patch()

        # Register a custom place
        custom_place = RitualPlace(
            place_id="",
            zone="THE_WORKSHOP",
            functions=["build", "test"],
            time_behavior="focused",
            charge_modifier=5,
        )
        organ.register_custom_place(custom_place)

        # Query rules for the custom zone
        result = organ.invoke(
            make_inv("PLACE_PROTOCOLS", "THE_WORKSHOP", "rules", 50),
            patch
        )
        # Line 324: custom zone rules retrieved
        assert result["status"] == "rules_retrieved"
        assert result["zone"] == "THE_WORKSHOP"
        assert "zone_config" in result


class TestPlaceProtocolsCalculateTimeInZone:
    """Cover lines 361, 370: _calculate_time_in_zone edge cases."""

    def test_calculate_time_no_history_returns_none(self):
        """Line 361: empty _place_history → return None."""
        organ = PlaceProtocols()
        # No history at all (fresh organ with just default _current_place)
        organ._place_history = []
        result = organ._calculate_time_in_zone("THERE")
        assert result is None

    def test_calculate_time_zone_not_in_history_returns_none(self):
        """Line 370: zone not found in history entries → return None."""
        organ = PlaceProtocols()
        patch = make_patch()

        # Set current place to THERE without recording entry
        organ._current_place = "THERE"

        # Exit: records {from: THERE, to: HERE} in history
        # _calculate_time_in_zone("THERE") looks in history[:-1] which is empty
        result = organ.invoke(
            make_inv("PLACE_PROTOCOLS", "", "exit", 50),
            patch
        )
        assert result["status"] == "exited"
        # time_spent is None (line 370): no prior entry_to_place="THERE" in history
        assert result["time_spent"] is None


# ============================================================
# ProcessProductConverter coverage
# ============================================================

class TestProcessProductSuggestFormatsOutOfRange:
    """Cover line 351: _suggest_formats returns fallback DROP."""

    def test_suggest_formats_out_of_range_returns_drop(self):
        """Line 351: charge outside all FORMAT_RECOMMENDATIONS ranges → [DROP]."""
        from rege.organs.process_product import ProductFormat
        organ = ProcessProductConverter()

        # charge = 101 → outside all ranges (all ranges go to 100)
        result = organ._suggest_formats(101)
        assert result == [ProductFormat.DROP]

    def test_suggest_formats_negative_returns_drop(self):
        """Line 351: negative charge → [DROP]."""
        from rege.organs.process_product import ProductFormat
        organ = ProcessProductConverter()
        result = organ._suggest_formats(-1)
        assert result == [ProductFormat.DROP]


class TestProcessProductDeterminesTierFromFlags:
    """Cover lines 382, 384: PAID+ and COLLECTIBLE+ flag tiers in _determine_tier."""

    def test_paid_flag_returns_paid_tier(self):
        """Line 382: PAID+ in flags → VisibilityTier.PAID."""
        organ = ProcessProductConverter()
        result = organ._determine_tier(["PAID+"], 50)
        assert result == VisibilityTier.PAID

    def test_collectible_flag_returns_collectible_tier(self):
        """Line 384: COLLECTIBLE+ in flags → VisibilityTier.COLLECTIBLE."""
        organ = ProcessProductConverter()
        result = organ._determine_tier(["COLLECTIBLE+"], 50)
        assert result == VisibilityTier.COLLECTIBLE


class TestProcessProductChargeBasedTier:
    """Cover lines 391-394: charge-based tier assignment in _determine_tier."""

    def test_charge_86_plus_returns_collectible(self):
        """Line 391: charge >= 86 → VisibilityTier.COLLECTIBLE."""
        organ = ProcessProductConverter()
        result = organ._determine_tier([], 90)
        assert result == VisibilityTier.COLLECTIBLE

    def test_charge_71_returns_paid(self):
        """Line 392: charge >= 71 (but < 86) → VisibilityTier.PAID."""
        organ = ProcessProductConverter()
        result = organ._determine_tier([], 75)
        assert result == VisibilityTier.PAID

    def test_charge_51_returns_public(self):
        """Line 393: charge >= 51 (but < 71) → VisibilityTier.PUBLIC."""
        organ = ProcessProductConverter()
        result = organ._determine_tier([], 60)
        assert result == VisibilityTier.PUBLIC

    def test_charge_below_51_returns_sacred(self):
        """Line 394: charge < 51 → VisibilityTier.SACRED."""
        organ = ProcessProductConverter()
        result = organ._determine_tier([], 30)
        assert result == VisibilityTier.SACRED


class TestProcessProductGetOutputTypes:
    """Cover line 412: get_output_types."""

    def test_get_output_types(self):
        """Line 412: get_output_types returns expected list."""
        organ = ProcessProductConverter()
        types = organ.get_output_types()
        assert "readiness_report" in types
        assert "product" in types
        assert "tier_assignment" in types
        assert "format_list" in types
