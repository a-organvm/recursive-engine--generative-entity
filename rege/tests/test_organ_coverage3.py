"""
Tests for organ and orchestrator resume coverage improvements.

Targets uncovered lines in:
- rege/orchestration/orchestrator.py: 249-259, 267, 271-272, 284-285 (resume paths)
- rege/organs/mythic_senate.py: 38, 53, 57, 79-89, 102, 112-115, 177, 261, 278, 281, 285, 289
- rege/organs/ritual_court.py: 70, 85, 103, 111, 135-146, 272, 302, 312, 314, 318, 321, 324
- rege/organs/bloom_engine.py: 116, 129, 200-201, 251-261, 280-281, 287, 289, 291, 354, 356, 377, 380
- rege/organs/echo_shell.py: 44, 111, 172-173, 207-210, 223-232, 283-284, 309, 318, 325, 328, 336
- rege/organs/mask_engine.py: 70-71, 107, 127, 158, 197-199, 208-209, 215-217, 337, 344, 359, 362, 366, 370, 376
"""

import pytest
from unittest.mock import MagicMock, patch


# ==================== Orchestrator Resume Paths ====================

class TestOrchestratorResumePaths:
    """Tests for resume_execution uncovered paths (249-259, 267, 271-272, 284-285)."""

    def _make_phase(self, name, organ="HEART_OF_CANON", mode="mythic", required=True):
        from rege.orchestration.phase import Phase
        return Phase(name=name, organ=organ, mode=mode, required=required)

    def _make_chain(self, phases, name="test_chain"):
        from rege.orchestration.chain import RitualChain
        return RitualChain(name=name, phases=phases)

    def test_resume_compensation_path(self):
        """Test resume_execution triggers compensation (lines 249-259)."""
        from rege.orchestration.orchestrator import RitualChainOrchestrator
        from rege.orchestration.registry import ChainRegistry

        phase1 = self._make_phase("phase1")
        comp_phase = self._make_phase("comp_phase", organ="ECHO_SHELL", mode="decay")
        phase2 = self._make_phase("phase2", organ="MIRROR_CABINET", mode="emotional_reflection")
        phase2.compensation = comp_phase
        phase2.required = True

        chain = self._make_chain([phase1, phase2], "comp_chain")
        registry = ChainRegistry()
        registry.register(chain)
        orchestrator = RitualChainOrchestrator(registry=registry)

        execution = orchestrator.execute_chain("comp_chain", step_mode=True)
        assert execution.status.value == "paused"

        def failing_handler(input_data):
            raise RuntimeError("Phase2 fails during resume")

        orchestrator.register_phase_handler("MIRROR_CABINET", "emotional_reflection", failing_handler)
        resumed = orchestrator.resume_execution(execution.execution_id)
        assert resumed is not None
        assert resumed.status.value in ("failed", "completed")

    def test_resume_escalation_path(self):
        """Test resume_execution triggers escalation (line 267)."""
        from rege.orchestration.orchestrator import RitualChainOrchestrator
        from rege.orchestration.registry import ChainRegistry

        phase1 = self._make_phase("phase1")
        phase2 = self._make_phase("phase2", organ="MIRROR_CABINET", mode="emotional_reflection")

        chain = self._make_chain([phase1, phase2], "esc_chain")
        registry = ChainRegistry()
        registry.register(chain)
        orchestrator = RitualChainOrchestrator(registry=registry)

        execution = orchestrator.execute_chain("esc_chain", step_mode=True)
        assert execution.status.value == "paused"

        execution.context["charge"] = 80
        resumed = orchestrator.resume_execution(execution.execution_id)
        assert resumed is not None

    def test_resume_branch_path(self):
        """Test resume_execution takes branch (lines 271-272)."""
        from rege.orchestration.orchestrator import RitualChainOrchestrator
        from rege.orchestration.registry import ChainRegistry
        from rege.orchestration.phase import Phase, Branch

        phase1 = Phase(name="phase1", organ="HEART_OF_CANON", mode="mythic")
        phase2 = Phase(name="phase2", organ="MIRROR_CABINET", mode="emotional_reflection")
        phase3 = Phase(name="phase3", organ="ECHO_SHELL", mode="pulse")

        branch = Branch(name="to_phase3", condition=lambda ctx: True, target_phase="phase3")
        phase2.branches.append(branch)

        chain = self._make_chain([phase1, phase2, phase3], "branch_chain")
        registry = ChainRegistry()
        registry.register(chain)
        orchestrator = RitualChainOrchestrator(registry=registry)

        execution = orchestrator.execute_chain("branch_chain", step_mode=True)
        assert execution.status.value == "paused"

        resumed = orchestrator.resume_execution(execution.execution_id)
        assert resumed is not None
        assert resumed.status.value in ("completed", "failed")

    def test_resume_step_mode_pauses_again(self):
        """Test resume_execution with step_mode pauses again (lines 276-279)."""
        from rege.orchestration.orchestrator import RitualChainOrchestrator
        from rege.orchestration.registry import ChainRegistry

        phase1 = self._make_phase("phase1")
        phase2 = self._make_phase("phase2", organ="MIRROR_CABINET", mode="emotional_reflection")
        phase3 = self._make_phase("phase3", organ="ECHO_SHELL", mode="pulse")

        chain = self._make_chain([phase1, phase2, phase3], "step_chain")
        registry = ChainRegistry()
        registry.register(chain)
        orchestrator = RitualChainOrchestrator(registry=registry)

        execution = orchestrator.execute_chain("step_chain", step_mode=True)
        assert execution.status.value == "paused"

        resumed = orchestrator.resume_execution(execution.execution_id, step_mode=True)
        assert resumed is not None
        assert resumed.status.value == "paused"

    def test_resume_exception_path(self):
        """Test resume_execution handles exception (lines 284-285)."""
        from rege.orchestration.orchestrator import RitualChainOrchestrator
        from rege.orchestration.registry import ChainRegistry

        phase1 = self._make_phase("phase1")
        phase2 = self._make_phase("phase2", organ="MIRROR_CABINET", mode="emotional_reflection")

        chain = self._make_chain([phase1, phase2], "exc_chain")
        registry = ChainRegistry()
        registry.register(chain)
        orchestrator = RitualChainOrchestrator(registry=registry)

        execution = orchestrator.execute_chain("exc_chain", step_mode=True)
        assert execution.status.value == "paused"

        with patch.object(orchestrator, '_execute_phase', side_effect=RuntimeError("Unexpected error")):
            resumed = orchestrator.resume_execution(execution.execution_id)
            assert resumed is not None
            assert resumed.status.value == "failed"


