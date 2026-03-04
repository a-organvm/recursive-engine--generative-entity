"""
RE:GE Invocation Validator - Validate parsed invocations.

Based on: RE-GE_OS_INTERFACE_01_RITUAL_ACCESS_CO.md
"""

from typing import Dict, List, Tuple, Any, Optional
from rege.core.models import Invocation, DepthLevel
from rege.core.exceptions import ValidationError, InvalidModeError, OrganNotFoundError


# Organ Registry - Configuration for each organ
ORGAN_REGISTRY: Dict[str, Dict[str, Any]] = {
    # Core organs (01-11)
    "HEART_OF_CANON": {
        "valid_modes": ["mythic", "recursive", "devotional", "default"],
        "required_charge": 0,
        "output_types": ["canon_event", "pulse_check", "archive_entry"],
        "description": "The emotional core governing Canon Events and mythic truth",
    },
    "MIRROR_CABINET": {
        "valid_modes": ["emotional_reflection", "grief_mirroring", "shadow_work", "default"],
        "required_charge": 0,
        "output_types": ["fragment_map", "law_suggestion", "reflection_sentence"],
        "description": "Emotional processing engine for contradiction and integration",
    },
    "MYTHIC_SENATE": {
        "valid_modes": ["legislative", "debate", "vote", "default"],
        "required_charge": 51,
        "output_types": ["law_proposal", "vote_result", "echo_record"],
        "description": "Law governance and symbolic debate",
    },
    "ARCHIVE_ORDER": {
        "valid_modes": ["sacred_logging", "retrieval", "decay_check", "default"],
        "required_charge": 0,
        "output_types": ["canonical_thread_tag", "memory_node", "archive_entry"],
        "description": "Storage and retrieval of symbolic records",
    },
    "RITUAL_COURT": {
        "valid_modes": ["contradiction_trial", "grief_ritual", "fusion_verdict", "emergency_session", "default"],
        "required_charge": 51,
        "output_types": ["closure", "law", "verdict", "glyph_archive", "authorization_verdict"],
        "description": "Ceremonial logic and contradiction resolution",
    },
    "CODE_FORGE": {
        "valid_modes": ["func_mode", "class_mode", "wave_mode", "tree_mode", "sim_mode", "default"],
        "required_charge": 0,
        "output_types": [".py", ".maxpat", ".json", ".glyph", ".ritual_code"],
        "description": "Symbol-to-code translation engine",
    },
    "BLOOM_ENGINE": {
        "valid_modes": ["seasonal_mutation", "growth", "versioning", "seasonal_growth", "default"],
        "required_charge": 51,
        "output_types": ["mutated_fragment", "symbolic_schedule", "version_map", "versioned_fragment"],
        "description": "Generative growth and mutation scheduler",
    },
    "SOUL_PATCHBAY": {
        "valid_modes": ["route", "connect", "remap", "default"],
        "required_charge": 0,
        "output_types": ["patch_record", "route_map", "junction_node"],
        "description": "Modular routing hub connecting all organs",
    },
    "ECHO_SHELL": {
        "valid_modes": ["decay", "whisper", "pulse", "default"],
        "required_charge": 0,
        "output_types": ["echo_log", "latent_state", "whisper_record"],
        "description": "Recursion interface for decay and whispered loops",
    },
    "DREAM_COUNCIL": {
        "valid_modes": ["prophetic_lawmaking", "glyph_decode", "interpretation", "default"],
        "required_charge": 0,
        "output_types": ["law_proposal", "archive_symbol", "dream_map"],
        "description": "Collective processing and prophecy from dreams",
    },
    "MASK_ENGINE": {
        "valid_modes": ["assembly", "inheritance", "shift", "default"],
        "required_charge": 0,
        "output_types": ["persona", "mask_record", "identity_layer"],
        "description": "Identity layers and persona assembly",
    },
    # Extended organs (12-22)
    "CHAMBER_OF_COMMERCE": {
        "valid_modes": ["value", "trade", "mint", "ledger", "balance", "default"],
        "required_charge": 0,
        "output_types": ["valuation", "trade_record", "mint_record", "ledger", "balance", "economy_status"],
        "description": "Symbolic economy and mythic valuation engine",
    },
    "BLOCKCHAIN_ECONOMY": {
        "valid_modes": ["mint", "verify", "contract", "history", "contributors", "default"],
        "required_charge": 0,
        "output_types": ["block", "verification_result", "contract", "history", "contributor_stats", "chain_status"],
        "description": "Immutable record system for ritual tracking",
    },
    "PLACE_PROTOCOLS": {
        "valid_modes": ["enter", "exit", "map", "rules", "default"],
        "required_charge": 0,
        "output_types": ["place_state", "transition_record", "zone_rules", "location_map"],
        "description": "Spatial context engine for location-aware invocations",
    },
    "TIME_RULES": {
        "valid_modes": ["cycle", "schedule", "decay", "recurrence", "default"],
        "required_charge": 0,
        "output_types": ["cycle_state", "schedule_entry", "decay_result", "recurrence_record", "temporal_state"],
        "description": "Temporal recursion engine for bloom cycles and charge-based timing",
    },
    "PROCESS_PRODUCT": {
        "valid_modes": ["evaluate", "convert", "tier", "formats", "default"],
        "required_charge": 71,
        "output_types": ["readiness_report", "product", "tier_assignment", "format_list", "converter_status"],
        "description": "Converts lived process into sharable forms",
    },
    "PUBLISHING_TEMPLE": {
        "valid_modes": ["sanctify", "publish", "seal", "withdraw", "queue", "default"],
        "required_charge": 0,
        "output_types": ["sanctification", "publication", "seal_record", "withdrawal", "queue_status", "temple_status"],
        "description": "Final gate for releasing outputs",
    },
    # Additional organs (14, 15, 18, 20, 21)
    "PROCESS_MONETIZER": {
        "valid_modes": ["value", "monetize", "gate", "ledger", "default"],
        "required_charge": 0,
        "output_types": ["valuation", "product", "gate_result", "ledger", "monetizer_status"],
        "description": "Transforms creative process into sacred product and ritual currency",
    },
    "AUDIENCE_ENGINE": {
        "valid_modes": ["cultivate", "tier", "track", "filter", "default"],
        "required_charge": 0,
        "output_types": ["node", "tier_assignment", "echo_log", "filter_report", "engine_status"],
        "description": "Fan cultivation protocol and witness engagement module",
    },
    "ANALOG_DIGITAL_ENGINE": {
        "valid_modes": ["encode", "protect", "evaluate", "trail", "default"],
        "required_charge": 0,
        "output_types": ["evaluation", "encoding_result", "protection_record", "trail", "engine_status"],
        "description": "Threshold guardian between flesh and function",
    },
    "CONSUMPTION_PROTOCOL": {
        "valid_modes": ["ingest", "assess", "gate", "track", "default"],
        "required_charge": 0,
        "output_types": ["assessment", "consumption_record", "gate_result", "pattern_report", "protocol_status"],
        "description": "Governs ethical ingestion of outputs",
    },
    "STAGECRAFT_MODULE": {
        "valid_modes": ["perform", "setup", "enact", "log", "default"],
        "required_charge": 0,
        "output_types": ["performance", "stage_config", "enactment", "performance_log", "module_status"],
        "description": "Performance engine for enacting rituals in real-time",
    },
    "INTERLOCUTOR": {
        "valid_modes": ["possession", "summoning", "mirroring", "mask-shift", "multiplicity", "consent", "default"],
        "required_charge": 0,
        "output_types": ["dialogue_entry", "possession_log", "ghost_response", "mirror_echo", "multiplicity_record", "consent_record", "engine_status"],
        "description": "Ghost dialogue protocols and symbolic being interfaces — Chamber of Dialogic Echo",
    },
    # Protocol pseudo-organs
    "PROTOCOL_FUSE01": {
        "valid_modes": ["auto", "invoked", "forced", "default"],
        "required_charge": 70,
        "output_types": ["fused_fragment", "fusion_report", "rejection"],
        "description": "Fragment fusion protocol",
    },
    "PROTOCOL_FUSE01_ROLLBACK": {
        "valid_modes": ["default"],
        "required_charge": 0,
        "output_types": ["rollback_confirmation"],
        "description": "Fusion rollback protocol",
    },
    "PROTOCOL_SYSTEM_RECOVERY": {
        "valid_modes": ["full_rollback", "partial", "reconstruct", "emergency_stop", "default"],
        "required_charge": 0,
        "output_types": ["system_restored", "organs_restored", "reconstructed_data", "system_halted"],
        "description": "System recovery and rollback protocol",
    },
}

