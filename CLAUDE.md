# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**RE:GE** (Recursive Engine: Generative Entity) is a symbolic operating system for myth, identity, ritual, and recursive systems. It consists of:

1. **Specification Documentation** (`docs/`) - Mythic-academic framework expressed through interconnected Markdown
2. **Python Implementation** (`rege/`) - Fully functional executable system

## Repository Structure

```
recursive-engine--generative-entity/
├── rege/                    # Python implementation
│   ├── core/                # Constants, models, exceptions
│   ├── parser/              # Invocation syntax parser
│   ├── routing/             # Soul Patchbay queue system
│   ├── organs/              # 10 organ handlers
│   ├── protocols/           # FUSE01, recovery, enforcement
│   ├── persistence/         # JSON archive system
│   └── tests/               # Test suite
├── docs/                    # Specification documentation
│   ├── core/                # Core system docs (4NTHOLOGY, constants, linkmap)
│   ├── organs/              # Organ specifications (01-22)
│   ├── protocols/           # Protocol specifications (FUSE01, recovery)
│   ├── interfaces/          # OS interface docs (ritual access, bridges)
│   ├── academic-wing/       # Academic expansion chambers (08-12)
│   └── archive/             # Historical/symbolic fragments
├── README.md                # Project overview and usage
├── CLAUDE.md                # This file
├── CONTRIBUTING.md          # Contribution guidelines
├── LICENSE                  # MIT License
└── pyproject.toml           # Package configuration
```

## Documentation Architecture

### Core System Files (`docs/core/`)
- `RE-GE_4NTHOLOGY_INIT.v1.0.md` - Main comprehensive system documentation
- `RE-GE_RECURSIVE_SYSTEM_RENDER_LINKMAP.md` - Inter-organ routing and connections
- `RE-GE_CONSTANTS_CHARGE_THRESHOLDS.md` - 5-tier charge system

### Organizational Bodies (`docs/organs/`)
22 thematically-named modules functioning like organs of a symbolic body:
- **01 Heart of Canon** - Core mythology and canon events
- **02 Mirror Cabinet** - Reflection and interpretation
- **03 Mythic Senate** - Law governance
- **04 Archive Order** - Storage and retrieval
- **05 Ritual Court** - Ceremonial logic and contradiction resolution
- **06 Code Forge** - Symbol-to-code translation (Python, Max/MSP, JSON)
- **07 Bloom Engine** - Generative growth and mutation
- **08 Soul Patchbay** - Modular routing hub (all modules connect through here)
- **09 Echo Shell** - Recursion interface, whispered loops
- **10 Dream Council** - Collective processing and prophecy
- **11 Mask Engine** - Identity layers and persona assembly
- **12-22** - Commerce, Blockchain, Monetizer, Audience, Place, Time, Analog-Digital, Process-Product, Consumption, Stagecraft, Publishing

### Academic Wing (`docs/academic-wing/`)
- `RE-GE_ORG_BODY_00_ACADEMIA_WING_PROTOCOL.md` - Foundational academic layer
- `RE-GE_AAW_CORE_08_CANONIZATION_ENGINE.md` - How objects enter personal canon
- `RE-GE_AAW_CORE_09_INTERLOCUTOR_PROTOCOLS.md` - Dialogue with ghosts, masks, symbolic beings
- `RE-GE_AAW_CORE_10_GENEALOGY_ENGINE.md` - Symbolic lineage and influence mapping
- `RE-GE_AAW_CORE_11_FAILURE_STUDY_CHAMBER.md` - Ritual study of collapse and abandonment
- `RE-GE_AAW_CORE_12_MYTHICAL_CITATION_SYSTEM.md` - Recursive attribution and echo tracking

### Protocols (`docs/protocols/`)
- `RE-GE_PROTOCOL_FUSE01.md` - Fragment fusion protocol
- `RE-GE_PROTOCOL_SYSTEM_RECOVERY.md` - System recovery protocol
- `RE-GE_PROTOCOL_COLLABORATOR.md` - Collaboration protocol

