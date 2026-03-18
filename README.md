# RE:GE - Recursive Engine: Generative Entity

[![CI](https://github.com/organvm-i-theoria/recursive-engine--generative-entity/actions/workflows/ci.yml/badge.svg)](https://github.com/organvm-i-theoria/recursive-engine--generative-entity/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-pending-lightgrey)](https://github.com/organvm-i-theoria/recursive-engine--generative-entity)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/organvm-i-theoria/recursive-engine--generative-entity/blob/main/LICENSE)
[![Organ I](https://img.shields.io/badge/Organ-I%20Theoria-8B5CF6)](https://github.com/organvm-i-theoria)
[![Status](https://img.shields.io/badge/status-active-brightgreen)](https://github.com/organvm-i-theoria/recursive-engine--generative-entity)
[![Python](https://img.shields.io/badge/lang-Python-informational)](https://github.com/organvm-i-theoria/recursive-engine--generative-entity)


[![ORGAN-I: Theory](https://img.shields.io/badge/ORGAN--I-Theory-1a237e?style=flat-square)](https://github.com/organvm-i-theoria)
[![Tests](https://img.shields.io/badge/tests-1254%20passing-brightgreen?style=flat-square)]()
[![Coverage](https://img.shields.io/badge/coverage-85%25-green?style=flat-square)]()
[![Python](https://img.shields.io/badge/python-%E2%89%A53.8-blue?style=flat-square)]()
[![License](https://img.shields.io/badge/license-MIT-blue?style=flat-square)](LICENSE)

> A symbolic operating system for myth, identity, ritual, and recursive systems — where software processes meaning the way human experience does.

[Problem Statement](#problem-statement) | [Core Concepts](#core-concepts) | [Related Work](#related-work) | [Installation](#installation--usage) | [Examples](#examples) | [Architecture](#architecture) | [Downstream Implementation](#downstream-implementation) | [Validation](#validation) | [Roadmap](#roadmap) | [Cross-References](#cross-references) | [Contributing](#contributing) | [License](#license)

---

## Problem Statement

Software has no concept of significance. Traditional systems store data as flat records — a string is a string whether it represents a passing thought or a life-defining event. Databases optimize for retrieval, not meaning. Version control tracks changes, not transformation. There is no infrastructure for the recursive, layered, emotionally weighted processes that define how humans actually relate to symbols, memories, and creative output.

This gap is not academic. Every creative practitioner who has built a body of work confronts it: the tools for *making* things and the tools for *understanding what those things mean* operate in entirely different planes. A musician can record a performance but cannot encode that the third phrase is a deliberate echo of a phrase from two years ago, that this echo has gained significance through repetition, or that the whole piece is a ritual response to a contradiction the artist has been processing across multiple works. The creative record is inert — a warehouse of files with no model of how they relate, accrete meaning, or transform over time.

RE:GE addresses this by implementing a **symbolic operating system**: a computational framework where every piece of content carries charge (emotional/symbolic weight), flows through specialized processors (organs), and undergoes transformation according to ceremonial logic (protocols). The system treats meaning as a first-class computational object — not metadata attached to files, but the primary substrate that the system operates on.

The contribution is epistemological. RE:GE provides a formal model for questions that are typically left to intuition: When does a recurring pattern become canonical? How should contradictions between creative fragments be resolved? What is the lifecycle of a creative idea from emergence through maturation to archival? By formalizing these processes as executable logic, RE:GE makes them inspectable, repeatable, and extensible — without reducing them to mechanical procedures.

---

## Core Concepts

### Concept 1: Fragments and Charge Dynamics

The atomic unit of RE:GE is the **Fragment** — a piece of meaningful content (a symbol, a memory, a creative artifact) that carries a **charge** value between 0 and 100. Charge represents significance: how much weight this fragment holds in the system's symbolic economy. Unlike metadata tags or priority flags, charge is dynamic — it changes as fragments interact, recur, fuse, or decay.

Charge maps to five behavioral tiers that determine how the system processes each fragment:

| Tier | Charge Range | System Behavior |
|------|-------------|-----------------|
| LATENT | 0–25 | Background presence. Minimal processing, available for retrieval but not actively engaged. |
| PROCESSING | 26–50 | Active consideration. The system acknowledges and routes this fragment through standard channels. |
| ACTIVE | 51–70 | Full engagement. The fragment participates in fusion eligibility checks and cross-organ routing. |
| INTENSE | 71–85 | Canon candidate. The fragment may be elevated to permanent canon status if it meets additional criteria. |
| CRITICAL | 86–100 | Immediate action. The system treats this as requiring ceremonial attention — emergency protocols, ritual court intervention, or forced resolution. |

This five-tier model emerged from the observation that creative significance is not binary (important / not important) but exists on a spectrum with qualitatively different behavioral thresholds. A latent fragment is not "less valid" than a critical one — it simply occupies a different phase in the symbolic lifecycle. The charge system encodes this distinction as executable logic rather than subjective interpretation.

Charge dynamics interact with time through the BLOOM_ENGINE organ (Organ 07), which implements seasonal mutation cycles. Fragments can gain charge through recurrence (appearing in multiple contexts), ritual processing (explicit invocation), or fusion with other high-charge fragments. They can lose charge through decay (time-based attenuation) or archival (deliberate removal from active circulation). This creates a living system where the significance landscape evolves naturally rather than remaining static after initial assignment.

### Concept 2: The Organ System (21 Specialized Processors)

RE:GE organizes its processing capabilities into **21 organs** — specialized handlers that each perform a distinct function in the symbolic operating system. This is not a plugin architecture or a microservice pattern. It is a model of differentiated function: each organ has its own valid modes of invocation, its own internal state, and its own relationship to the charge system. Organs interact through the routing layer (the Soul Patchbay), not through direct coupling.

The organ system is organized by functional domain:

**Narrative and Mythology** — HEART_OF_CANON (01), MYTHIC_SENATE (03), ARCHIVE_ORDER (04): These organs manage the canonical record. Heart of Canon creates and elevates mythology. Mythic Senate governs the law system. Archive Order handles storage, retrieval, and controlled decay.

**Reflection and Identity** — MIRROR_CABINET (02), MASK_ENGINE (11), ECHO_SHELL (09): These organs process self-reference. Mirror Cabinet handles reflection and grief work. Mask Engine manages identity layers and persona assembly. Echo Shell provides recursive invocation (calling an organ from within an organ).

**Ceremonial Logic** — RITUAL_COURT (05), DREAM_COUNCIL (10), STAGECRAFT_MODULE (21): These organs handle transformation events. Ritual Court resolves contradictions through deliberation. Dream Council processes collective input. Stagecraft Module embodies performance rituals.

**Generative and Economic** — BLOOM_ENGINE (07), CODE_FORGE (06), CHAMBER_COMMERCE (12), BLOCKCHAIN_ECONOMY (13), PROCESS_MONETIZER (14), AUDIENCE_ENGINE (15): These organs handle creation, transformation, and symbolic economy. Bloom Engine manages generative growth. Code Forge translates symbols to executable form. The commerce organs manage three internal currencies (dreampoints, looptokens, mirrorcredits).

**Context and Translation** — PLACE_PROTOCOLS (16), TIME_RULES (17), ANALOG_DIGITAL (18), PROCESS_PRODUCT (19), CONSUMPTION_PROTOCOL (20), PUBLISHING_TEMPLE (22): These organs manage the conditions under which processing occurs. Place Protocols defines 10 canonical spatial zones. Time Rules implements temporal recursion and bloom cycles. Publishing Temple gates the transition from internal process to external publication.

Every organ extends the `OrganHandler` abstract base class, ensuring consistent lifecycle management: invocation validation, state persistence, and participation in system-wide checkpointing and recovery.

### Concept 3: Ritual Syntax (A Domain-Specific Language for Meaning)

Conventional software exposes functionality through function calls, REST endpoints, or command flags. RE:GE uses a **ritual syntax** — a domain-specific language designed to make the act of invocation itself meaningful:

```
::CALL_ORGAN HEART_OF_CANON
::WITH "a memory that recurs in dreams"
::MODE mythic
::DEPTH standard
::EXPECT narrative
::CHARGE 72
```

Each line of an invocation carries semantic weight. `::CALL_ORGAN` names the processor. `::WITH` provides the symbolic input. `::MODE` selects the organ's processing intention (mythic, recursive, devotional, etc.). `::DEPTH` controls recursion limits across four tiers (light/standard/extended/full spiral). `::EXPECT` declares the desired output form. `::CHARGE` assigns initial significance.

The syntax is parsed by a regex-based engine (`InvocationParser`) that extracts structured `Invocation` objects, validates them against the organ registry, and routes them through the Soul Patchbay for execution. The parser supports chained invocations (multiple `::CALL_ORGAN` blocks in sequence), protocol invocations (`::CALL_PROTOCOL FUSE01`), and fragment references by name or version.

The ritual syntax is not decorative. It serves two architectural purposes: first, it makes invocations self-documenting — reading a chain of ritual commands reveals the *intention* of the processing sequence, not just its mechanics. Second, it creates a clean boundary between the human-facing interface (symbolic, expressive) and the machine-facing execution (typed, validated, queued). The parser is the bridge between these worlds.

### Concept 4: Protocols and Workflow Orchestration

Individual organ invocations solve point problems. **Protocols** solve systemic ones. RE:GE implements three core protocols:

**FUSE01** — Fragment fusion. When two or more fragments share sufficient overlap (overlap_count >= 2) and charge (>= 70), FUSE01 merges them into a `FusedFragment`. Three fusion modes (AUTO, INVOKED, FORCED) control the level of human intervention. Three charge calculation methods (INHERITED_MAX, AVERAGED, SUMMED_CAPPED) determine the resulting fragment's significance. Crucially, fusion is reversible: rollback is available within a 7-day window unless the CANON+ tag has been applied.

**System Recovery** — Four recovery modes (FULL_ROLLBACK, PARTIAL, RECONSTRUCT, EMERGENCY_STOP) handle corruption, deadlocks, data loss, and depth panics. Recovery operates on checkpoints maintained by the persistence layer.

**Law Enforcement** — Seven core laws (e.g., LAW_01 isolation, LAW_04 stagnation prevention, LAW_81 fusion violations) encode the system's invariants. Violations trigger consequences; laws can be activated or deactivated through the Mythic Senate organ.

For multi-step processes, RE:GE provides a **Ritual Chain Orchestrator** — a workflow engine that sequences organ invocations with branching, compensation, and error handling. Six built-in chains ship with the system:

1. **Canonization Ceremony**: HEART_OF_CANON → RITUAL_COURT → FUSE01 → ARCHIVE_ORDER — the path from raw fragment to permanent canon
2. **Contradiction Resolution**: Deliberation → conditional branching (bloom or fuse) → archival
3. **Grief Processing**: Six-phase ritual with compensation (what happens if grief processing fails at phase 3?)
4. **Emergency Recovery**: Court → snapshot → forced fusion → recovery → verification
5. **Seasonal Bloom**: Growth → mutation → archival check → consolidation → storage
6. **Fragment Lifecycle**: Creation → charge cultivation → tagging → storage → decay

The orchestrator supports step mode (pause between phases), dry run (simulate without executing), and full execution statistics.

### Concept 5: External Bridges (Obsidian, Git, Max/MSP)

RE:GE is not a closed system. Three **bridges** connect it to external tools:

**Obsidian Bridge** — Exports fragments as Markdown notes with YAML frontmatter (charge, tags, organ history) into an Obsidian vault. Imports Obsidian notes back as fragments. This allows RE:GE's symbolic processing to work alongside a knowledge management system.

**Git Bridge** — Installs Git hooks that log commits as invocation events. Maps branch creation, merges, and tags to symbolic operations. Validates branch names against organ naming conventions. This embeds version control activity into the symbolic record.

**Max/MSP Bridge** — Communicates via OSC (Open Sound Control) protocol with Max/MSP patches. Sends fragment charge levels and organ states as real-time data streams. Receives performance events as invocations. This connects the symbolic operating system to audio-visual creative environments.

Each bridge extends the `ExternalBridge` abstract base class with connect/disconnect lifecycle, operation logging, and sensitive configuration masking.

---

## Related Work

RE:GE operates at the intersection of several research traditions, though no existing system combines all of its concerns:

**Computational Creativity** — Systems like Margaret Boden's computational creativity framework and the DARCI (Digital Artist Communicating Intention) project formalize aspects of creative process. RE:GE differs by modeling the *lifecycle* of creative artifacts rather than the generation of new ones. Where DARCI generates art, RE:GE manages the symbolic economy around art.

**Knowledge Graphs and Semantic Systems** — Tools like Roam Research, Obsidian, and LogSeq implement bidirectional linking and networked thought. RE:GE goes further by adding charge dynamics (significance weighting that changes over time), ceremonial processing (explicit transformation events), and a formal protocol system (fusion, canonization, recovery). The Obsidian bridge connects RE:GE to this ecosystem without replacing it.

**Ritual and Performance Computing** — Projects like the MIT Media Lab's "Ritual Design" research and David Rokeby's "Very Nervous System" explore computational ritual and embodied interaction. RE:GE formalizes ritual as a software architecture pattern — invocation syntax, ceremonial chains, organ-based processing — rather than as a physical interface design.

**Agent-Based Systems** — Multi-agent frameworks like AutoGen, CrewAI, and LangChain implement specialized processing agents. RE:GE's organ system is structurally similar but differs in its domain model: organs process symbolic meaning rather than task completions. The system also implements modular routing (Soul Patchbay) rather than fixed agent-to-agent communication.

**Personal Mythology and Depth Psychology** — The organ naming and charge system draw from Jungian analytical psychology (shadow work, individuation), Joseph Campbell's monomyth (hero's journey stages), and ritual studies. These are not metaphorical mappings but structural influences on the system's processing logic.

---

## Installation & Usage

### Prerequisites

- Python >= 3.8
- pip (or any Python package manager)
- Git (for cloning)

### Installation

```bash
# Clone the repository
git clone https://github.com/organvm-i-theoria/recursive-engine--generative-entity.git
cd recursive-engine--generative-entity

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# Install the package (editable mode for development)
pip install -e .

# Install development dependencies (pytest, coverage)
pip install -e ".[dev]"

# Verify installation
rege status
```

### Runtime Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `click` | >= 8.0.0 | CLI framework |

RE:GE has a single runtime dependency. All 21 organs, protocols, bridges, and the orchestration engine are implemented in pure Python with no external libraries beyond Click for the command-line interface.

### Development Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `pytest` | >= 7.0.0 | Test framework |
| `pytest-cov` | >= 4.0.0 | Coverage reporting |

---

## Examples

### Example 1: Invoking the Heart of Canon

The most common operation is invoking an organ to process a symbolic input. This example invokes HEART_OF_CANON in mythic mode to create a canon event:

```bash
rege invoke '::CALL_ORGAN HEART_OF_CANON
::WITH "the threshold crossing at midnight"
::MODE mythic
::DEPTH standard
::CHARGE 75'
```

The invocation creates a `CanonEvent` with charge 75 (INTENSE tier — canon candidate). Because the charge exceeds 71, the fragment is eligible for canonization. The system logs the event, updates the recurrence tracker, and returns a narrative output:

```json
{
  "status": "success",
  "organ": "HEART_OF_CANON",
  "mode": "mythic",
  "output": {
    "event_id": "canon_evt_001",
    "charge": 75,
    "tier": "INTENSE",
    "canonization_eligible": true,
    "recurrence": 1
  },
  "execution_time_ms": 12
}
```

If the same symbol recurs three or more times, its charge is boosted by `recurrence * 5`. Recurring patterns gain weight automatically — the system recognizes significance through repetition, not just explicit assignment.

### Example 2: Running a Ritual Chain (Canonization Ceremony)

For multi-step processes, ritual chains orchestrate sequences of organ invocations with conditional branching:

```python
from rege.orchestration import RitualChainOrchestrator
from rege.orchestration.builtin_chains import register_builtin_chains
from rege.organs.registry import register_default_organs

# Initialize
register_default_organs()
register_builtin_chains()

# Execute the canonization ceremony
orchestrator = RitualChainOrchestrator()
execution = orchestrator.execute_chain(
    "canonization_ceremony",
    context={"charge": 85, "symbol": "the recurring dream"}
)

# The ceremony follows 4 phases:
# 1. HEART_OF_CANON: Evaluate the fragment's mythic significance
# 2. RITUAL_COURT: Deliberate whether canonization is warranted
# 3. FUSE01: Merge with related high-charge fragments (if any)
# 4. ARCHIVE_ORDER: Commit to permanent canon

for result in execution.phase_results:
    print(f"Phase: {result.phase_name} -> {result.status.value}")
```

The canonization ceremony includes a conditional branch: if RITUAL_COURT's verdict is "deny," the chain skips FUSE01 and routes directly to ARCHIVE_ORDER with a "deferred" tag. Compensation logic handles failures at each phase — if FUSE01 fails, the system rolls back to the pre-fusion state.

### Example 3: Interactive REPL Session

The REPL provides an exploratory interface for working with the symbolic operating system:

```bash
$ rege repl

RE:GE v1.0.0 - Symbolic Operating System
Type :help for commands, :quit to exit

rege> :organs
21 organs registered:
  HEART_OF_CANON, MIRROR_CABINET, MYTHIC_SENATE, ARCHIVE_ORDER,
  RITUAL_COURT, CODE_FORGE, BLOOM_ENGINE, ECHO_SHELL,
  DREAM_COUNCIL, MASK_ENGINE, CHAMBER_COMMERCE, BLOCKCHAIN_ECONOMY,
  PROCESS_MONETIZER, AUDIENCE_ENGINE, PLACE_PROTOCOLS, TIME_RULES,
  ANALOG_DIGITAL, PROCESS_PRODUCT, CONSUMPTION_PROTOCOL,
  STAGECRAFT_MODULE, PUBLISHING_TEMPLE

rege> :modes MIRROR_CABINET
Valid modes: reflect_grief, shadow_work

rege> ::CALL_ORGAN MIRROR_CABINET
::WITH "the face I show at work vs. who I am alone"
::MODE shadow_work
::DEPTH standard

Processing... shadow_work mode engaged.
Output: Shadow analysis generated. Charge delta: +8 (confrontation bonus).

rege> :status
System Status:
  Active organs: 21/21
  Queue depth: 0
  Total invocations: 1
  Last invocation: MIRROR_CABINET (shadow_work)
```

---

## Architecture

### System Overview

```
                    ┌─────────────────────┐
                    │     CLI / REPL      │
                    │   (Click framework) │
                    └──────────┬──────────┘
                               │ raw text
                    ┌──────────▼──────────┐
                    │  Invocation Parser  │
                    │  (regex-based DSL)  │
                    └──────────┬──────────┘
                               │ Invocation object
                    ┌──────────▼──────────┐
                    │     Validator       │
                    │ (organ/mode/depth)  │
                    └──────────┬──────────┘
                               │ validated Invocation
                    ┌──────────▼──────────┐
                    │    Soul Patchbay    │
                    │  (priority queue +  │
                    │  collision detect + │
                    │  deadlock prevent)  │
                    └──────────┬──────────┘
                               │ Patch
                    ┌──────────▼──────────┐
                    │     Dispatcher      │
                    │ (organ lookup +     │
                    │  depth tracking +   │
                    │  execution + log)   │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
    ┌─────────▼──────┐ ┌──────▼───────┐ ┌──────▼───────┐
    │  21 Organs     │ │  Protocols   │ │  Bridges     │
    │ (Heart, Mirror,│ │ (FUSE01,     │ │ (Obsidian,   │
    │  Senate, ...)  │ │  Recovery,   │ │  Git,        │
    │                │ │  Enforcement)│ │  Max/MSP)    │
    └────────────────┘ └──────────────┘ └──────────────┘
              │                │                │
              └────────────────┼────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │    Persistence      │
                    │  (JSON archive +    │
                    │   checkpoints)      │
                    └─────────────────────┘
```

### Layer Responsibilities

| Layer | Directory | Responsibility |
|-------|-----------|---------------|
| **Core** | `rege/core/` | Type system (charge tiers, priorities, depth limits), data models (Fragment, Patch, Invocation), exception hierarchy (16 classes) |
| **Parser** | `rege/parser/` | Ritual syntax DSL → structured `Invocation` objects. Supports single, chained, and protocol invocations. |
| **Routing** | `rege/routing/` | Soul Patchbay (heap-based priority queue with collision detection, junction creation, deadlock prevention). Dispatcher (lifecycle: PARSE → VALIDATE → QUEUE → EXECUTE → FORMAT → LOG). Depth tracker (4-tier recursion guard: 7/12/21/33). |
| **Organs** | `rege/organs/` | 21 handlers extending `OrganHandler` ABC. Each has distinct modes, state management, and lifecycle hooks. Registry manages lookup and bulk state operations. |
| **Protocols** | `rege/protocols/` | FUSE01 (3-mode fragment fusion with rollback), Recovery (4-mode system recovery), Enforcement (7+ core laws with violation tracking). |
| **Bridges** | `rege/bridges/` | External integrations. Obsidian (vault export/import), Git (hook installation, commit logging), Max/MSP (OSC communication). |
| **Orchestration** | `rege/orchestration/` | Ritual Chain engine. Phases, branches, compensation, step mode, dry run. 6 built-in chains. |
| **Persistence** | `rege/persistence/` | JSON file-based archive (6 categories in `.rege_archive/`). Checkpoint manager for system state snapshots. |
| **CLI** | `rege/cli.py` | 15 Click command groups. Interactive REPL with 12 special commands. JSON and colored terminal output. |

### Recursion Depth Management

The depth tracker implements four-tier recursion ceilings — a critical safety mechanism for a system that explicitly supports recursive invocation:

| Tier | Max Depth | Trigger | Action |
|------|-----------|---------|--------|
| STANDARD | 7 | Default | Normal routing continues |
| EXTENDED | 12 | `LAW_LOOP+` flag present | Extended processing with monitoring |
| EMERGENCY | 21 | `RITUAL_COURT` override | Emergency escalation path |
| ABSOLUTE | 33 | Hard limit | `PanicStop` exception — system halts |

---

## Downstream Implementation

RE:GE provides the theoretical vocabulary that downstream organs implement in applied contexts:

- **ORGAN-II (Art):** The [Omni-Dromenon Engine](https://github.com/organvm-ii-poiesis/metasystem-master) builds performance systems on top of RE:GE's organ model, applying the charge dynamics and ritual syntax concepts to live creative performance. The deployed website [etceter4.com](https://github.com/organvm-ii-poiesis/a-mavs-olevm) implements RE:GE's Pantheon architecture as a navigable web experience.

- **ORGAN-III (Commerce):** Commercial products in [ORGAN-III](https://github.com/organvm-iii-ergon) apply RE:GE's modular processing pattern (specialized handlers with routing and priority) to business domains — from [data scraping infrastructure](https://github.com/organvm-iii-ergon/public-record-data-scrapper) to [trading systems](https://github.com/organvm-iii-ergon/trade-perpetual-future).

- **ORGAN-IV (Orchestration):** The [Agentic Titan](https://github.com/organvm-iv-taxis/agentic-titan) multi-agent swarm framework shares RE:GE's architectural commitment to modular, topology-aware processing — extending the organ pattern into multi-agent AI orchestration with 6 distinct topologies.

The dependency flow is unidirectional: ORGAN-I (theory) → ORGAN-II (artistic implementation) → ORGAN-III (commercial application). RE:GE establishes the conceptual framework; downstream organs instantiate it in their respective domains.

---

## Validation

### Test Suite

RE:GE ships with **1,254 passing tests** at **85% code coverage**, organized across 33 test files:

```bash
# Run the full suite
pytest

# Run with coverage reporting
pytest --cov=rege --cov-report=term-missing

# Run a specific area
pytest rege/tests/test_orchestration.py -v
```

### Coverage by Area

| Area | Test Files | Focus |
|------|-----------|-------|
| Parser | `test_parser.py` | Syntax parsing, edge cases, malformed input |
| Routing | `test_routing.py`, `test_dispatcher.py`, `test_patchbay_coverage.py`, `test_depth_tracker_coverage.py` | Priority queuing, collision detection, deadlock prevention, depth limits |
| Organs | `test_organs.py`, `test_organs_extended.py`, 11 per-organ files | Mode validation, state management, charge dynamics per organ |
| Protocols | `test_protocols.py` | Fusion eligibility, rollback, recovery modes, law enforcement |
| CLI | `test_cli.py`, `test_cli_coverage.py`, `test_cli_new_commands.py` | All 15 command groups, REPL, output formatting |
| Persistence | `test_persistence.py` | Archive read/write, checkpoint create/restore, schema validation |
| Orchestration | `test_orchestration.py` | Chain execution, branching, compensation, step mode |
| Bridges | `test_bridges.py` | Connect/disconnect lifecycle, Obsidian export/import, Git hooks, Max/MSP OSC |

### Quality Metrics

| Metric | Value |
|--------|-------|
| Total tests | 1,254 |
| Coverage | 85% |
| Test framework | pytest >= 7.0.0 |
| Passing rate | 100% (0 failures, 0 errors) |
| Runtime dependencies | 1 (Click) |
| Python compatibility | 3.8, 3.9, 3.10, 3.11, 3.12 |

---

## Roadmap

The ROADMAP.md tracks a 15-phase development plan. Phases 1-6 are complete (core implementation through bridges and orchestration). Remaining phases focus on:

- **Phase 7:** INTERLOCUTOR organ (Organ 22 successor — conversational interface)
- **Phase 8:** Advanced workflow templates (user-defined ritual chains)
- **Phase 9:** Web interface (browser-based REPL and visualization)
- **Phase 10:** Performance optimization (large-scale fragment management)
- **Phases 11-15:** Extended bridge ecosystem, collaborative multi-user features, and institutional deployment

See [ROADMAP.md](ROADMAP.md) for the complete plan with phase descriptions and dependencies.

---

## Cross-References

### Within ORGAN-I (Theory)

- [organon-noumenon--ontogenetic-morphe](https://github.com/organvm-i-theoria/organon-noumenon--ontogenetic-morphe) — Ontological morphogenesis framework. Shares RE:GE's concern with formal models of transformation, applied specifically to ontogenetic (developmental) change.
- [sema-metra--alchemica-mundi](https://github.com/organvm-i-theoria/sema-metra--alchemica-mundi) — Semantic measurement and alchemical transformation. Implements a complementary axiom system (10 axioms) for measuring symbolic significance.
- [auto-revision-epistemic-engine](https://github.com/organvm-i-theoria/auto-revision-epistemic-engine) — Self-revising epistemic system. Extends the recursive self-modification concepts that RE:GE's ECHO_SHELL organ implements.

### Across the Eight-Organ System

| Organ | Related Repo | Relationship |
|-------|-------------|-------------|
| II (Art) | [metasystem-master](https://github.com/organvm-ii-poiesis/metasystem-master) | Implements RE:GE's organ model in creative performance contexts |
| III (Commerce) | [public-record-data-scrapper](https://github.com/organvm-iii-ergon/public-record-data-scrapper) | Applies modular processing pattern to commercial data infrastructure |
| IV (Orchestration) | [agentic-titan](https://github.com/organvm-iv-taxis/agentic-titan) | Extends organ-based architecture into multi-agent AI orchestration |
| V (Public Process) | [How I Used 4 AI Agents to Cross-Validate an Eight-Organ System](https://github.com/organvm-v-logos) | Process essay documenting the AI-conductor methodology behind this system |

### System Context

RE:GE is part of the [organvm eight-organ system](https://github.com/meta-organvm) — a creative-institutional architecture coordinating ~79 repositories across 8 GitHub organizations. It serves as the **theoretical foundation** (ORGAN-I) that establishes vocabulary, formal models, and architectural patterns used by all downstream organs.

---

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

### Areas for Contribution

- **New organs:** Implement additional specialized processors following the `OrganHandler` ABC
- **Bridge integrations:** Connect RE:GE to additional external tools (Notion, Logseq, Ableton Live, etc.)
- **Ritual chain templates:** Design new multi-step workflows for specific creative processes
- **Documentation:** Expand the academic wing, add usage examples, improve organ specifications
- **Testing:** Increase coverage beyond 85%, add property-based tests, add integration tests

### Development Setup

```bash
git clone https://github.com/organvm-i-theoria/recursive-engine--generative-entity.git
cd recursive-engine--generative-entity
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest  # verify all 1,254 tests pass
```

---

## License

MIT License — see [LICENSE](LICENSE) for the full text.

---

## Author & Contact

**Author:** [@4444J99](https://github.com/4444J99)
**Organization:** [organvm-i-theoria](https://github.com/organvm-i-theoria) (ORGAN-I: Theory)
**System:** [organvm eight-organ system](https://github.com/meta-organvm)

*Last updated: 2026-02-10*

<!-- SYSTEM-NAV-START -->

---

<sub>[Case Study](https://4444j99.github.io/portfolio/projects/recursive-engine/) · [Portfolio](https://4444j99.github.io/portfolio/) · [System Directory](https://4444j99.github.io/portfolio/directory/) · [ORGAN I · Theoria](https://organvm-i-theoria.github.io/) · Part of the <a href="https://4444j99.github.io/portfolio/directory/">ORGANVM eight-organ system</a></sub>

<!-- SYSTEM-NAV-END -->
