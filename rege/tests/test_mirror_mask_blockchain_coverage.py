"""
Coverage tests for:
- organs/mirror_cabinet.py: 78, 120-122, 276, 279
- organs/mask_engine.py: 197-199, 376
- organs/blockchain_economy.py: 226-227, 340, 474, 478-484, 488-490
"""

import pytest
from rege.organs.mirror_cabinet import MirrorCabinet
from rege.organs.mask_engine import MaskEngine
from rege.organs.blockchain_economy import BlockchainEconomy
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
# MirrorCabinet coverage
# ============================================================

class TestMirrorCabinetDescription:
    """Cover line 78: description property."""

    def test_description_property(self):
        """Line 78: description returns meaningful string."""
        organ = MirrorCabinet()
        desc = organ.description
        assert isinstance(desc, str)
        assert len(desc) > 0
        assert "emotional" in desc.lower() or "contradiction" in desc.lower() or "shadow" in desc.lower()


class TestMirrorCabinetFusionEligible:
    """Cover lines 120-122: fusion_eligible block in _emotional_reflection."""

    def test_fusion_eligible_block_with_high_overlap(self):
        """Lines 120-122: 3+ overlapping fragments with charge >= 70 → fusion_eligible."""
        organ = MirrorCabinet()
        patch = make_patch()

        # First two calls create overlapping fragments (same charge, no fusion yet)
        organ.invoke(make_inv("MIRROR_CABINET", "recurring pattern emerges", "emotional_reflection", 80), patch)
        organ.invoke(make_inv("MIRROR_CABINET", "recurring loop returns", "emotional_reflection", 80), patch)

        # Third call: at least 2 overlapping fragments → fusion_eligible=True
        result = organ.invoke(
            make_inv("MIRROR_CABINET", "recurring cycle again", "emotional_reflection", 80),
            patch
        )
        # Lines 120-122: if fusion_eligible: result["fusion_eligible"] = True, ...
        assert result.get("fusion_eligible") is True
        assert "overlap_count" in result
        assert result["overlap_count"] >= 2
        assert result.get("recommended_action") == "trigger_fuse01"


class TestMirrorCabinetModes:
    """Cover lines 276, 279: get_valid_modes and get_output_types."""

    def test_get_valid_modes(self):
        """Line 276: get_valid_modes returns list with all modes."""
        organ = MirrorCabinet()
        modes = organ.get_valid_modes()
        assert "emotional_reflection" in modes
        assert "grief_mirroring" in modes
        assert "shadow_work" in modes

    def test_get_output_types(self):
        """Line 279: get_output_types returns list with expected types."""
        organ = MirrorCabinet()
        types = organ.get_output_types()
        assert "fragment_map" in types
        assert "law_suggestion" in types
        assert "reflection_sentence" in types


# ============================================================
# MaskEngine coverage
# ============================================================

class TestMaskEngineShiftRemovesActive:
    """Cover lines 197-199: _shift removes current active mask."""

    def test_shift_removes_active_mask(self):
        """Lines 197-199: when _active_mask is set and mask found, remove() is called."""
        organ = MaskEngine()
        patch = make_patch()

        # Create mask A via assembly
        result_a = organ.invoke(
            make_inv("MASK_ENGINE", "hero brave fight", "assembly", 70),
            patch
        )
        mask_a_id = result_a["mask"]["mask_id"]

        # Manually set mask A as active
        organ._active_mask = mask_a_id

        # Create mask B via assembly
        result_b = organ.invoke(
            make_inv("MASK_ENGINE", "sage wise truth", "assembly", 70),
            patch
        )
        mask_b_id = result_b["mask"]["mask_id"]

        # Shift to mask B using its ID — this should remove mask A (lines 197-199)
        result_shift = organ.invoke(
            make_inv("MASK_ENGINE", mask_b_id.lower(), "shift", 70),
            patch
        )

        # Lines 197-199 executed: mask A removed
        assert "removed" in result_shift
        assert result_shift["removed"]["mask_id"] == mask_a_id
        assert result_shift["removed"]["status"] == "removed"

    def test_shift_active_mask_not_in_masks_dict(self):
        """Lines 196-199: _active_mask set to stale ID → get() returns None → no remove."""
        organ = MaskEngine()
        patch = make_patch()

        # Set a stale (non-existent) active mask ID
        organ._active_mask = "MASK_NONEXISTENT"

        # Shift to a target that doesn't exist either → status "target_not_found"
        result = organ.invoke(
            make_inv("MASK_ENGINE", "unknown mask symbol", "shift", 50),
            patch
        )
        # No "removed" key because current was None
        assert "removed" not in result
        assert result["status"] == "target_not_found"


