"""
RE:GE Organ Registry - Central registry for organ handlers.
"""

from typing import Dict, Optional, List, Type
from rege.organs.base import OrganHandler
from rege.core.exceptions import OrganNotFoundError


class OrganRegistry:
    """
    Central registry mapping organ names to handler instances.

    The registry allows:
    - Registration of organ handlers
    - Lookup by name
    - Enumeration of available organs
    - Handler instance management
    """

    def __init__(self):
        """Initialize empty registry."""
        self._handlers: Dict[str, OrganHandler] = {}

    def register(self, handler: OrganHandler) -> None:
        """
        Register an organ handler.

        Args:
            handler: The organ handler instance to register
        """
        self._handlers[handler.name.upper()] = handler

    def register_class(self, handler_class: Type[OrganHandler]) -> OrganHandler:
        """
        Register an organ handler by class, instantiating it.

        Args:
            handler_class: The organ handler class

        Returns:
            The instantiated handler
        """
        handler = handler_class()
        self.register(handler)
        return handler

    def get(self, name: str) -> Optional[OrganHandler]:
        """
        Get an organ handler by name.

        Args:
            name: The organ name

        Returns:
            The handler, or None if not found
        """
        return self._handlers.get(name.upper())

    def get_or_raise(self, name: str) -> OrganHandler:
        """
        Get an organ handler by name, raising if not found.

        Args:
            name: The organ name

        Returns:
            The handler

        Raises:
            OrganNotFoundError: If organ is not registered
        """
        handler = self.get(name)
        if handler is None:
            raise OrganNotFoundError(name, list(self._handlers.keys()))
        return handler

    def has(self, name: str) -> bool:
        """
        Check if an organ is registered.

        Args:
            name: The organ name

        Returns:
            True if registered
        """
        return name.upper() in self._handlers

    def list_names(self) -> List[str]:
        """Get list of all registered organ names."""
        return list(self._handlers.keys())

    def list_handlers(self) -> List[OrganHandler]:
        """Get list of all registered handler instances."""
        return list(self._handlers.values())

    def unregister(self, name: str) -> bool:
        """
        Unregister an organ handler.

        Args:
            name: The organ name

        Returns:
            True if handler was removed, False if not found
        """
        if name.upper() in self._handlers:
            del self._handlers[name.upper()]
            return True
        return False

    def clear(self) -> None:
        """Clear all registered handlers."""
        self._handlers.clear()

    def get_all_states(self) -> Dict[str, Dict]:
        """
        Get state of all organs for checkpointing.

        Returns:
            Dictionary mapping organ names to their states
        """
        return {
            name: handler.get_state()
            for name, handler in self._handlers.items()
        }

    def restore_all_states(self, states: Dict[str, Dict]) -> None:
        """
        Restore state for all organs.

        Args:
            states: Dictionary mapping organ names to states
        """
        for name, state in states.items():
            handler = self.get(name)
            if handler:
                handler.restore_state(state)

    def __len__(self) -> int:
        return len(self._handlers)

    def __contains__(self, name: str) -> bool:
        return self.has(name)

    def __iter__(self):
        return iter(self._handlers.values())


# Global organ registry
_organ_registry: Optional[OrganRegistry] = None


def get_organ_registry() -> OrganRegistry:
    """Get or create global organ registry."""
    global _organ_registry
    if _organ_registry is None:
        _organ_registry = OrganRegistry()
    return _organ_registry


def register_default_organs() -> OrganRegistry:
    """
    Register all default organ handlers.

    Returns:
        The registry with all organs registered
    """
    # Core organs (01-11)
    from rege.organs.heart_of_canon import HeartOfCanon
    from rege.organs.mirror_cabinet import MirrorCabinet
    from rege.organs.mythic_senate import MythicSenate
    from rege.organs.archive_order import ArchiveOrder
    from rege.organs.ritual_court import RitualCourt
    from rege.organs.code_forge import CodeForge
    from rege.organs.bloom_engine import BloomEngine
    from rege.organs.echo_shell import EchoShell
    from rege.organs.dream_council import DreamCouncil
    from rege.organs.mask_engine import MaskEngine
    # Extended organs (12-22)
    from rege.organs.chamber_commerce import ChamberOfCommerce
    from rege.organs.blockchain_economy import BlockchainEconomy
    from rege.organs.place_protocols import PlaceProtocols
    from rege.organs.time_rules import TimeRulesEngine
    from rege.organs.process_product import ProcessProductConverter
    from rege.organs.publishing_temple import PublishingTemple
    from rege.organs.process_monetizer import ProcessMonetizer
    from rege.organs.audience_engine import AudienceEngine
    from rege.organs.analog_digital_engine import AnalogDigitalEngine
    from rege.organs.consumption_protocol import ConsumptionProtocol
    from rege.organs.stagecraft_module import StagecraftModule
    from rege.organs.interlocutor import InterlocutorEngine

    registry = get_organ_registry()

    # Core organs
    registry.register_class(HeartOfCanon)
    registry.register_class(MirrorCabinet)
    registry.register_class(MythicSenate)
    registry.register_class(ArchiveOrder)
    registry.register_class(RitualCourt)
    registry.register_class(CodeForge)
    registry.register_class(BloomEngine)
    registry.register_class(EchoShell)
    registry.register_class(DreamCouncil)
    registry.register_class(MaskEngine)
    # Extended organs
    registry.register_class(ChamberOfCommerce)
    registry.register_class(BlockchainEconomy)
    registry.register_class(PlaceProtocols)
    registry.register_class(TimeRulesEngine)
    registry.register_class(ProcessProductConverter)
    registry.register_class(PublishingTemple)
    # Additional organs (14, 15, 18, 20, 21)
    registry.register_class(ProcessMonetizer)
    registry.register_class(AudienceEngine)
    registry.register_class(AnalogDigitalEngine)
    registry.register_class(ConsumptionProtocol)
    registry.register_class(StagecraftModule)
    registry.register_class(InterlocutorEngine)

    return registry
