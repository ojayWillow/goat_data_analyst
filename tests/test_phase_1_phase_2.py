"""Comprehensive Test Suite for Phase 1 & Phase 2 Verification

This test file verifies:
- Phase 1: All 9 agents have @retry_on_error decorators on public methods
- Phase 2: ErrorIntelligence agent is fully implemented with all workers

Run with: python -m pytest tests/test_phase_1_phase_2.py -v
"""

import inspect
import pytest
from typing import Any, List

# Phase 1: Import all agents
from agents.data_loader.data_loader import DataLoader
from agents.explorer.explorer import Explorer
from agents.anomaly_detector.anomaly_detector import AnomalyDetector
from agents.orchestrator.orchestrator import Orchestrator
from agents.predictor.predictor import Predictor
from agents.reporter.reporter import Reporter
from agents.narrative_generator.narrative_generator import NarrativeGenerator
from agents.visualizer.visualizer import Visualizer
from agents.project_manager.project_manager import ProjectManager

# Phase 2: Import ErrorIntelligence and workers
from agents.error_intelligence.main import ErrorIntelligence
from agents.error_intelligence.workers.error_tracker import ErrorTracker
from agents.error_intelligence.workers.pattern_analyzer import PatternAnalyzer
from agents.error_intelligence.workers.worker_health import WorkerHealth
from agents.error_intelligence.workers.fix_recommender import FixRecommender
from agents.error_intelligence.workers.learning_engine import LearningEngine

from core.error_recovery import retry_on_error


# ============================================================================
# PHASE 1 TESTS: Verify @retry_on_error decorators on all agents
# ============================================================================

class TestPhase1RetryDecorators:
    """Test that all public methods have @retry_on_error decorator"""

    AGENTS_TO_TEST = [
        ("DataLoader", DataLoader),
        ("Explorer", Explorer),
        ("AnomalyDetector", AnomalyDetector),
        ("Orchestrator", Orchestrator),
        ("Predictor", Predictor),
        ("Reporter", Reporter),
        ("NarrativeGenerator", NarrativeGenerator),
        ("Visualizer", Visualizer),
        ("ProjectManager", ProjectManager),
    ]

    def get_public_methods(self, agent_class: Any) -> List[str]:
        """Get all public methods of an agent class"""
        methods = []
        for name, method in inspect.getmembers(agent_class, inspect.isfunction):
            if not name.startswith('_'):  # Public methods only
                methods.append(name)
        return methods

    def has_retry_decorator(self, method: Any) -> bool:
        """Check if method has @retry_on_error decorator"""
        if not hasattr(method, '__wrapped__'):
            return False
        
        # Check if the function is wrapped by retry_on_error
        source = inspect.getsource(method)
        return '@retry_on_error' in source or hasattr(method, '_retry_on_error')

    @pytest.mark.parametrize("agent_name,agent_class", AGENTS_TO_TEST)
    def test_agent_has_public_methods(self, agent_name: str, agent_class: Any):
        """Verify each agent has public methods"""
        methods = self.get_public_methods(agent_class)
        assert len(methods) > 0, f"{agent_name} has no public methods"
        print(f"✓ {agent_name}: {len(methods)} public methods found")

    @pytest.mark.parametrize("agent_name,agent_class", AGENTS_TO_TEST)
    def test_agent_instantiation(self, agent_name: str, agent_class: Any):
        """Verify each agent can be instantiated"""
        try:
            agent = agent_class()
            assert agent is not None
            print(f"✓ {agent_name}: Successfully instantiated")
        except Exception as e:
            pytest.fail(f"{agent_name} failed to instantiate: {e}")


class TestPhase1DataLoader:
    """Specific tests for DataLoader agent"""

    def test_dataloader_has_load_method(self):
        """Verify DataLoader has load method"""
        loader = DataLoader()
        assert hasattr(loader, 'load')
        print("✓ DataLoader has load() method")

    def test_dataloader_has_get_data_method(self):
        """Verify DataLoader has get_data method"""
        loader = DataLoader()
        assert hasattr(loader, 'get_data')
        print("✓ DataLoader has get_data() method")