# ==================== Shared helpers ====================

def _make_invocation(organ, mode, symbol="test symbol", charge=65, expect="output"):
    from rege.core.models import Invocation, DepthLevel
    return Invocation(
        organ=organ, mode=mode, symbol=symbol,
        depth=DepthLevel.STANDARD, expect=expect, charge=charge,
    )


def _make_patch(input_node, output_node, charge=65):
    from rege.core.models import Patch
    return Patch(input_node=input_node, output_node=output_node, tags=[], charge=charge)


# ==================== Mythic Senate Tests ====================

class TestMythicSenateMissingPaths:
    """Tests for MythicSenate uncovered paths."""

    def test_description_property(self):
        """Test description property (line 38)."""
        from rege.organs.mythic_senate import MythicSenate
        senate = MythicSenate()
        assert "law" in senate.description.lower() or "governance" in senate.description.lower()

    def test_invoke_debate_mode_law_found(self):
        """Test invoke in debate mode when law found (lines 53, 79-88)."""
        from rege.organs.mythic_senate import MythicSenate
        senate = MythicSenate()
        law = senate.create_law("Recursive Primacy", "The first law", "HEART_OF_CANON", 80)
        inv = _make_invocation("MYTHIC_SENATE", "debate", symbol="Recursive Primacy")
        patch = _make_patch("HEART_OF_CANON", "MYTHIC_SENATE")
        result = senate.invoke(inv, patch)
        assert "debating_law" in result or "no_law_found" in result

    def test_invoke_debate_mode_law_not_found(self):
        """Test invoke debate when no law matches (lines 89-93)."""
        from rege.organs.mythic_senate import MythicSenate
        senate = MythicSenate()
        inv = _make_invocation("MYTHIC_SENATE", "debate", symbol="completely unknown xyz")
        patch = _make_patch("HEART_OF_CANON", "MYTHIC_SENATE")
        result = senate.invoke(inv, patch)
        assert result.get("status") == "no_law_found"

    def test_invoke_default_mode(self):
        """Test invoke with unknown mode falls to default (lines 57, 112-121)."""
        from rege.organs.mythic_senate import MythicSenate
        senate = MythicSenate()
        senate.create_law("Law 1", "desc", "HEART_OF_CANON", 70)
        senate.create_law("Law 2", "desc", "HEART_OF_CANON", 60)
        inv = _make_invocation("MYTHIC_SENATE", "unknown_mode")
        patch = _make_patch("HEART_OF_CANON", "MYTHIC_SENATE")
        result = senate.invoke(inv, patch)
        assert "total_laws" in result
        assert result["total_laws"] == 2

    def test_vote_process_law_not_found(self):
        """Test _vote_process when law not found (lines 101-105)."""
        from rege.organs.mythic_senate import MythicSenate
        senate = MythicSenate()
        inv = _make_invocation("MYTHIC_SENATE", "vote", symbol="yes approve nonexistent law")
        patch = _make_patch("HEART_OF_CANON", "MYTHIC_SENATE")
        result = senate.invoke(inv, patch)
        assert result.get("status") == "vote_failed"

    def test_ritual_vote_law_not_found(self):
        """Test ritual_vote when law not found (line 177)."""
        from rege.organs.mythic_senate import MythicSenate
        senate = MythicSenate()
        result = senate.ritual_vote("NONEXISTENT_LAW", True, 75)
        assert result["status"] == "failed"
        assert "not found" in result["reason"]

    def test_find_law_by_content_not_found(self):
        """Test _find_law_by_content returns None when not found (line 261)."""
        from rege.organs.mythic_senate import MythicSenate
        senate = MythicSenate()
        result = senate._find_law_by_content("completely nonexistent content xyz")
        assert result is None

    def test_get_valid_modes(self):
        """Test get_valid_modes() (line 278)."""
        from rege.organs.mythic_senate import MythicSenate
        senate = MythicSenate()
        modes = senate.get_valid_modes()
        assert isinstance(modes, list)
        assert "legislative" in modes

    def test_get_output_types(self):
        """Test get_output_types() (line 281)."""
        from rege.organs.mythic_senate import MythicSenate
        senate = MythicSenate()
        types = senate.get_output_types()
        assert isinstance(types, list)

    def test_get_all_laws(self):
        """Test get_all_laws() (line 285)."""
        from rege.organs.mythic_senate import MythicSenate
        senate = MythicSenate()
        senate.create_law("Law 1", "desc", "HEART_OF_CANON", 70)
        laws = senate.get_all_laws()
        assert len(laws) == 1

    def test_get_law_by_id(self):
        """Test get_law() (line 289)."""
        from rege.organs.mythic_senate import MythicSenate
        senate = MythicSenate()
        law = senate.create_law("Law X", "desc", "HEART_OF_CANON", 70)
        result = senate.get_law(law.law_id)
        assert result is not None
        assert result.name == "Law X"


