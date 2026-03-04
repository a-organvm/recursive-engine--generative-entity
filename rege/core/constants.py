"""
RE:GE Constants - Charge thresholds, priority levels, and depth limits.

Based on: RE-GE_CONSTANTS_CHARGE_THRESHOLDS.md
"""

from enum import IntEnum
from typing import List


class ChargeTier(IntEnum):
    """
    The 5-tier charge system governing symbolic intensity.

    | Tier | Name       | Range  | Description                        |
    |------|------------|--------|------------------------------------|
    | 1    | LATENT     | 0-25   | Dormant, minimal processing        |
    | 2    | PROCESSING | 26-50  | Active but not urgent              |
    | 3    | ACTIVE     | 51-70  | Standard engagement                |
    | 4    | INTENSE    | 71-85  | Heightened symbolic weight         |
    | 5    | CRITICAL   | 86-100 | Emergency, maximum intensity       |
    """
    LATENT = 1
    PROCESSING = 2
    ACTIVE = 3
    INTENSE = 4
    CRITICAL = 5


class Priority(IntEnum):
    """
    Priority levels for queue processing, aligned with charge tiers.
    Lower value = higher priority (for heap ordering).
    """
    CRITICAL = 0    # charge >= 86 (CRITICAL tier)
    HIGH = 1        # charge >= 71 (INTENSE tier) or LAW_LOOP+
    STANDARD = 2    # charge 51-70 (ACTIVE tier)
    BACKGROUND = 3  # charge <= 50 (PROCESSING/LATENT)


class DepthLimits:
    """
    Recursion depth limits for routing operations.

    Based on: RE-GE_ORG_BODY_08_SOUL_PATCHBAY.md
    """
    STANDARD = 7     # Normal routing
    EXTENDED = 12    # LAW_LOOP+ flag present
    EMERGENCY = 21   # RITUAL_COURT override
    ABSOLUTE = 33    # System hard limit (panic stop)


# Charge tier ranges as a dictionary
CHARGE_TIERS = {
    "LATENT": (0, 25),
    "PROCESSING": (26, 50),
    "ACTIVE": (51, 70),
    "INTENSE": (71, 85),
    "CRITICAL": (86, 100),
}

# Tier boundary thresholds
TIER_BOUNDARIES = {
    "LATENT_MAX": 25,
    "PROCESSING_MAX": 50,
    "ACTIVE_MAX": 70,
    "INTENSE_MAX": 85,
    "CRITICAL_MIN": 86,
    "CANONIZATION_THRESHOLD": 71,  # INTENSE tier minimum
    "FUSION_THRESHOLD": 70,        # ACTIVE/INTENSE boundary
    "FUSION_AUTO_TRIGGER": 90,     # Auto-trigger fusion
    "EMERGENCY_THRESHOLD": 86,     # CRITICAL tier
}

# Valid system tags
VALID_TAGS = frozenset({
    # Special flags
    "ECHO+", "FUSE+", "CRYPT+", "BLOOM+", "LAW_LOOP+", "LIVE+", "DREAM+",
    "EMERGENCY+", "CANON+", "ARCHIVE+", "VOLATILE+", "RITUAL+", "MIRROR+",
    "REMIX+", "MASK+", "BROKEN_LOOP+", "INCOMPLETE+", "JUNCTION+",
    "RECOVERED+", "RECONSTRUCTED+",
    # Content tags
    "SHDW+", "RIT+", "ARCH+", "CHAR+", "GEN+", "MIR+", "MOD+", "MAP+",
    "PATCH+", "MUTATE+", "CYCLE+", "SPRING+", "WILT+", "GRIEF+", "FEAR+",
    "SHAME+", "DOUBT+", "PROTOCOL+", "TRANSFORM+", "SYNTHESIS+",
    "SYSTEM+", "FOUNDATIONAL+", "CONSTANT+", "THRESHOLD+", "TIER+",
    "RECOVERY+", "ROLLBACK+", "CHECKPOINT+", "RESTORATION+",
    # Interlocutor tags (AAW_CORE_09)
    "DIALOGUE+", "GHOST+", "POSSESSION+", "SUMMON+", "SPEAKING_SYSTEM+",
    "AAW+", "CONSENT+", "INTERLOCUTOR+",
})