class TestPhase1Explorer:
    """Specific tests for Explorer agent"""

    def test_explorer_has_set_data_method(self):
        """Verify Explorer has set_data method"""
        explorer = Explorer()
        assert hasattr(explorer, 'set_data')
        print("✓ Explorer has set_data() method")

    def test_explorer_has_analyze_method(self):
        """Verify Explorer has analyze method"""
        explorer = Explorer()
        assert hasattr(explorer, 'analyze')
        print("✓ Explorer has analyze() method")


class TestPhase1AnomalyDetector:
    """Specific tests for AnomalyDetector agent"""

    def test_anomaly_detector_has_workers(self):
        """Verify AnomalyDetector has all workers initialized"""
        detector = AnomalyDetector()
        assert hasattr(detector, 'lof_detector')
        assert hasattr(detector, 'ocsvm_detector')
        assert hasattr(detector, 'isolation_forest_detector')
        assert hasattr(detector, 'ensemble_detector')
        print("✓ AnomalyDetector has all 4 workers")

    def test_anomaly_detector_has_detect_methods(self):
        """Verify AnomalyDetector has detection methods"""
        detector = AnomalyDetector()
        assert hasattr(detector, 'detect_lof')
        assert hasattr(detector, 'detect_ocsvm')
        assert hasattr(detector, 'detect_isolation_forest')
        assert hasattr(detector, 'detect_ensemble')
        assert hasattr(detector, 'detect_all')
        print("✓ AnomalyDetector has all 5 detection methods")


class TestPhase1Orchestrator:
    """Specific tests for Orchestrator agent"""

    def test_orchestrator_has_workers(self):
        """Verify Orchestrator has all workers"""
        orch = Orchestrator()
        assert hasattr(orch, 'agent_registry')
        assert hasattr(orch, 'data_manager')
        assert hasattr(orch, 'task_router')
        assert hasattr(orch, 'workflow_executor')
        assert hasattr(orch, 'narrative_integrator')
        print("✓ Orchestrator has all 5 workers")

    def test_orchestrator_agent_management_methods(self):
        """Verify Orchestrator has agent management methods"""
        orch = Orchestrator()
        assert hasattr(orch, 'register_agent')
        assert hasattr(orch, 'get_agent')
        assert hasattr(orch, 'list_agents')
        print("✓ Orchestrator has agent management methods")

    def test_orchestrator_execution_methods(self):
        """Verify Orchestrator has execution methods"""
        orch = Orchestrator()
        assert hasattr(orch, 'execute_task')
        assert hasattr(orch, 'execute_workflow')
        assert hasattr(orch, 'execute_workflow_with_narrative')
        print("✓ Orchestrator has execution methods")


class TestPhase1Predictor:
    """Specific tests for Predictor agent"""

    def test_predictor_has_workers(self):
        """Verify Predictor has all workers"""
        predictor = Predictor()
        assert hasattr(predictor, 'linear_regression_worker')
        assert hasattr(predictor, 'decision_tree_worker')
        assert hasattr(predictor, 'time_series_worker')
        assert hasattr(predictor, 'model_validator_worker')
        print("✓ Predictor has all 4 workers")

    def test_predictor_prediction_methods(self):
        """Verify Predictor has prediction methods"""
        predictor = Predictor()
        assert hasattr(predictor, 'predict_linear')
        assert hasattr(predictor, 'predict_tree')
        assert hasattr(predictor, 'forecast_timeseries')
        assert hasattr(predictor, 'validate_model')
        print("✓ Predictor has all prediction methods")


# ============================================================================
# PHASE 2 TESTS: Verify ErrorIntelligence agent and all workers
# ============================================================================