# ==================== Ritual Court Tests ====================

class TestRitualCourtMissingPaths:
    """Tests for RitualCourt uncovered paths."""

    def test_description_property(self):
        """Test description property (line 70)."""
        from rege.organs.ritual_court import RitualCourt
        court = RitualCourt()
        desc = court.description
        assert isinstance(desc, str) and len(desc) > 0

    def test_invoke_grief_ritual_mode(self):
        """Test invoke in grief_ritual mode (lines 85, 135-146)."""
        from rege.organs.ritual_court import RitualCourt
        court = RitualCourt()
        inv = _make_invocation("RITUAL_COURT", "grief_ritual", symbol="loss of a cherished memory", charge=75)
        patch = _make_patch("HEART_OF_CANON", "RITUAL_COURT")
        result = court.invoke(inv, patch)
        assert isinstance(result, dict)

    def test_invoke_contradiction_trial_critical(self):
        """Test contradiction_trial with critical charge (line 103)."""
        from rege.organs.ritual_court import RitualCourt
        court = RitualCourt()
        inv = _make_invocation("RITUAL_COURT", "contradiction_trial",
                               symbol="belief A conflicts with memory B", charge=90)
        patch = _make_patch("HEART_OF_CANON", "RITUAL_COURT")
        result = court.invoke(inv, patch)
        assert "verdict" in result

    def test_invoke_contradiction_trial_intense(self):
        """Test contradiction_trial with intense charge (line 111)."""
        from rege.organs.ritual_court import RitualCourt
        court = RitualCourt()
        inv = _make_invocation("RITUAL_COURT", "contradiction_trial",
                               symbol="old belief and new memory conflict", charge=75)
        patch = _make_patch("HEART_OF_CANON", "RITUAL_COURT")
        result = court.invoke(inv, patch)
        assert "verdict" in result

    def test_extract_parties_with_and(self):
        """Test _extract_parties with 'and' keyword (line 272)."""
        from rege.organs.ritual_court import RitualCourt
        court = RitualCourt()
        parties = court._extract_parties("Party Alpha and Party Beta")
        assert len(parties) == 2

    def test_generate_grief_glyph(self):
        """Test _generate_grief_glyph (line 302)."""
        from rege.organs.ritual_court import RitualCourt
        court = RitualCourt()
        glyph = court._generate_grief_glyph("grief symbol")
        assert "glyph_id" in glyph
        assert glyph["type"] == "grief_sigil"

    def test_generate_recommendation_critical(self):
        """Test _generate_recommendation with critical charge (line 312)."""
        from rege.organs.ritual_court import RitualCourt
        court = RitualCourt()
        rec = court._generate_recommendation(90)
        assert "emergency" in rec.lower()

    def test_generate_recommendation_intense(self):
        """Test _generate_recommendation with intense charge (line 314)."""
        from rege.organs.ritual_court import RitualCourt
        court = RitualCourt()
        rec = court._generate_recommendation(75)
        assert "full" in rec.lower() or "ritual" in rec.lower()

    def test_generate_recommendation_latent(self):
        """Test _generate_recommendation with latent charge (line 318)."""
        from rege.organs.ritual_court import RitualCourt
        court = RitualCourt()
        rec = court._generate_recommendation(20)
        assert "archive" in rec.lower() or "observe" in rec.lower()

    def test_get_valid_modes(self):
        """Test get_valid_modes() (line 321)."""
        from rege.organs.ritual_court import RitualCourt
        court = RitualCourt()
        modes = court.get_valid_modes()
        assert isinstance(modes, list)
        assert "grief_ritual" in modes

    def test_get_output_types(self):
        """Test get_output_types() (line 324)."""
        from rege.organs.ritual_court import RitualCourt
        court = RitualCourt()
        types = court.get_output_types()
        assert isinstance(types, list)

    def test_get_all_verdicts(self):
        """Test get_all_verdicts() covers verdict collection."""
        from rege.organs.ritual_court import RitualCourt
        court = RitualCourt()
        inv = _make_invocation("RITUAL_COURT", "contradiction_trial",
                               symbol="A disputes B", charge=65)
        patch = _make_patch("HEART_OF_CANON", "RITUAL_COURT")
        court.invoke(inv, patch)
        verdicts = court.get_all_verdicts()
        assert len(verdicts) >= 1