### Interfaces (`docs/interfaces/`)
- `RE-GE_OS_INTERFACE_01_RITUAL_ACCESS_CONTROLLER.md` - Invocation syntax for calling organs
- `RE-GE_OS_INTERFACE_02_EXTERNAL_BRIDGES.md` - Obsidian, Git, Max/MSP integration

## Python Implementation

### Key Modules (`rege/`)

| Module | Purpose |
|--------|---------|
| `core/constants.py` | Charge tiers, priorities, depth limits |
| `core/models.py` | Fragment, Patch, Invocation data classes |
| `parser/invocation_parser.py` | Ritual syntax parser |
| `routing/patchbay.py` | Priority queue system |
| `organs/*.py` | 10 organ handlers |
| `protocols/fuse01.py` | Fusion protocol |
| `cli.py` | Command-line interface |

### CLI Commands

```bash
rege invoke '<ritual syntax>'    # Execute invocation
rege status                      # Show system status
rege repl                        # Interactive mode
rege fragments list|show|create  # Fragment management
rege checkpoint create|list      # Checkpointing
rege recover [mode]              # System recovery
```

## Key Concepts

### Invocation Syntax
Organs are called using ritual syntax:
```
::CALL_ORGAN [ORGAN_NAME]
::WITH [SYMBOL or INPUT]
::MODE [INTENTION_MODE]
::DEPTH [light | standard | full spiral]
::EXPECT [output_form]
```

### Charge System
| Tier | Range | Behavior |
|------|-------|----------|
| LATENT | 0-25 | Background, no processing |
| PROCESSING | 26-50 | Active consideration |
| ACTIVE | 51-70 | Full engagement |
| INTENSE | 71-85 | Canon candidate |
| CRITICAL | 86-100 | Immediate action |

### Tag System
Content tagged for tracking: `CANON+`, `ECHO+`, `ARCHIVE+`, `VOLATILE+`, `RITUAL+`, `MIRROR+`, `REMIX+`, `MASK+`, `FUSE+`

### LG4 Translation Modes
Symbol-to-code conversion patterns:
- `FUNC_MODE` - Lyrics become Python functions
- `CLASS_MODE` - Archetypes become classes
- `WAVE_MODE` - Emotions become waveforms/LFOs
- `TREE_MODE` - Sentences become flowcharts
- `SIM_MODE` - Myths become simulations

### Laws
79+ recursive laws govern the system (e.g., LAW_01: Recursive Primacy, LAW_06: Symbol-to-Code Equivalence)

## Development

### Running Tests
```bash
pytest                      # Run all tests
pytest --cov=rege           # With coverage
pytest rege/tests/test_parser.py -v  # Specific file
```

### Working with Documentation
- Maintain the ritual/mythic tone and formatting conventions
- Use the established tag system when adding content
- Respect the inter-organ routing logic (Soul Patchbay as hub)
- Follow the 7-module AAW study flow: INPUT_RITUAL → RAA_ACADEMIC_LOOP → EMI_MYTH_INTERPRETATION → AA10_REFERENCIAL_CROSSMAPPING → SELF_AS_MIRROR → CODE_EXPORT_SCT → RECURSION_ENGINE_ARCHIVE

## File Naming Convention
`RE-GE_[TYPE]_[NUMBER]_[NAME].md`
- TYPE: ORG_BODY, OS_INTERFACE, AAW_CORE, PROTOCOL
- Stylized with `4` replacing `A` in certain contexts (ET4L, R!4L)

<!-- ORGANVM:AUTO:START -->
## System Context (auto-generated — do not edit)

**Organ:** ORGAN-I (Theory) | **Tier:** flagship | **Status:** PUBLIC_PROCESS
**Org:** `organvm-i-theoria` | **Repo:** `recursive-engine--generative-entity`

### Edges
- **Produces** → `unspecified`: theory