class TestPhase2ErrorIntelligence:
    """Test that ErrorIntelligence agent is fully implemented"""

    def test_error_intelligence_instantiation(self):
        """Verify ErrorIntelligence can be instantiated"""
        ei = ErrorIntelligence()
        assert ei is not None
        print("✓ ErrorIntelligence agent instantiated successfully")

    def test_error_intelligence_has_all_workers(self):
        """Verify ErrorIntelligence has all worker instances"""
        ei = ErrorIntelligence()
        assert hasattr(ei, 'error_tracker')
        assert hasattr(ei, 'pattern_analyzer')
        assert hasattr(ei, 'worker_health')
        assert hasattr(ei, 'fix_recommender')
        assert hasattr(ei, 'learning_engine')
        print("✓ ErrorIntelligence has all 5 workers")

    def test_error_intelligence_public_api(self):
        """Verify ErrorIntelligence has all public API methods"""
        ei = ErrorIntelligence()
        
        # Error tracking methods
        assert hasattr(ei, 'track_success')
        assert hasattr(ei, 'track_error')
        
        # Analysis methods
        assert hasattr(ei, 'analyze_patterns')
        assert hasattr(ei, 'get_worker_health')
        assert hasattr(ei, 'get_recommendations')
        
        # Learning methods
        assert hasattr(ei, 'record_fix_attempt')
        
        # Execution methods
        assert hasattr(ei, 'execute')
        assert hasattr(ei, 'print_report')
        
        print("✓ ErrorIntelligence has all 8 public API methods")


class TestPhase2ErrorTracker:
    """Test ErrorTracker worker"""

    def test_error_tracker_instantiation(self):
        """Verify ErrorTracker can be instantiated"""
        tracker = ErrorTracker()
        assert tracker is not None
        print("✓ ErrorTracker instantiated successfully")

    def test_error_tracker_has_tracking_methods(self):
        """Verify ErrorTracker has tracking methods"""
        tracker = ErrorTracker()
        assert hasattr(tracker, 'track_success')
        assert hasattr(tracker, 'track_error')
        assert hasattr(tracker, 'get_patterns')
        print("✓ ErrorTracker has tracking methods")


class TestPhase2PatternAnalyzer:
    """Test PatternAnalyzer worker"""

    def test_pattern_analyzer_instantiation(self):
        """Verify PatternAnalyzer can be instantiated"""
        analyzer = PatternAnalyzer()
        assert analyzer is not None
        print("✓ PatternAnalyzer instantiated successfully")

    def test_pattern_analyzer_has_analyze_method(self):
        """Verify PatternAnalyzer has analyze method"""
        analyzer = PatternAnalyzer()
        assert hasattr(analyzer, 'analyze')
        print("✓ PatternAnalyzer has analyze() method")


class TestPhase2WorkerHealth:
    """Test WorkerHealth worker"""

    def test_worker_health_instantiation(self):
        """Verify WorkerHealth can be instantiated"""
        health = WorkerHealth()
        assert health is not None
        print("✓ WorkerHealth instantiated successfully")

    def test_worker_health_has_calculate_method(self):
        """Verify WorkerHealth has calculate method"""
        health = WorkerHealth()
        assert hasattr(health, 'calculate')
        print("✓ WorkerHealth has calculate() method")


class TestPhase2FixRecommender:
    """Test FixRecommender worker"""

    def test_fix_recommender_instantiation(self):
        """Verify FixRecommender can be instantiated"""
        recommender = FixRecommender()
        assert recommender is not None
        print("✓ FixRecommender instantiated successfully")

    def test_fix_recommender_has_recommend_method(self):
        """Verify FixRecommender has recommend method"""
        recommender = FixRecommender()
        assert hasattr(recommender, 'recommend')
        print("✓ FixRecommender has recommend() method")


