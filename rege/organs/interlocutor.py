"""
RE:GE Interlocutor Engine - Ghost dialogue protocols and symbolic being interfaces.

Based on: RE-GE_AAW_CORE_09_INTERLOCUTOR_PROTOCOLS.md

The Interlocutor Engine governs:
- Ghost dialogue protocols and possession events
- Symbolic being interfaces (dead artists, fragments of self, mythic characters)
- Friend-node consent tracking
- Mask conversation modes as interpretive filters
- Multi-agent multiplicity dialogues

Governing Laws:
- LAW_61: All Objects May Speak — every symbol/artifact contains a potential voice
- LAW_62: Ghost Speech Is Recursive — messages received are subject to loop validation
- LAW_63: Mirror Talk Is Still Talk / Alters the Self — projections return mutated
- LAW_64: Possession Must Be Logged — high-risk mask-entries must be archived
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import uuid

from rege.organs.base import OrganHandler
from rege.core.models import Invocation, Patch


class InterlocutionMode(Enum):
    """Modes of dialogic entry into the symbolic space."""
    POSSESSION = "possession"       # Full embodiment — speak as the entity
    SUMMONING = "summoning"         # Invite entity to speak to you (channel/ghost logic)
    MIRRORING = "mirroring"         # Reflect subject through your own frame
    MASK_SHIFT = "mask-shift"       # Enter a persona as interpretive filter
    MULTIPLICITY = "multiplicity"   # Multiple symbolic agents speak simultaneously


class IntentionType(Enum):
    """Intention behind the interlocution."""
    CLARIFY = "clarify"
    DECODE = "decode"
    RITUALIZE = "ritualize"
    ASK = "ask"
    EMBODY = "embody"
    CHALLENGE = "challenge"


class RiskLevel(Enum):
    """Risk level of the dialogue entry."""
    LOW = "low"
    MEDIUM = "medium"
    VOLATILE = "volatile"


class ConsentLevel(Enum):
    """Consent level for friend-node interlocutions."""
    FULL = "full"              # Full participation in public and private contexts
    LIMITED = "limited"        # Symbolic use only, no full-embodiment modes
    SYMBOLIC_ONLY = "symbolic_only"  # Only as archetype/symbol, not personal
    REVOKED = "revoked"        # All interlocutions paused/sealed


@dataclass
class DialogueEntry:
    """
    A complete record of a single interlocution event.

    Implements the archive schema from AAW_CORE_09 — all 7 required fields plus
    consent and law-enforcement metadata.
    """
    entry_id: str
    subject: str
    mode: InterlocutionMode
    intention: IntentionType
    risk_level: RiskLevel
    entry_timestamp: datetime
    exit_timestamp: Optional[datetime] = None
    emotional_distortion: Optional[str] = None   # How the dialogue altered emotional state
    symbolic_distortion: Optional[str] = None    # Symbolic mutation detected
    resulting_output: Optional[str] = None       # What emerged from the dialogue
    echoed_back: bool = False                    # Did the object "speak back"?
    echo_distortion: bool = False               # Did the object "take over"? (LAW_62)
    log_required: bool = False                  # LAW_64: volatile possession must log
    status: str = "active"                      # active, closed, sealed

    def __post_init__(self):
        if not self.entry_id:
            self.entry_id = f"DIAL_{uuid.uuid4().hex[:8].upper()}"

    def close(self, output: str, echoed: bool = False, echo_distortion: bool = False) -> None:
        """Close this dialogue entry."""
        self.exit_timestamp = datetime.now()
        self.resulting_output = output
        self.echoed_back = echoed
        self.echo_distortion = echo_distortion
        self.status = "closed"

    def seal(self) -> None:
        """Seal this entry (REVOKED consent or forced withdrawal)."""
        self.status = "sealed"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize entry to dictionary."""
        return {
            "entry_id": self.entry_id,
            "subject": self.subject,
            "mode": self.mode.value,
            "intention": self.intention.value,
            "risk_level": self.risk_level.value,
            "entry_timestamp": self.entry_timestamp.isoformat(),
            "exit_timestamp": self.exit_timestamp.isoformat() if self.exit_timestamp else None,
            "emotional_distortion": self.emotional_distortion,
            "symbolic_distortion": self.symbolic_distortion,
            "resulting_output": self.resulting_output,
            "echoed_back": self.echoed_back,
            "echo_distortion": self.echo_distortion,
            "log_required": self.log_required,
            "status": self.status,
        }