class TestMaskEngineGetActiveMaskNone:
    """Cover line 376: get_active_mask returns None when no active mask."""

    def test_get_active_mask_returns_none_when_bare(self):
        """Line 376: get_active_mask returns None when _active_mask is None."""
        organ = MaskEngine()
        result = organ.get_active_mask()
        assert result is None

    def test_get_active_mask_returns_mask_when_set(self):
        """Verify get_active_mask returns mask when one is active."""
        organ = MaskEngine()
        patch = make_patch()

        result_a = organ.invoke(
            make_inv("MASK_ENGINE", "creator make art", "assembly", 70),
            patch
        )
        mask_id = result_a["mask"]["mask_id"]
        organ._active_mask = mask_id

        active = organ.get_active_mask()
        assert active is not None
        assert active.mask_id == mask_id


# ============================================================
# BlockchainEconomy coverage
# ============================================================

class TestBlockchainVerifyHashMismatch:
    """Cover lines 226-227: hash mismatch in _verify_chain."""

    def test_verify_detects_hash_mismatch(self):
        """Lines 226-227: block with wrong previous_hash → errors appended."""
        organ = BlockchainEconomy()
        patch = make_patch()

        # Mint a block to get a second block in the chain
        organ.invoke(
            make_inv("BLOCKCHAIN_ECONOMY", "sacred memory", "mint", 80),
            patch
        )

        # Tamper with the second block's previous_hash
        assert len(organ._chain) >= 2
        organ._chain[1].previous_hash = "tampered_hash_0000000000000000"

        # Verify should detect the mismatch
        result = organ.invoke(
            make_inv("BLOCKCHAIN_ECONOMY", "", "verify", 50),
            patch
        )

        assert result["is_valid"] is False
        assert result["status"] == "corrupted"
        assert len(result["errors"]) > 0
        # Lines 226-227: error message contains "hash mismatch"
        assert any("hash mismatch" in e for e in result["errors"])


class TestBlockchainEvaluateContractNotFound:
    """Cover line 340: _evaluate_contract when contract not found."""

    def test_evaluate_nonexistent_contract(self):
        """Line 340: EVALUATE+ flag with non-existent contract_id → failed status."""
        organ = BlockchainEconomy()
        patch = make_patch()

        result = organ.invoke(
            make_inv(
                "BLOCKCHAIN_ECONOMY",
                "NONEXISTENT_CONTRACT_ID",
                "contract",
                50,
                ["EVALUATE+"]
            ),
            patch
        )

        # Line 340: contract not found → status "failed"
        assert result["status"] == "failed"
        assert "Contract not found" in result["error"]


class TestBlockchainGetOutputTypes:
    """Cover line 474: get_output_types."""

    def test_get_output_types(self):
        """Line 474: get_output_types returns expected list."""
        organ = BlockchainEconomy()
        types = organ.get_output_types()
        assert "block" in types
        assert "verification_result" in types
        assert "contract" in types
        assert "chain_status" in types


class TestBlockchainGetState:
    """Cover lines 478-484: get_state builds chain dict."""

    def test_get_state_includes_chain(self):
        """Lines 478-484: get_state() returns state with chain, contracts, contributors."""
        organ = BlockchainEconomy()
        patch = make_patch()

        # Mint a block so chain has content
        organ.invoke(make_inv("BLOCKCHAIN_ECONOMY", "genesis memory", "mint", 80), patch)

        state = organ.get_state()

        # Lines 479-484: state includes chain, contracts, contributors
        assert "state" in state
        assert "chain" in state["state"]
        assert "contracts" in state["state"]
        assert "contributors" in state["state"]
        assert len(state["state"]["chain"]) >= 1

    def test_get_state_with_contract(self):
        """Lines 478-484: get_state includes contracts dict."""
        organ = BlockchainEconomy()
        patch = make_patch()

        # Create a contract
        organ.invoke(
            make_inv("BLOCKCHAIN_ECONOMY", "I will deliver|Output produced|60", "contract", 70),
            patch
        )

        state = organ.get_state()
        assert len(state["state"]["contracts"]) >= 1


class TestBlockchainRestoreState:
    """Cover lines 488-490: restore_state restores contributors."""

    def test_restore_state_restores_contributors(self):
        """Lines 488-490: restore_state() restores contributors from state."""
        organ = BlockchainEconomy()
        patch = make_patch()

        # Mint to create a contributor
        organ.invoke(make_inv("BLOCKCHAIN_ECONOMY", "memory block", "mint", 80), patch)

        state = organ.get_state()
        assert len(state["state"]["contributors"]) > 0

        # Restore into a fresh organ
        organ2 = BlockchainEconomy()
        organ2.restore_state(state)

        # Lines 488-490: contributors restored
        assert organ2._contributors == state["state"]["contributors"]

    def test_restore_state_empty_contributors(self):
        """Lines 488-490: restore_state with no contributors in state."""
        organ = BlockchainEconomy()
        organ.restore_state({"state": {}})
        assert organ._contributors == {}