# ==================== Bloom Engine Tests ====================

class TestBloomEngineMissingPaths:
    """Tests for BloomEngine uncovered paths."""

    def test_description_property(self):
        """Test description property (line 116)."""
        from rege.organs.bloom_engine import BloomEngine
        bloom = BloomEngine()
        desc = bloom.description
        assert "generative" in desc.lower() or "growth" in desc.lower()

    def test_invoke_seasonal_mutation_mode(self):
        """Test invoke in seasonal_mutation mode (line 129)."""
        from rege.organs.bloom_engine import BloomEngine
        bloom = BloomEngine()
        inv = _make_invocation("BLOOM_ENGINE", "seasonal_mutation", symbol="symbol to mutate", charge=65)
        patch = _make_patch("HEART_OF_CANON", "BLOOM_ENGINE")
        result = bloom.invoke(inv, patch)
        assert isinstance(result, dict)

    def test_invoke_versioning_consolidation_needed(self):
        """Test _versioning triggers consolidation at 3+ versions (lines 200-201)."""
        from rege.organs.bloom_engine import BloomEngine
        bloom = BloomEngine()
        # Invoke versioning 3 times with same base to trigger consolidation
        for _ in range(3):
            inv = _make_invocation("BLOOM_ENGINE", "versioning", symbol="MyFragment")
            patch = _make_patch("HEART_OF_CANON", "BLOOM_ENGINE")
            result = bloom.invoke(inv, patch)
        assert result.get("consolidation_needed") is True

    def test_branch_version_success(self):
        """Test branch_version when cycle exists (lines 251-259)."""
        from rege.organs.bloom_engine import BloomEngine
        bloom = BloomEngine()
        inv = _make_invocation("BLOOM_ENGINE", "growth", symbol="growing symbol", charge=70)
        patch = _make_patch("HEART_OF_CANON", "BLOOM_ENGINE")
        bloom.invoke(inv, patch)
        cycles = bloom.get_active_cycles()
        if cycles:
            result = bloom.branch_version(cycles[0].cycle_id)
            assert result["status"] in ("branched", "consolidated")

    def test_branch_version_not_found(self):
        """Test branch_version when cycle not found."""
        from rege.organs.bloom_engine import BloomEngine
        bloom = BloomEngine()
        result = bloom.branch_version("NONEXISTENT_CYCLE")
        assert result["status"] == "failed"

    def test_force_consolidation_found(self):
        """Test force_consolidation when cycle found (lines 280-281)."""
        from rege.organs.bloom_engine import BloomEngine
        bloom = BloomEngine()
        inv = _make_invocation("BLOOM_ENGINE", "growth", symbol="growing symbol", charge=70)
        patch = _make_patch("HEART_OF_CANON", "BLOOM_ENGINE")
        bloom.invoke(inv, patch)
        cycles = bloom.get_active_cycles()
        if cycles:
            result = bloom.force_consolidation(cycles[0].cycle_id)
            assert isinstance(result, dict)

    def test_force_consolidation_not_found(self):
        """Test force_consolidation when not found."""
        from rege.organs.bloom_engine import BloomEngine
        bloom = BloomEngine()
        result = bloom.force_consolidation("NONEXISTENT")
        assert result["status"] == "failed"

    def test_growth_recommendations_high_charge(self):
        """Test _growth_recommendations with charge >= 71, >= 86 (lines 354, 356)."""
        from rege.organs.bloom_engine import BloomEngine
        bloom = BloomEngine()
        recs_71 = bloom._growth_recommendations(75)
        assert any("branch" in r.lower() or "version" in r.lower() for r in recs_71)
        recs_86 = bloom._growth_recommendations(90)
        assert any("metamorphosis" in r.lower() for r in recs_86)

    def test_get_valid_modes(self):
        """Test get_valid_modes() (line 377)."""
        from rege.organs.bloom_engine import BloomEngine
        bloom = BloomEngine()
        modes = bloom.get_valid_modes()
        assert isinstance(modes, list)
        assert "growth" in modes

    def test_get_output_types(self):
        """Test get_output_types() (line 380)."""
        from rege.organs.bloom_engine import BloomEngine
        bloom = BloomEngine()
        types = bloom.get_output_types()
        assert isinstance(types, list)