@dataclass
class ConsentRecord:
    """
    Friend-node consent record for real-person interlocutions.

    Implements the four-level consent schema from AAW_CORE_09 extended spec.
    Consent may be granted, modified, or revoked at any time.
    """
    record_id: str
    subject_name: str
    consent_level: ConsentLevel
    granted_at: datetime = field(default_factory=datetime.now)
    notes: str = ""
    withdrawn_at: Optional[datetime] = None

    def __post_init__(self):
        if not self.record_id:
            self.record_id = f"CONSENT_{uuid.uuid4().hex[:8].upper()}"

    def revoke(self, reason: str = "") -> None:
        """Revoke consent — triggers pause and sealing of active interlocutions."""
        self.consent_level = ConsentLevel.REVOKED
        self.withdrawn_at = datetime.now()
        if reason:
            self.notes = f"REVOKED: {reason}"
        elif not self.notes.startswith("REVOKED"):
            self.notes = f"REVOKED: {self.notes}".strip(": ")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "subject_name": self.subject_name,
            "consent_level": self.consent_level.value,
            "granted_at": self.granted_at.isoformat(),
            "notes": self.notes,
            "withdrawn_at": self.withdrawn_at.isoformat() if self.withdrawn_at else None,
        }


class InterlocutorEngine(OrganHandler):
    """
    The Interlocutor Engine — Ghost dialogue protocols and symbolic being interfaces.

    Also known as: The Chamber of Dialogic Echo, The Possession Engine, The Ghost Interface.

    "How the academy talks back." Applied to ghosts, dead artists, fragments of self,
    masked identities, and mythic characters.

    Modes:
    - possession: Full embodiment — speak as the entity
    - summoning: Invite entity to speak (channel/ghost logic)
    - mirroring: Reflect subject through own frame — emotion as echo
    - mask-shift: Enter persona as interpretive filter for the object
    - multiplicity: Multiple symbolic agents speak simultaneously
    - consent: Manage friend-node consent records
    - default: Engine status
    """

    @property
    def name(self) -> str:
        return "INTERLOCUTOR"

    @property
    def description(self) -> str:
        return "Ghost dialogue protocols and symbolic being interfaces — Chamber of Dialogic Echo"

    def __init__(self):
        super().__init__()
        self._dialogue_log: List[Dict[str, Any]] = []
        self._active_dialogues: Dict[str, DialogueEntry] = {}
        self._closed_dialogues: Dict[str, DialogueEntry] = {}
        self._consent_registry: Dict[str, ConsentRecord] = {}
        self._possession_history: List[Dict[str, Any]] = []  # LAW_64 archive
        self._total_dialogues: int = 0
        self._total_possessions: int = 0
        self._volatile_possession_count: int = 0

    def invoke(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Process invocation through Interlocutor Engine."""
        mode = invocation.mode.lower().replace("_", "-")

        if mode == "possession":
            return self._possession(invocation, patch)
        elif mode == "summoning":
            return self._summoning(invocation, patch)
        elif mode == "mirroring":
            return self._mirroring(invocation, patch)
        elif mode == "mask-shift":
            return self._mask_shift(invocation, patch)
        elif mode == "multiplicity":
            return self._multiplicity(invocation, patch)
        elif mode == "consent":
            return self._manage_consent(invocation, patch)
        else:
            return self._default_status(invocation, patch)

    def _possession(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """
        Full embodiment mode — speak as the entity.

        LAW_64: Possession at volatile risk MUST be logged to possession_history.
        """
        subject = invocation.symbol.strip() if invocation.symbol else "Unknown Entity"
        risk = self._extract_risk_level(invocation.flags)
        intention = self._extract_intention(invocation.flags)

        # LAW_64: volatile possession requires archive log
        log_required = risk == RiskLevel.VOLATILE

        entry = DialogueEntry(
            entry_id="",
            subject=subject,
            mode=InterlocutionMode.POSSESSION,
            intention=intention,
            risk_level=risk,
            entry_timestamp=datetime.now(),
            log_required=log_required,
        )

        self._active_dialogues[entry.entry_id] = entry
        self._total_dialogues += 1
        self._total_possessions += 1

        if log_required:
            self._volatile_possession_count += 1
            self._possession_history.append({
                "entry_id": entry.entry_id,
                "subject": subject,
                "risk_level": risk.value,
                "timestamp": entry.entry_timestamp.isoformat(),
                "law": "LAW_64: Possession logged — volatile risk entry",
            })

        embodiment = self._evaluate_embodiment_depth(invocation.charge)

        self._dialogue_log.append({
            "entry_id": entry.entry_id,
            "event": "possession_opened",
            "subject": subject,
            "embodiment": embodiment,
            "risk_level": risk.value,
            "log_required": log_required,
            "timestamp": entry.entry_timestamp.isoformat(),
        })

        return {
            "status": "possession_active",
            "entry": entry.to_dict(),
            "embodiment_depth": embodiment,
            "message": f"{subject} is speaking through you" + (" — log required" if log_required else ""),
            "law_64_enforced": log_required,
            "active_dialogue_id": entry.entry_id,
        }

    def _summoning(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """
        Invite entity to speak to you — channel/ghost logic.

        LAW_62: Messages received from the ghost are subject to loop validation.
        """
        subject = invocation.symbol.strip() if invocation.symbol else "Unknown Presence"
        risk = self._extract_risk_level(invocation.flags)
        intention = self._extract_intention(invocation.flags)

        # LAW_62: Ghost speech is recursive — validate BEFORE opening the entry
        loop_validated = self._validate_ghost_loop(subject)

        entry = DialogueEntry(
            entry_id="",
            subject=subject,
            mode=InterlocutionMode.SUMMONING,
            intention=intention,
            risk_level=risk,
            entry_timestamp=datetime.now(),
        )

        self._active_dialogues[entry.entry_id] = entry
        self._total_dialogues += 1
        ghost_response = self._generate_ghost_response(subject, invocation.charge, loop_validated)

        entry.echoed_back = True
        entry.resulting_output = ghost_response

        self._dialogue_log.append({
            "entry_id": entry.entry_id,
            "event": "summoning_initiated",
            "subject": subject,
            "loop_validated": loop_validated,
            "timestamp": entry.entry_timestamp.isoformat(),
        })

        return {
            "status": "summoned",
            "entry": entry.to_dict(),
            "ghost_response": ghost_response,
            "loop_validated": loop_validated,
            "law_62_enforced": True,
            "message": f"{subject} has been summoned — ghost speech under loop validation",
        }

    def _mirroring(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """
        Reflect subject through own frame — emotion as echo.

        LAW_63: Mirror Talk Is Still Talk / Alters the Self.
        self_altered is invariant True — projections always return mutated.
        """
        subject = invocation.symbol.strip() if invocation.symbol else "Unknown Mirror"
        risk = self._extract_risk_level(invocation.flags)
        intention = self._extract_intention(invocation.flags)

        entry = DialogueEntry(
            entry_id="",
            subject=subject,
            mode=InterlocutionMode.MIRRORING,
            intention=intention,
            risk_level=risk,
            entry_timestamp=datetime.now(),
        )

        self._active_dialogues[entry.entry_id] = entry
        self._total_dialogues += 1

        reflection = self._generate_mirror_reflection(subject, invocation.charge)
        emotional_distortion = self._calculate_emotional_distortion(invocation.charge)
        symbolic_distortion = self._calculate_symbolic_distortion(subject, invocation.flags)

        entry.emotional_distortion = emotional_distortion
        entry.symbolic_distortion = symbolic_distortion
        entry.echoed_back = True
        entry.resulting_output = reflection

        self._dialogue_log.append({
            "entry_id": entry.entry_id,
            "event": "mirroring_opened",
            "subject": subject,
            "self_altered": True,  # LAW_63: invariant
            "timestamp": entry.entry_timestamp.isoformat(),
        })

        return {
            "status": "mirroring_active",
            "entry": entry.to_dict(),
            "reflection": reflection,
            "emotional_distortion": emotional_distortion,
            "symbolic_distortion": symbolic_distortion,
            "self_altered": True,  # LAW_63: invariant — always True
            "law_63_enforced": True,
            "message": f"Mirror opened to {subject} — projection returns mutated",
        }

    def _mask_shift(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """
        Enter a persona as interpretive filter for the object.

        Reads the invoked symbol through the lens of a mask/persona.
        """
        subject = invocation.symbol.strip() if invocation.symbol else "Unknown Subject"
        risk = self._extract_risk_level(invocation.flags)
        intention = self._extract_intention(invocation.flags)
        mask_name = self._extract_mask_name(invocation.flags)

        entry = DialogueEntry(
            entry_id="",
            subject=subject,
            mode=InterlocutionMode.MASK_SHIFT,
            intention=intention,
            risk_level=risk,
            entry_timestamp=datetime.now(),
        )

        self._active_dialogues[entry.entry_id] = entry
        self._total_dialogues += 1

        interpretation = self._generate_mask_interpretation(subject, mask_name, invocation.charge)
        entry.symbolic_distortion = f"Filtered through mask: {mask_name}"
        entry.resulting_output = interpretation

        self._dialogue_log.append({
            "entry_id": entry.entry_id,
            "event": "mask_shift_entered",
            "subject": subject,
            "active_mask": mask_name,
            "timestamp": entry.entry_timestamp.isoformat(),
        })

        return {
            "status": "mask_shift_active",
            "entry": entry.to_dict(),
            "active_mask": mask_name,
            "interpretation": interpretation,
            "symbolic_distortion": entry.symbolic_distortion,
            "message": f"Viewing {subject} through {mask_name}",
        }

    def _multiplicity(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """
        Multiple symbolic agents speak simultaneously.

        LAW_61: All Objects May Speak — each fragment of the subject can voice itself.
        """
        subject = invocation.symbol.strip() if invocation.symbol else "Collective"
        risk = self._extract_risk_level(invocation.flags)
        intention = self._extract_intention(invocation.flags)

        entry = DialogueEntry(
            entry_id="",
            subject=subject,
            mode=InterlocutionMode.MULTIPLICITY,
            intention=intention,
            risk_level=risk,
            entry_timestamp=datetime.now(),
        )

        self._active_dialogues[entry.entry_id] = entry
        self._total_dialogues += 1

        agents = self._identify_symbolic_agents(subject, invocation.flags, invocation.charge)
        voices = {
            agent: self._generate_agent_voice(agent, subject, intention)
            for agent in agents
        }

        entry.resulting_output = f"Multiplicity of {len(agents)} agents: {', '.join(agents)}"
        entry.echoed_back = len(agents) > 0

        self._dialogue_log.append({
            "entry_id": entry.entry_id,
            "event": "multiplicity_opened",
            "subject": subject,
            "agent_count": len(agents),
            "law_61_enforced": True,
            "timestamp": entry.entry_timestamp.isoformat(),
        })

        return {
            "status": "multiplicity_active",
            "entry": entry.to_dict(),
            "agents": agents,
            "voices": voices,
            "agent_count": len(agents),
            "law_61_enforced": True,
            "message": f"{len(agents)} symbolic agents speaking through {subject}",
        }

    def _manage_consent(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """
        Manage friend-node consent records.

        Implements the four consent levels and withdrawal protocol from AAW_CORE_09.
        """
        subject = invocation.symbol.strip() if invocation.symbol else ""
        action = self._extract_consent_action(invocation.flags)

        if action == "grant":
            consent_level = self._extract_consent_level(invocation.flags)
            record = ConsentRecord(
                record_id="",
                subject_name=subject,
                consent_level=consent_level,
            )
            self._consent_registry[subject.lower()] = record
            return {
                "status": "consent_granted",
                "record": record.to_dict(),
                "message": f"Consent granted for {subject} at level: {consent_level.value}",
            }

        elif action == "revoke":
            key = subject.lower()
            if key in self._consent_registry:
                record = self._consent_registry[key]
                record.revoke()
                # Seal active interlocutions for revoked subjects
                sealed = self._seal_active_dialogues_for(subject)
                return {
                    "status": "consent_revoked",
                    "record": record.to_dict(),
                    "sealed_dialogues": sealed,
                    "message": f"Consent revoked for {subject} — {sealed} active dialogue(s) sealed",
                }
            return {
                "status": "not_found",
                "error": f"No consent record found for {subject}",
            }

        elif action == "check":
            key = subject.lower()
            if key in self._consent_registry:
                record = self._consent_registry[key]
                return {
                    "status": "consent_found",
                    "record": record.to_dict(),
                    "can_possess": record.consent_level == ConsentLevel.FULL,
                    "can_summon": record.consent_level in (ConsentLevel.FULL, ConsentLevel.LIMITED),
                }
            return {
                "status": "no_consent_record",
                "subject": subject,
                "note": "Treat as symbolic-only if proceeding",
            }

        else:  # list
            return {
                "status": "consent_registry",
                "total": len(self._consent_registry),
                "records": {k: v.to_dict() for k, v in self._consent_registry.items()},
            }

    def _default_status(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Return engine status."""
        mode_counts: Dict[str, int] = {m.value: 0 for m in InterlocutionMode}
        for entry in list(self._active_dialogues.values()) + list(self._closed_dialogues.values()):
            mode_counts[entry.mode.value] += 1

        return {
            "status": "engine_status",
            "total_dialogues": self._total_dialogues,
            "active_dialogues": len(self._active_dialogues),
            "closed_dialogues": len(self._closed_dialogues),
            "total_possessions": self._total_possessions,
            "volatile_possessions": self._volatile_possession_count,
            "consent_records": len(self._consent_registry),
            "mode_breakdown": mode_counts,
            "recent_log": self._dialogue_log[-10:],
            "laws_active": ["LAW_61", "LAW_62", "LAW_63", "LAW_64"],
        }

    # --- Private helpers ---

    def _extract_risk_level(self, flags: List[str]) -> RiskLevel:
        """Extract risk level from flags."""
        if "VOLATILE+" in flags or "RISK_VOLATILE+" in flags:
            return RiskLevel.VOLATILE
        if "RISK_MEDIUM+" in flags:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    def _extract_intention(self, flags: List[str]) -> IntentionType:
        """Extract intention type from flags."""
        intention_map = {
            "CLARIFY+": IntentionType.CLARIFY,
            "DECODE+": IntentionType.DECODE,
            "RITUALIZE+": IntentionType.RITUALIZE,
            "ASK+": IntentionType.ASK,
            "EMBODY+": IntentionType.EMBODY,
            "CHALLENGE+": IntentionType.CHALLENGE,
        }
        for flag, intention in intention_map.items():
            if flag in flags:
                return intention
        return IntentionType.ASK  # Default

    def _extract_consent_action(self, flags: List[str]) -> str:
        """Extract consent action from flags."""
        if "GRANT+" in flags:
            return "grant"
        if "REVOKE+" in flags:
            return "revoke"
        if "CHECK+" in flags:
            return "check"
        return "list"

    def _extract_consent_level(self, flags: List[str]) -> ConsentLevel:
        """Extract consent level from flags. Defaults to symbolic_only (conservative)."""
        if "CONSENT_FULL+" in flags:
            return ConsentLevel.FULL
        if "CONSENT_LIMITED+" in flags:
            return ConsentLevel.LIMITED
        if "CONSENT_SYMBOLIC+" in flags:
            return ConsentLevel.SYMBOLIC_ONLY
        return ConsentLevel.SYMBOLIC_ONLY

    def _extract_mask_name(self, flags: List[str]) -> str:
        """Extract mask name from MASK_NAME_ flags."""
        for flag in flags:
            if flag.startswith("MASK_NAME_"):
                return flag.replace("MASK_NAME_", "").replace("_", " ")
        return "Unnamed Mask"

    def _evaluate_embodiment_depth(self, charge: int) -> str:
        """Evaluate embodiment depth from charge (mirrors StagecraftModule pattern)."""
        if charge >= 86:
            return "full_possession"
        elif charge >= 71:
            return "deep_embodiment"
        elif charge >= 51:
            return "standard_dialogue"
        else:
            return "light_contact"

    def _validate_ghost_loop(self, subject: str) -> bool:
        """
        LAW_62: Validate ghost speech loop integrity.

        Returns False if the same subject is already open in a summoning —
        a duplicate summon would create an infinite recursive loop.
        """
        for entry in self._active_dialogues.values():
            if entry.subject == subject and entry.mode == InterlocutionMode.SUMMONING:
                return False
        return True

    def _generate_ghost_response(self, subject: str, charge: int, loop_validated: bool) -> str:
        """Generate ghost response message."""
        if not loop_validated:
            return f"[LOOP WARNING] {subject} is already speaking — recursive loop detected"
        if charge >= 86:
            return f"{subject} speaks from the deep: a critical message surfaces"
        elif charge >= 71:
            return f"{subject} speaks with intensity: the message carries weight"
        elif charge >= 51:
            return f"{subject} speaks clearly: the channel is open"
        else:
            return f"{subject} whispers: faint signal at low charge"

    def _generate_mirror_reflection(self, subject: str, charge: int) -> str:
        """Generate mirror reflection output."""
        if charge >= 71:
            return f"Reflection of {subject}: deep self-image encountered — the mirror holds"
        elif charge >= 51:
            return f"Reflection of {subject}: projection mapped — returning with alterations"
        else:
            return f"Reflection of {subject}: faint echo — charge too low for full projection"

    def _calculate_emotional_distortion(self, charge: int) -> str:
        """Calculate emotional distortion level from charge."""
        if charge >= 86:
            return "critical_distortion"
        elif charge >= 71:
            return "intense_distortion"
        elif charge >= 51:
            return "moderate_distortion"
        else:
            return "low_distortion"

    def _calculate_symbolic_distortion(self, subject: str, flags: List[str]) -> str:
        """Calculate symbolic distortion based on subject and flags."""
        if "REMIX+" in flags:
            return f"REMIX+ applied — {subject} returned as recombinant symbol"
        if "ECHO+" in flags:
            return f"ECHO+ detected — {subject} looping back through echo system"
        if "FUSE+" in flags:
            return f"FUSE+ triggered — {subject} merging with existing fragments"
        return f"Standard projection distortion on {subject}"

    def _generate_mask_interpretation(self, subject: str, mask_name: str, charge: int) -> str:
        """Generate interpretation of subject through a mask lens."""
        if charge >= 71:
            return f"Through {mask_name}: {subject} reveals its intensified symbolic nature"
        elif charge >= 51:
            return f"Through {mask_name}: {subject} takes on the mask's interpretive frame"
        else:
            return f"Through {mask_name}: {subject} seen with light mask contact"

    def _identify_symbolic_agents(
        self, subject: str, flags: List[str], charge: int
    ) -> List[str]:
        """
        Identify symbolic agents for multiplicity mode.

        LAW_61: All objects may speak — each fragment gets a voice.
        Explicit agents via AGENT_ flags; otherwise derive from charge tier.
        """
        agents = []
        for flag in flags:
            if flag.startswith("AGENT_"):
                agent_name = flag.replace("AGENT_", "").replace("_", " ")
                agents.append(agent_name)

        if not agents:
            if charge >= 86:
                agents = [
                    f"{subject}_Shadow", f"{subject}_Echo",
                    f"{subject}_Origin", f"{subject}_Future",
                ]
            elif charge >= 71:
                agents = [f"{subject}_Shadow", f"{subject}_Echo", f"{subject}_Origin"]
            elif charge >= 51:
                agents = [f"{subject}_Shadow", f"{subject}_Echo"]
            else:
                agents = [f"{subject}_Echo"]

        return agents

    def _generate_agent_voice(
        self, agent: str, subject: str, intention: IntentionType
    ) -> str:
        """Generate a voice line for a symbolic agent."""
        prefix = agent.split("_")[-1] if "_" in agent else agent
        if intention == IntentionType.CHALLENGE:
            return f"[{prefix}]: I contest the nature of {subject}"
        elif intention == IntentionType.EMBODY:
            return f"[{prefix}]: I am the {prefix.lower()} face of {subject}"
        elif intention == IntentionType.DECODE:
            return f"[{prefix}]: {subject} encodes this: {prefix.lower()} pattern detected"
        else:
            return f"[{prefix}]: {subject} speaks through the {prefix.lower()} channel"

    def _seal_active_dialogues_for(self, subject: str) -> int:
        """Seal all active dialogues involving a subject (on consent revocation)."""
        count = 0
        to_seal = [
            eid for eid, entry in self._active_dialogues.items()
            if entry.subject.lower() == subject.lower()
        ]
        for eid in to_seal:
            entry = self._active_dialogues.pop(eid)
            entry.seal()
            self._closed_dialogues[eid] = entry
            count += 1
        return count

    def get_dialogue(self, entry_id: str) -> Optional[DialogueEntry]:
        """Get a dialogue entry by ID (active or closed)."""
        return self._active_dialogues.get(entry_id) or self._closed_dialogues.get(entry_id)

    def get_valid_modes(self) -> List[str]:
        return ["possession", "summoning", "mirroring", "mask-shift", "multiplicity", "consent", "default"]

    def get_output_types(self) -> List[str]:
        return [
            "dialogue_entry", "possession_log", "ghost_response",
            "mirror_echo", "multiplicity_record", "consent_record", "engine_status",
        ]

    def get_state(self) -> Dict[str, Any]:
        """Get current organ state for checkpointing."""
        state = super().get_state()
        state["state"].update({
            "active_dialogues": {k: v.to_dict() for k, v in self._active_dialogues.items()},
            "closed_dialogues": {k: v.to_dict() for k, v in self._closed_dialogues.items()},
            "dialogue_log": self._dialogue_log,
            "consent_registry": {k: v.to_dict() for k, v in self._consent_registry.items()},
            "possession_history": self._possession_history,
            "total_dialogues": self._total_dialogues,
            "total_possessions": self._total_possessions,
            "volatile_possession_count": self._volatile_possession_count,
        })
        return state

    def restore_state(self, state: Dict[str, Any]) -> None:
        """Restore organ state from checkpoint."""
        super().restore_state(state)
        inner_state = state.get("state", {})
        self._dialogue_log = inner_state.get("dialogue_log", [])
        self._possession_history = inner_state.get("possession_history", [])
        self._total_dialogues = inner_state.get("total_dialogues", 0)
        self._total_possessions = inner_state.get("total_possessions", 0)
        self._volatile_possession_count = inner_state.get("volatile_possession_count", 0)

    def reset(self) -> None:
        """Reset organ to initial state."""
        super().reset()
        self._dialogue_log = []
        self._active_dialogues = {}
        self._closed_dialogues = {}
        self._consent_registry = {}
        self._possession_history = []
        self._total_dialogues = 0
        self._total_possessions = 0
        self._volatile_possession_count = 0