### Siblings in Theory
`organon-noumenon--ontogenetic-morphe`, `auto-revision-epistemic-engine`, `narratological-algorithmic-lenses`, `call-function--ontological`, `sema-metra--alchemica-mundi`, `system-governance-framework`, `cognitive-archaelogy-tribunal`, `a-recursive-root`, `radix-recursiva-solve-coagula-redi`, `.github`, `nexus--babel-alexandria-`, `reverse-engine-recursive-run`, `4-ivi374-F0Rivi4`, `cog-init-1-0-`, `collective-persona-operations` ... and 4 more

### Governance
- Foundational theory layer. No upstream dependencies.

*Last synced: 2026-03-08T20:11:34Z*

## Session Review Protocol

At the end of each session that produces or modifies files:
1. Run `organvm session review --latest` to get a session summary
2. Check for unimplemented plans: `organvm session plans --project .`
3. Export significant sessions: `organvm session export <id> --slug <slug>`
4. Run `organvm prompts distill --dry-run` to detect uncovered operational patterns

Transcripts are on-demand (never committed):
- `organvm session transcript <id>` — conversation summary
- `organvm session transcript <id> --unabridged` — full audit trail
- `organvm session prompts <id>` — human prompts only


## Active Directives

| Scope | Phase | Name | Description |
|-------|-------|------|-------------|
| system | any | prompting-standards | Prompting Standards |
| system | any | research-standards-bibliography | APPENDIX: Research Standards Bibliography |
| system | any | research-standards | METADOC: Architectural Typology & Research Standards |
| system | any | sop-ecosystem | METADOC: SOP Ecosystem — Taxonomy, Inventory & Coverage |
| system | any | autopoietic-systems-diagnostics | SOP: Autopoietic Systems Diagnostics (The Mirror of Eternity) |
| system | any | cicd-resilience-and-recovery | SOP: CI/CD Pipeline Resilience & Recovery |
| system | any | cross-agent-handoff | SOP: Cross-Agent Session Handoff |
| system | any | document-audit-feature-extraction | SOP: Document Audit & Feature Extraction |
| system | any | essay-publishing-and-distribution | SOP: Essay Publishing & Distribution |
| system | any | market-gap-analysis | SOP: Full-Breath Market-Gap Analysis & Defensive Parrying |
| system | any | pitch-deck-rollout | SOP: Pitch Deck Generation & Rollout |
| system | any | promotion-and-state-transitions | SOP: Promotion & State Transitions |
| system | any | repo-onboarding-and-habitat-creation | SOP: Repo Onboarding & Habitat Creation |
| system | any | research-to-implementation-pipeline | SOP: Research-to-Implementation Pipeline (The Gold Path) |
| system | any | security-and-accessibility-audit | SOP: Security & Accessibility Audit |
| system | any | session-self-critique | session-self-critique |
| system | any | source-evaluation-and-bibliography | SOP: Source Evaluation & Annotated Bibliography (The Refinery) |
| system | any | stranger-test-protocol | SOP: Stranger Test Protocol |
| system | any | strategic-foresight-and-futures | SOP: Strategic Foresight & Futures (The Telescope) |
| system | any | typological-hermeneutic-analysis | SOP: Typological & Hermeneutic Analysis (The Archaeology) |
| unknown | any | gpt-to-os | SOP_GPT_TO_OS.md |
| unknown | any | index | SOP_INDEX.md |
| unknown | any | obsidian-sync | SOP_OBSIDIAN_SYNC.md |

Linked skills: evaluation-to-growth


**Prompting (Anthropic)**: context 200K tokens, format: XML tags, thinking: extended thinking (budget_tokens)

<!-- ORGANVM:AUTO:END -->


## ⚡ Conductor OS Integration
This repository is a managed component of the ORGANVM meta-workspace.
- **Orchestration:** Use `conductor patch` for system status and work queue.
- **Lifecycle:** Follow the `FRAME -> SHAPE -> BUILD -> PROVE` workflow.
- **Governance:** Promotions are managed via `conductor wip promote`.
- **Intelligence:** Conductor MCP tools are available for routing and mission synthesis.