# Valid special flags
VALID_FLAGS = frozenset({
    "ECHO+", "FUSE+", "CRYPT+", "BLOOM+", "LAW_LOOP+", "LIVE+", "DREAM+",
    "EMERGENCY+", "CANON+", "ARCHIVE+", "VOLATILE+", "RITUAL+", "MIRROR+",
})

# Valid depth levels
VALID_DEPTHS = frozenset({"light", "standard", "full spiral"})


class InvocationValidator:
    """
    Validates parsed invocations against organ registry.

    Validates:
    - Organ exists in registry
    - Mode is valid for organ
    - Charge meets minimum requirements
    - Depth level is valid
    - Flags are recognized
    """

    def __init__(self, registry: Dict[str, Dict] = None):
        """
        Initialize validator with organ registry.

        Args:
            registry: Optional custom registry, defaults to ORGAN_REGISTRY
        """
        self.registry = registry or ORGAN_REGISTRY

    def validate(self, invocation: Invocation) -> Tuple[bool, List[str]]:
        """
        Validate invocation against registry.

        Args:
            invocation: Parsed invocation to validate

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []

        # Check organ exists
        organ_name = invocation.organ.upper()
        if organ_name not in self.registry:
            errors.append(f"Unknown organ: {invocation.organ}")
        else:
            organ_config = self.registry[organ_name]

            # Check mode is valid
            valid_modes = organ_config.get("valid_modes", ["default"])
            if invocation.mode.lower() not in valid_modes:
                errors.append(
                    f"Invalid mode '{invocation.mode}' for {invocation.organ}. "
                    f"Valid modes: {', '.join(valid_modes)}"
                )

            # Check charge meets minimum
            required_charge = organ_config.get("required_charge", 0)
            if invocation.charge < required_charge:
                errors.append(
                    f"Charge {invocation.charge} below minimum {required_charge} "
                    f"for {invocation.organ}"
                )

        # Check depth is valid
        if invocation.depth not in DepthLevel:
            errors.append(f"Invalid depth: {invocation.depth}")

        # Check flags are recognized
        for flag in invocation.flags:
            if flag.upper() not in VALID_FLAGS:
                errors.append(f"Unrecognized flag: {flag}")

        return (len(errors) == 0, errors)

    def validate_or_raise(self, invocation: Invocation) -> None:
        """
        Validate invocation and raise exception on failure.

        Args:
            invocation: Parsed invocation to validate

        Raises:
            OrganNotFoundError: If organ is not in registry
            InvalidModeError: If mode is not valid for organ
            ValidationError: For other validation failures
        """
        is_valid, errors = self.validate(invocation)

        if not is_valid:
            # Check for specific error types
            organ_name = invocation.organ.upper()
            if organ_name not in self.registry:
                raise OrganNotFoundError(
                    organ_name,
                    list(self.registry.keys())
                )

            # Check for mode errors
            if organ_name in self.registry:
                valid_modes = self.registry[organ_name].get("valid_modes", ["default"])
                if invocation.mode.lower() not in valid_modes:
                    raise InvalidModeError(
                        invocation.organ,
                        invocation.mode,
                        valid_modes
                    )

            # Generic validation error
            raise ValidationError(errors)

    def get_organ_config(self, organ_name: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for an organ.

        Args:
            organ_name: Name of the organ

        Returns:
            Organ configuration dict or None
        """
        return self.registry.get(organ_name.upper())

    def get_valid_modes(self, organ_name: str) -> List[str]:
        """
        Get valid modes for an organ.

        Args:
            organ_name: Name of the organ

        Returns:
            List of valid mode names
        """
        config = self.get_organ_config(organ_name)
        if config:
            return config.get("valid_modes", ["default"])
        return []

    def get_output_types(self, organ_name: str) -> List[str]:
        """
        Get possible output types for an organ.

        Args:
            organ_name: Name of the organ

        Returns:
            List of output type names
        """
        config = self.get_organ_config(organ_name)
        if config:
            return config.get("output_types", ["default_output"])
        return []

    def is_valid_output_type(self, organ_name: str, output_type: str) -> bool:
        """
        Check if output type is valid for an organ.

        Args:
            organ_name: Name of the organ
            output_type: Requested output type

        Returns:
            True if output type is valid
        """
        valid_types = self.get_output_types(organ_name)
        return output_type.lower() in [t.lower() for t in valid_types]

    def list_organs(self) -> List[str]:
        """Get list of all registered organ names."""
        return list(self.registry.keys())

    def describe_organ(self, organ_name: str) -> Optional[str]:
        """
        Get description of an organ.

        Args:
            organ_name: Name of the organ

        Returns:
            Description string or None
        """
        config = self.get_organ_config(organ_name)
        if config:
            return config.get("description", "No description available")
        return None