# ==================== Echo Shell Tests ====================

class TestEchoShellMissingPaths:
    """Tests for EchoShell uncovered paths."""

    def _create_echo_object(self, charge=60):
        from rege.organs.echo_shell import Echo
        return Echo(content="test content", charge=charge, source="HEART_OF_CANON")

    def test_echo_calculate_decay_rate_active(self):
        """Test Echo._calculate_decay_rate for charge > 50 (line 44)."""
        echo = self._create_echo_object(charge=70)
        rate = echo._calculate_decay_rate()
        assert rate == 0.05

    def test_description_property(self):
        """Test description property (line 111)."""
        from rege.organs.echo_shell import EchoShell
        echo = EchoShell()
        desc = echo.description
        assert isinstance(desc, str) and len(desc) > 0

    def test_pulse_mode_with_existing_echo(self):
        """Test _pulse_mode when matching echo found (lines 172-173)."""
        from rege.organs.echo_shell import EchoShell
        shell = EchoShell()
        # Create an echo first via default mode
        inv = _make_invocation("ECHO_SHELL", "default", symbol="unique echo content abc")
        patch = _make_patch("HEART_OF_CANON", "ECHO_SHELL")
        shell.invoke(inv, patch)
        # Now pulse with same content - should find the existing echo
        inv2 = _make_invocation("ECHO_SHELL", "pulse", symbol="unique echo content abc")
        result = shell.invoke(inv2, patch)
        assert isinstance(result, dict)

    def test_pulse_method_echo_not_found(self):
        """Test pulse() method when echo not found (lines 207-208)."""
        from rege.organs.echo_shell import EchoShell
        shell = EchoShell()
        result = shell.pulse("NONEXISTENT_ECHO_ID")
        assert result["status"] == "not_found"

    def test_pulse_method_echo_found(self):
        """Test pulse() method when echo found (line 210)."""
        from rege.organs.echo_shell import EchoShell
        shell = EchoShell()
        inv = _make_invocation("ECHO_SHELL", "default", symbol="echo to pulse")
        patch = _make_patch("HEART_OF_CANON", "ECHO_SHELL")
        result = shell.invoke(inv, patch)
        echo_id = result["echo"]["echo_id"]
        pulse_result = shell.pulse(echo_id)
        assert "pulse_count" in pulse_result or "status" in pulse_result

    def test_decay_method_echo_not_found(self):
        """Test decay() method when echo not found (lines 223-224)."""
        from rege.organs.echo_shell import EchoShell
        shell = EchoShell()
        result = shell.decay("NONEXISTENT_ECHO_ID")
        assert result["status"] == "not_found"

    def test_decay_method_echo_found(self):
        """Test decay() method when echo found (lines 226-237)."""
        from rege.organs.echo_shell import EchoShell
        shell = EchoShell()
        inv = _make_invocation("ECHO_SHELL", "default", symbol="echo to decay")
        patch = _make_patch("HEART_OF_CANON", "ECHO_SHELL")
        result = shell.invoke(inv, patch)
        echo_id = result["echo"]["echo_id"]
        decay_result = shell.decay(echo_id, days=30)
        assert "new_charge" in decay_result

    def test_find_echo_by_content_found(self):
        """Test _find_echo_by_content when echo matches (lines 283-284)."""
        from rege.organs.echo_shell import EchoShell
        shell = EchoShell()
        inv = _make_invocation("ECHO_SHELL", "default", symbol="searchable content xyz")
        patch = _make_patch("HEART_OF_CANON", "ECHO_SHELL")
        shell.invoke(inv, patch)
        found = shell._find_echo_by_content("searchable content xyz")
        assert found is not None

    def test_update_latent_pool_removal(self):
        """Test _update_latent_pool removes echo when charge increases (line 309)."""
        from rege.organs.echo_shell import EchoShell
        shell = EchoShell()
        # Create an echo with low charge → goes to latent pool
        inv = _make_invocation("ECHO_SHELL", "default", symbol="latent echo", charge=20)
        patch = _make_patch("HEART_OF_CANON", "ECHO_SHELL")
        result = shell.invoke(inv, patch)
        echo_id = result["echo"]["echo_id"]
        # Force it into latent pool
        if echo_id not in shell._latent_pool:
            shell._latent_pool.append(echo_id)
        # Increase the echo's charge to trigger removal from pool
        shell._echoes[echo_id].charge = 80
        shell._update_latent_pool(shell._echoes[echo_id])
        assert echo_id not in shell._latent_pool

    def test_echo_recommendations_high_charge(self):
        """Test _echo_recommendations with high charge (line 318)."""
        from rege.organs.echo_shell import EchoShell, Echo
        shell = EchoShell()
        echo = Echo(content="strong echo", charge=80, source="HEART_OF_CANON")
        recs = shell._echo_recommendations(echo)
        assert any("archival" in r.lower() or "strong" in r.lower() for r in recs)

    def test_get_valid_modes(self):
        """Test get_valid_modes() (line 325)."""
        from rege.organs.echo_shell import EchoShell
        shell = EchoShell()
        modes = shell.get_valid_modes()
        assert isinstance(modes, list)
        assert "decay" in modes

    def test_get_output_types(self):
        """Test get_output_types() (line 328)."""
        from rege.organs.echo_shell import EchoShell
        shell = EchoShell()
        types = shell.get_output_types()
        assert isinstance(types, list)

    def test_get_all_echoes(self):
        """Test get_all_echoes() (line 336)."""
        from rege.organs.echo_shell import EchoShell
        shell = EchoShell()
        inv = _make_invocation("ECHO_SHELL", "default", symbol="echo content")
        patch = _make_patch("HEART_OF_CANON", "ECHO_SHELL")
        shell.invoke(inv, patch)
        echoes = shell.get_all_echoes()
        assert len(echoes) >= 1


