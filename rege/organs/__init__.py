"""
RE:GE Organs - Symbolic processing organs of the system.

Each organ implements specific mythic functions:
- HEART_OF_CANON: Canon events and mythic truth
- MIRROR_CABINET: Emotional processing and contradiction
- MYTHIC_SENATE: Law governance and voting
- ARCHIVE_ORDER: Storage and retrieval
- RITUAL_COURT: Ceremonial logic and verdicts
- CODE_FORGE: Symbol-to-code translation
- BLOOM_ENGINE: Generative growth and mutation
- SOUL_PATCHBAY: Routing hub (handled by routing module)
- ECHO_SHELL: Decay and whispered loops
- DREAM_COUNCIL: Prophecy and dream processing
- MASK_ENGINE: Identity and persona assembly
- CHAMBER_OF_COMMERCE: Symbolic economy and mythic valuation
- BLOCKCHAIN_ECONOMY: Immutable record system for ritual tracking
- PLACE_PROTOCOLS: Spatial context engine
- TIME_RULES: Temporal recursion engine
- PROCESS_PRODUCT: Converts lived process into sharable forms
- PUBLISHING_TEMPLE: Final gate for releasing outputs
- INTERLOCUTOR: Ghost dialogue protocols and symbolic being interfaces
"""

from rege.organs.base import OrganHandler
from rege.organs.registry import OrganRegistry, get_organ_registry
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

__all__ = [
    # Base
    "OrganHandler",
    "OrganRegistry",
    "get_organ_registry",
    # Core Organs (01-11)
    "HeartOfCanon",
    "MirrorCabinet",
    "MythicSenate",
    "ArchiveOrder",
    "RitualCourt",
    "CodeForge",
    "BloomEngine",
    "EchoShell",
    "DreamCouncil",
    "MaskEngine",
    # Extended Organs (12-22)
    "ChamberOfCommerce",
    "BlockchainEconomy",
    "PlaceProtocols",
    "TimeRulesEngine",
    "ProcessProductConverter",
    "PublishingTemple",
    # Additional Organs (14, 15, 18, 20, 21)
    "ProcessMonetizer",
    "AudienceEngine",
    "AnalogDigitalEngine",
    "ConsumptionProtocol",
    "StagecraftModule",
    "InterlocutorEngine",
]