class InvocationLogger:
    """
    Logs all invocations for system tracking.
    """

    def __init__(self):
        self.logs: List[Dict] = []
        self._id_counter = 0

    def log(
        self,
        invocation: Invocation,
        result: Any,
        execution_time_ms: int,
        status: str
    ) -> Dict:
        """
        Log invocation with result.

        Args:
            invocation: The executed invocation
            result: Result of execution
            execution_time_ms: Execution time in milliseconds
            status: Execution status (success, failed, escalated)

        Returns:
            Log entry dictionary
        """
        from datetime import datetime

        self._id_counter += 1
        if not invocation.invocation_id:
            invocation.invocation_id = f"INV_{self._id_counter:06d}"

        log_entry = {
            **invocation.to_dict(),
            "result": str(result)[:500] if result else None,  # Truncate large results
            "execution_time_ms": execution_time_ms,
            "status": status,
            "logged_at": datetime.now().isoformat(),
        }

        self.logs.append(log_entry)
        return log_entry

    def get_recent(self, count: int = 10) -> List[Dict]:
        """Get most recent log entries."""
        return self.logs[-count:]

    def get_by_organ(self, organ_name: str) -> List[Dict]:
        """Get all log entries for a specific organ."""
        return [
            log for log in self.logs
            if log.get("organ", "").upper() == organ_name.upper()
        ]

    def get_by_status(self, status: str) -> List[Dict]:
        """Get all log entries with a specific status."""
        return [
            log for log in self.logs
            if log.get("status") == status
        ]

    def clear(self) -> None:
        """Clear all logs."""
        self.logs = []
        self._id_counter = 0

    def to_dict(self) -> List[Dict]:
        """Export all logs as list of dictionaries."""
        return self.logs.copy()