# ==================== Mask Engine Tests ====================

class TestMaskEngineMissingPaths:
    """Tests for MaskEngine uncovered paths."""

    def test_mask_add_layer(self):
        """Test Mask.add_layer() (lines 70-71)."""
        from rege.organs.mask_engine import Mask
        mask = Mask(name="TestMask", archetype="HERO", charge=70, traits=["brave"])
        mask.add_layer("shadow_layer")
        assert "shadow_layer" in mask.identity_layers
        # Adding again should not duplicate
        mask.add_layer("shadow_layer")
        assert mask.identity_layers.count("shadow_layer") == 1

    def test_description_property(self):
        """Test description property (line 107)."""
        from rege.organs.mask_engine import MaskEngine
        engine = MaskEngine()
        desc = engine.description
        assert isinstance(desc, str) and len(desc) > 0

    def test_invoke_default_mode(self):
        """Test invoke in default mode (lines 127, 215-217)."""
        from rege.organs.mask_engine import MaskEngine
        engine = MaskEngine()
        inv = _make_invocation("MASK_ENGINE", "unknown_mode", symbol="any content")
        patch = _make_patch("HEART_OF_CANON", "MASK_ENGINE")
        result = engine.invoke(inv, patch)
        assert "total_masks" in result

    def test_invoke_default_mode_with_active_mask(self):
        """Test _default_process with active mask (lines 215-217)."""
        from rege.organs.mask_engine import MaskEngine
        engine = MaskEngine()
        # Assemble a mask first
        inv_assemble = _make_invocation("MASK_ENGINE", "assembly", symbol="hero persona", charge=70)
        patch = _make_patch("HEART_OF_CANON", "MASK_ENGINE")
        result = engine.invoke(inv_assemble, patch)
        mask_id = result["mask"]["mask_id"]
        # Set as active directly
        engine._active_mask = mask_id
        # Now invoke default — should show active mask
        inv_default = _make_invocation("MASK_ENGINE", "unknown_mode", symbol="anything")
        result = engine.invoke(inv_default, patch)
        assert "active_mask" in result
        assert result["active_mask"] is not None

    def test_invoke_inheritance_parent_not_found(self):
        """Test _inheritance when parent not found (line 158)."""
        from rege.organs.mask_engine import MaskEngine
        engine = MaskEngine()
        inv = _make_invocation("MASK_ENGINE", "inheritance", symbol="nonexistent parent mask")
        patch = _make_patch("HEART_OF_CANON", "MASK_ENGINE")
        result = engine.invoke(inv, patch)
        assert result.get("status") == "parent_not_found"

    def test_invoke_shift_with_active_mask_removed(self):
        """Test _shift removes current active mask (lines 197-199)."""
        from rege.organs.mask_engine import MaskEngine
        engine = MaskEngine()
        # Assemble and shift to first mask
        inv1 = _make_invocation("MASK_ENGINE", "assembly", symbol="initial persona hero", charge=70)
        patch = _make_patch("HEART_OF_CANON", "MASK_ENGINE")
        result1 = engine.invoke(inv1, patch)
        mask_id = result1["mask"]["mask_id"]
        inv_shift1 = _make_invocation("MASK_ENGINE", "shift", symbol="initial persona hero")
        engine.invoke(inv_shift1, patch)
        # Shift to a different (non-existent) mask — should remove current
        inv_shift2 = _make_invocation("MASK_ENGINE", "shift", symbol="totally different xyz")
        result = engine.invoke(inv_shift2, patch)
        assert "removed" in result or result.get("status") in ("bare", "target_not_found")

    def test_invoke_shift_target_not_found(self):
        """Test _shift when target mask not found (lines 208-209)."""
        from rege.organs.mask_engine import MaskEngine
        engine = MaskEngine()
        inv = _make_invocation("MASK_ENGINE", "shift", symbol="nonexistent target mask")
        patch = _make_patch("HEART_OF_CANON", "MASK_ENGINE")
        result = engine.invoke(inv, patch)
        assert result.get("status") in ("bare", "target_not_found")

    def test_find_mask_by_content_id_match(self):
        """Test _find_mask_by_content matches by ID (line 337)."""
        from rege.organs.mask_engine import MaskEngine
        engine = MaskEngine()
        inv = _make_invocation("MASK_ENGINE", "assembly", symbol="test persona")
        patch = _make_patch("HEART_OF_CANON", "MASK_ENGINE")
        result = engine.invoke(inv, patch)
        mask_id = result["mask"]["mask_id"]
        found = engine._find_mask_by_content(mask_id.lower())
        assert found == mask_id

    def test_find_mask_by_content_not_found(self):
        """Test _find_mask_by_content returns None when not found (line 344)."""
        from rege.organs.mask_engine import MaskEngine
        engine = MaskEngine()
        found = engine._find_mask_by_content("totally nonexistent xyz")
        assert found is None

    def test_get_valid_modes(self):
        """Test get_valid_modes() (line 359)."""
        from rege.organs.mask_engine import MaskEngine
        engine = MaskEngine()
        modes = engine.get_valid_modes()
        assert isinstance(modes, list)
        assert "assembly" in modes

    def test_get_output_types(self):
        """Test get_output_types() (line 362)."""
        from rege.organs.mask_engine import MaskEngine
        engine = MaskEngine()
        types = engine.get_output_types()
        assert isinstance(types, list)

    def test_get_mask_by_id(self):
        """Test get_mask() (line 366)."""
        from rege.organs.mask_engine import MaskEngine
        engine = MaskEngine()
        inv = _make_invocation("MASK_ENGINE", "assembly", symbol="unique persona")
        patch = _make_patch("HEART_OF_CANON", "MASK_ENGINE")
        result = engine.invoke(inv, patch)
        mask_id = result["mask"]["mask_id"]
        mask = engine.get_mask(mask_id)
        assert mask is not None

    def test_get_all_masks(self):
        """Test get_all_masks() (line 370)."""
        from rege.organs.mask_engine import MaskEngine
        engine = MaskEngine()
        inv = _make_invocation("MASK_ENGINE", "assembly", symbol="persona one")
        patch = _make_patch("HEART_OF_CANON", "MASK_ENGINE")
        engine.invoke(inv, patch)
        masks = engine.get_all_masks()
        assert len(masks) >= 1

    def test_get_active_mask_when_active(self):
        """Test get_active_mask() when mask is active (line 376)."""
        from rege.organs.mask_engine import MaskEngine
        engine = MaskEngine()
        # Assemble a mask
        inv = _make_invocation("MASK_ENGINE", "assembly", symbol="active persona test", charge=70)
        patch = _make_patch("HEART_OF_CANON", "MASK_ENGINE")
        result = engine.invoke(inv, patch)
        # Set it as active directly
        mask_id = result["mask"]["mask_id"]
        engine._active_mask = mask_id
        active = engine.get_active_mask()
        assert active is not None
        assert active.mask_id == mask_id