def get_tier(charge: int) -> str:
    """
    Return tier name for a given charge value.

    Args:
        charge: Emotional charge value (0-100)

    Returns:
        Tier name (LATENT, PROCESSING, ACTIVE, INTENSE, CRITICAL)
    """
    for tier_name, (low, high) in CHARGE_TIERS.items():
        if low <= charge <= high:
            return tier_name
    return "UNKNOWN"


def get_tier_enum(charge: int) -> ChargeTier:
    """
    Return ChargeTier enum for a given charge value.

    Args:
        charge: Emotional charge value (0-100)

    Returns:
        ChargeTier enum value
    """
    if charge <= 25:
        return ChargeTier.LATENT
    elif charge <= 50:
        return ChargeTier.PROCESSING
    elif charge <= 70:
        return ChargeTier.ACTIVE
    elif charge <= 85:
        return ChargeTier.INTENSE
    else:
        return ChargeTier.CRITICAL


def get_tier_level(charge: int) -> int:
    """
    Return tier level (1-5) for priority calculations.

    Args:
        charge: Emotional charge value (0-100)

    Returns:
        Integer tier level (1=LATENT through 5=CRITICAL)
    """
    if charge <= 25:
        return 1
    elif charge <= 50:
        return 2
    elif charge <= 70:
        return 3
    elif charge <= 85:
        return 4
    else:
        return 5


def get_priority(charge: int, tags: List[str]) -> Priority:
    """
    Calculate queue priority from charge and tags.

    Args:
        charge: Emotional charge value (0-100)
        tags: List of symbolic tags

    Returns:
        Priority enum value
    """
    if charge >= 86 or "EMERGENCY+" in tags:
        return Priority.CRITICAL
    elif charge >= 71 or "LAW_LOOP+" in tags:
        return Priority.HIGH
    elif charge >= 51:
        return Priority.STANDARD
    else:
        return Priority.BACKGROUND


def is_canonization_eligible(charge: int) -> bool:
    """
    Check if charge meets canonization threshold (INTENSE+).

    Canonization requires charge >= 71 (INTENSE tier or higher).
    """
    return charge >= TIER_BOUNDARIES["CANONIZATION_THRESHOLD"]


def is_fusion_eligible(charge: int, overlap_count: int) -> bool:
    """
    Check if fragment meets FUSE01 auto-trigger conditions.

    Fusion requires:
    - charge >= 70 (at ACTIVE/INTENSE boundary or higher)
    - overlap_count >= 2 (shares content with 2+ fragments)
    """
    return charge >= TIER_BOUNDARIES["FUSION_THRESHOLD"] and overlap_count >= 2


def is_critical_emergency(charge: int) -> bool:
    """
    Check if charge requires emergency handling.

    Emergency handling at CRITICAL tier (charge >= 86).
    """
    return charge >= TIER_BOUNDARIES["EMERGENCY_THRESHOLD"]


def is_auto_fusion_trigger(charge: int) -> bool:
    """
    Check if charge triggers automatic fusion.

    Auto-fusion at charge >= 90 (deep CRITICAL tier).
    """
    return charge >= TIER_BOUNDARIES["FUSION_AUTO_TRIGGER"]


def get_depth_limit(tags: List[str]) -> int:
    """
    Determine depth limit based on tags.

    Args:
        tags: List of symbolic tags

    Returns:
        Maximum recursion depth allowed
    """
    if "EMERGENCY+" in tags:
        return DepthLimits.EMERGENCY
    elif "LAW_LOOP+" in tags:
        return DepthLimits.EXTENDED
    return DepthLimits.STANDARD


def validate_charge(charge: int) -> bool:
    """Validate charge is within acceptable range (0-100)."""
    return 0 <= charge <= 100


def validate_tag(tag: str) -> bool:
    """Validate tag is in the set of recognized tags."""
    return tag in VALID_TAGS