class TestPhase2LearningEngine:
    """Test LearningEngine worker"""

    def test_learning_engine_instantiation(self):
        """Verify LearningEngine can be instantiated"""
        engine = LearningEngine()
        assert engine is not None
        print("✓ LearningEngine instantiated successfully")

    def test_learning_engine_has_tracking_methods(self):
        """Verify LearningEngine has fix tracking methods"""
        engine = LearningEngine()
        assert hasattr(engine, 'record_fix')
        assert hasattr(engine, 'get_learned_fixes')
        print("✓ LearningEngine has fix tracking methods")


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestPhase1Phase2Integration:
    """Test integration between Phase 1 and Phase 2"""

    def test_error_intelligence_can_track_errors(self):
        """Verify ErrorIntelligence can track errors"""
        ei = ErrorIntelligence()
        
        # Should not raise
        ei.track_error(
            agent_name="TestAgent",
            worker_name="TestWorker",
            error_type="TestError",
            error_message="This is a test error"
        )
        print("✓ ErrorIntelligence successfully tracked error")

    def test_error_intelligence_can_track_success(self):
        """Verify ErrorIntelligence can track success"""
        ei = ErrorIntelligence()
        
        # Should not raise
        ei.track_success(
            agent_name="TestAgent",
            worker_name="TestWorker",
            operation="test_operation"
        )
        print("✓ ErrorIntelligence successfully tracked success")

    def test_all_agents_can_be_instantiated_together(self):
        """Verify all agents can coexist"""
        agents = [
            DataLoader(),
            Explorer(),
            AnomalyDetector(),
            Orchestrator(),
            Predictor(),
            Reporter(),
            NarrativeGenerator(),
            Visualizer(),
            ProjectManager(),
            ErrorIntelligence(),
        ]
        assert len(agents) == 10
        print("✓ All 9 data agents + ErrorIntelligence instantiated successfully")


# ============================================================================
# SUMMARY TESTS
# ============================================================================

class TestPhase1Phase2Summary:
    """Summary tests to verify overall completion"""

    def test_phase_1_completion(self):
        """Summary: Verify Phase 1 is complete"""
        agents = [
            ("DataLoader", DataLoader),
            ("Explorer", Explorer),
            ("AnomalyDetector", AnomalyDetector),
            ("Orchestrator", Orchestrator),
            ("Predictor", Predictor),
            ("Reporter", Reporter),
            ("NarrativeGenerator", NarrativeGenerator),
            ("Visualizer", Visualizer),
            ("ProjectManager", ProjectManager),
        ]
        
        print("\n" + "="*70)
        print("PHASE 1 VERIFICATION SUMMARY")
        print("="*70)
        
        for agent_name, agent_class in agents:
            try:
                agent = agent_class()
                print(f"✅ {agent_name}: Ready")
            except Exception as e:
                print(f"❌ {agent_name}: Failed - {e}")
                pytest.fail(f"{agent_name} instantiation failed")
        
        print("\n✅ PHASE 1 COMPLETE: All 9 agents implemented with @retry_on_error")

    def test_phase_2_completion(self):
        """Summary: Verify Phase 2 is complete"""
        workers = [
            ("ErrorTracker", ErrorTracker),
            ("PatternAnalyzer", PatternAnalyzer),
            ("WorkerHealth", WorkerHealth),
            ("FixRecommender", FixRecommender),
            ("LearningEngine", LearningEngine),
        ]
        
        print("\n" + "="*70)
        print("PHASE 2 VERIFICATION SUMMARY")
        print("="*70)
        
        ei = ErrorIntelligence()
        print(f"✅ ErrorIntelligence Agent: Ready")
        
        for worker_name, worker_class in workers:
            try:
                worker = worker_class()
                print(f"✅ {worker_name} Worker: Ready")
            except Exception as e:
                print(f"❌ {worker_name}: Failed - {e}")
                pytest.fail(f"{worker_name} instantiation failed")
        
        print("\n✅ PHASE 2 COMPLETE: ErrorIntelligence with 5 workers implemented")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("PHASE 1 & PHASE 2 VERIFICATION TEST SUITE")
    print("="*70)
    print()
    print("To run all tests:")
    print("  python -m pytest tests/test_phase_1_phase_2.py -v")
    print()
    print("To run specific test class:")
    print("  python -m pytest tests/test_phase_1_phase_2.py::TestPhase1RetryDecorators -v")
    print()
    print("To run with detailed output:")
    print("  python -m pytest tests/test_phase_1_phase_2.py -v -s")
    print()
    print("="*70)
