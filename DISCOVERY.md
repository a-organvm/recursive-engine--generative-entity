# Discovery: organvm/recursive-engine--generative-entity

**Discovered:** 2026-06-22  
**Status:** REAL VALUE — promoted to ranked tier

## Value Thesis

RE:GE is the organvm estate's most complete working implementation of a modular, priority-queued, plugin-based workflow orchestration framework — and its highest latent value is precisely that: a reusable orchestration library, not a mythology tool. The repo ships as an installable Python package (`pip install -e .`) with a single runtime dependency (Click), 21 handler plugins extending a common `OrganHandler` ABC, a heap-based priority-routing queue with deadlock prevention, a regex-parsed DSL that maps free-form invocation syntax to typed `Invocation` objects, a full workflow engine (phases, conditional branching, compensation, step mode, dry run) with 6 built-in chains, JSON persistence with checkpointing, and three external bridges (Obsidian, Git, Max/MSP via OSC). Test suite: 1,254 tests at 85% coverage. The organ/dispatcher/patchbay stack is the cleanest implementation of the dispatching pattern anywhere in the estate, and ORGAN-IV (agentic-titan) and any downstream organs doing multi-step routing could import `rege.orchestration` directly rather than re-implementing it. The outer publication path — listing `rege` on PyPI as a lightweight symbolic workflow engine for creative-computing contexts — is enabled today: `pyproject.toml` has all required metadata, version is 1.0.0, classifiers and keywords are present. The OSC bridge to Max/MSP differentiates it in the live-performance-coding space where no existing workflow library speaks that protocol.

## Highest-Value First Task

**Publish `rege` to PyPI.** The package is structurally ready: `pyproject.toml` is complete with name, version, description, classifiers, scripts entrypoint, and single runtime dependency. Running `python -m build && twine upload dist/*` is the only missing step. This unlocks `pip install rege` for downstream organ consumers and establishes the estate's first publicly distributed library.
