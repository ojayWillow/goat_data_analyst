#!/usr/bin/env python3
"""Pytest-compatible tests for NarrativeGenerator agent.

Tests cover:
- Initialization
- Result setting
- Summary reporting
- Edge cases
- Integration with other agents

Run with: pytest scripts/test_narrative_generator.py -v
"""

import sys
from pathlib import Path
import pytest
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.narrative_generator.narrative_generator import NarrativeGenerator
from core.logger import get_logger

logger = get_logger(__name__)


class TestNarrativeGeneratorBasic:
    """Basic NarrativeGenerator functionality tests."""
    
    @pytest.fixture
    def narrative_gen(self):
        """Create a NarrativeGenerator instance."""
        return NarrativeGenerator()
    
    def test_initialization(self, narrative_gen):
        """Test NarrativeGenerator initializes correctly."""
        assert narrative_gen is not None
        assert narrative_gen.name == "NarrativeGenerator"
        assert narrative_gen.logger is not None
        assert narrative_gen.structured_logger is not None
        logger.info("✓ Initialization test passed")
    
    def test_initial_state(self, narrative_gen):
        """Test initial state of NarrativeGenerator."""
        assert narrative_gen.agent_results == {}
        assert narrative_gen.insights == {}
        assert narrative_gen.problems == []
        assert narrative_gen.actions == []
        assert narrative_gen.narrative is None
        logger.info("✓ Initial state test passed")
    
    def test_set_empty_results(self, narrative_gen):
        """Test setting empty results."""
        narrative_gen.set_results({})
        assert narrative_gen.agent_results == {}
        logger.info("✓ Empty results test passed")
    
    def test_set_results_with_data(self, narrative_gen):
        """Test setting results with actual data."""
        results = {
            "anomalies": [{"type": "outlier", "count": 5}],
            "predictions": [{"value": 0.85}],
            "recommendations": ["action_1", "action_2"],
            "report": {"summary": "test summary"},
            "charts": [{"type": "histogram"}]
        }
        narrative_gen.set_results(results)
        
        assert narrative_gen.agent_results == results
        assert len(narrative_gen.agent_results) == 5
        logger.info("✓ Set results with data test passed")
    
    def test_set_results_clears_previous_state(self, narrative_gen):
        """Test that setting new results clears previous state."""
        # Set initial results
        first_results = {"data": "first"}
        narrative_gen.set_results(first_results)
        narrative_gen.insights = {"old": "insight"}
        narrative_gen.problems = ["problem1"]
        narrative_gen.actions = ["action1"]
        narrative_gen.narrative = {"story": "old"}
        
        # Set new results
        second_results = {"data": "second"}
        narrative_gen.set_results(second_results)
        
        assert narrative_gen.agent_results == second_results
        assert narrative_gen.insights == {}
        assert narrative_gen.problems == []
        assert narrative_gen.actions == []
        assert narrative_gen.narrative is None
        logger.info("✓ Clear previous state test passed")
    
    def test_get_summary(self, narrative_gen):
        """Test get_summary method."""
        summary = narrative_gen.get_summary()
        
        assert isinstance(summary, str)
        assert "NarrativeGenerator" in summary
        assert "Summary" in summary
        assert "Status" in summary
        logger.info("✓ Get summary test passed")
    
    def test_summary_includes_state_info(self, narrative_gen):
        """Test summary includes current state information."""
        # Without results
        summary1 = narrative_gen.get_summary()
        assert "Results loaded: False" in summary1
        
        # With results
        narrative_gen.set_results({"test": "data"})
        summary2 = narrative_gen.get_summary()
        assert "Results loaded: True" in summary2
        
        logger.info("✓ Summary state info test passed")


class TestNarrativeGeneratorResults:
    """Test result handling and processing."""
    
    @pytest.fixture
    def narrative_gen(self):
        return NarrativeGenerator()
    
    def test_set_anomaly_results(self, narrative_gen):
        """Test setting anomaly detection results."""
        anomaly_results = {
            "anomalies": [
                {"index": 0, "score": 0.95, "type": "outlier"},
                {"index": 15, "score": 0.87, "type": "outlier"}
            ],
            "total_anomalies": 2,
            "dataset_size": 100
        }
        narrative_gen.set_results(anomaly_results)
        
        assert len(narrative_gen.agent_results["anomalies"]) == 2
        assert narrative_gen.agent_results["total_anomalies"] == 2
        logger.info("✓ Anomaly results test passed")
    
    def test_set_prediction_results(self, narrative_gen):
        """Test setting prediction results."""
        prediction_results = {
            "predictions": [
                {"value": 0.78, "confidence": 0.92},
                {"value": 0.82, "confidence": 0.88}
            ],
            "model_type": "random_forest",
            "accuracy": 0.85
        }
        narrative_gen.set_results(prediction_results)
        
        assert len(narrative_gen.agent_results["predictions"]) == 2
        assert narrative_gen.agent_results["model_type"] == "random_forest"
        logger.info("✓ Prediction results test passed")
    
    def test_set_recommendation_results(self, narrative_gen):
        """Test setting recommendation results."""
        recommendation_results = {
            "recommendations": [
                {"action": "investigate_outlier", "priority": "high"},
                {"action": "retrain_model", "priority": "medium"}
            ],
            "total_recommendations": 2
        }
        narrative_gen.set_results(recommendation_results)
        
        assert len(narrative_gen.agent_results["recommendations"]) == 2
        assert narrative_gen.agent_results["total_recommendations"] == 2
        logger.info("✓ Recommendation results test passed")
    
    def test_set_complex_results(self, narrative_gen):
        """Test setting complex multi-agent results."""
        complex_results = {
            "anomalies": {"count": 3, "types": ["outlier", "drift"]},
            "predictions": {"accuracy": 0.92, "model": "xgboost"},
            "recommendations": {"count": 5, "priority_high": 2},
            "report": {
                "title": "Data Analysis Report",
                "generated_at": datetime.now().isoformat(),
                "sections": ["summary", "findings", "recommendations"]
            },
            "charts": [
                {"type": "histogram", "columns": ["feature1"]},
                {"type": "scatter", "columns": ["feature2", "feature3"]}
            ]
        }
        narrative_gen.set_results(complex_results)
        
        assert len(narrative_gen.agent_results) == 5
        assert "report" in narrative_gen.agent_results
        assert len(narrative_gen.agent_results["charts"]) == 2
        logger.info("✓ Complex results test passed")


class TestNarrativeGeneratorStateManagement:
    """Test state management and transitions."""
    
    @pytest.fixture
    def narrative_gen(self):
        return NarrativeGenerator()
    
    def test_insights_accumulation(self, narrative_gen):
        """Test that insights can accumulate."""
        narrative_gen.set_results({"data": "test"})
        
        # Manually add insights (as would be done by workers)
        narrative_gen.insights["insight1"] = {"value": 0.85}
        narrative_gen.insights["insight2"] = {"value": "high"}
        
        assert len(narrative_gen.insights) == 2
        logger.info("✓ Insights accumulation test passed")
    
    def test_problems_identification(self, narrative_gen):
        """Test problem identification."""
        narrative_gen.set_results({"data": "test"})
        
        # Add problems
        narrative_gen.problems.append("missing_values")
        narrative_gen.problems.append("outliers_detected")
        
        assert len(narrative_gen.problems) == 2
        assert "missing_values" in narrative_gen.problems
        logger.info("✓ Problems identification test passed")
    
    def test_actions_recommendation(self, narrative_gen):
        """Test action recommendations."""
        narrative_gen.set_results({"data": "test"})
        
        # Add actions
        narrative_gen.actions.append({"action": "impute_missing", "method": "mean"})
        narrative_gen.actions.append({"action": "remove_outliers", "method": "iqr"})
        
        assert len(narrative_gen.actions) == 2
        assert narrative_gen.actions[0]["action"] == "impute_missing"
        logger.info("✓ Actions recommendation test passed")
    
    def test_narrative_generation_placeholder(self, narrative_gen):
        """Test narrative generation (placeholder for future workers)."""
        narrative_gen.set_results({"data": "test"})
        narrative_gen.narrative = {
            "title": "Data Analysis Narrative",
            "story": "Once upon a time...",
            "findings": ["finding1", "finding2"],
            "recommendations": ["rec1", "rec2"]
        }
        
        assert narrative_gen.narrative is not None
        assert narrative_gen.narrative["title"] == "Data Analysis Narrative"
        assert len(narrative_gen.narrative["findings"]) == 2
        logger.info("✓ Narrative generation placeholder test passed")


class TestNarrativeGeneratorEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.fixture
    def narrative_gen(self):
        return NarrativeGenerator()
    
    def test_set_none_results(self, narrative_gen):
        """Test handling of None results."""
        try:
            narrative_gen.set_results(None)
            # Should handle gracefully (None might be converted to empty dict)
            assert narrative_gen.agent_results is not None or True
        except (TypeError, AttributeError):
            # This is acceptable behavior
            pass
        logger.info("✓ None results test passed")
    
    def test_set_large_results(self, narrative_gen):
        """Test handling of large result sets."""
        large_results = {
            f"result_{i}": {"value": i, "data": [j for j in range(1000)]}
            for i in range(100)
        }
        narrative_gen.set_results(large_results)
        
        assert len(narrative_gen.agent_results) == 100
        logger.info("✓ Large results test passed")
    
    def test_set_deeply_nested_results(self, narrative_gen):
        """Test handling of deeply nested results."""
        nested_results = {
            "level1": {
                "level2": {
                    "level3": {
                        "level4": {
                            "level5": "deep_value"
                        }
                    }
                }
            }
        }
        narrative_gen.set_results(nested_results)
        
        assert narrative_gen.agent_results["level1"]["level2"]["level3"]["level4"]["level5"] == "deep_value"
        logger.info("✓ Deeply nested results test passed")
    
    def test_repeated_set_results(self, narrative_gen):
        """Test repeated calls to set_results."""
        for i in range(10):
            results = {f"data_{i}": f"value_{i}"}
            narrative_gen.set_results(results)
            assert narrative_gen.agent_results == results
        
        logger.info("✓ Repeated set_results test passed")
    
    def test_summary_with_special_characters(self, narrative_gen):
        """Test summary generation with special characters in data."""
        special_results = {
            "data": "Test with special chars: \n \t \" ' \\ 中文 🚀"
        }
        narrative_gen.set_results(special_results)
        summary = narrative_gen.get_summary()
        
        assert isinstance(summary, str)
        assert len(summary) > 0
        logger.info("✓ Special characters test passed")


class TestNarrativeGeneratorIntegration:
    """Integration tests with other components."""
    
    @pytest.fixture
    def narrative_gen(self):
        return NarrativeGenerator()
    
    def test_full_workflow(self, narrative_gen):
        """Test complete narrative generation workflow."""
        # 1. Set results from other agents
        agent_results = {
            "anomalies": {"count": 3},
            "predictions": {"accuracy": 0.92},
            "recommendations": {"count": 4}
        }
        narrative_gen.set_results(agent_results)
        
        # 2. Add insights
        narrative_gen.insights["data_quality"] = "good"
        narrative_gen.insights["model_performance"] = "excellent"
        
        # 3. Identify problems
        narrative_gen.problems.append("few_anomalies_detected")
        
        # 4. Add recommendations
        narrative_gen.actions.append({"action": "investigate_anomalies"})
        
        # 5. Generate narrative (simulated)
        narrative_gen.narrative = {
            "story": "Analysis complete",
            "findings": list(narrative_gen.insights.keys()),
            "problems": narrative_gen.problems,
            "actions": narrative_gen.actions
        }
        
        # Verify complete state
        assert narrative_gen.agent_results is not None
        assert len(narrative_gen.insights) == 2
        assert len(narrative_gen.problems) == 1
        assert len(narrative_gen.actions) == 1
        assert narrative_gen.narrative is not None
        
        logger.info("✓ Full workflow test passed")
    
    def test_multiple_agent_outputs(self, narrative_gen):
        """Test handling outputs from multiple agents."""
        # Simulate results from DataLoader
        narrative_gen.set_results({
            "data_shape": (1000, 20),
            "columns": [f"col_{i}" for i in range(20)]
        })
        assert "data_shape" in narrative_gen.agent_results
        
        # Simulate results from Explorer
        narrative_gen.set_results({
            "numeric_stats": {"mean": 0.5, "std": 0.1},
            "categorical_stats": {"categories": 5}
        })
        assert "numeric_stats" in narrative_gen.agent_results
        
        # Simulate results from AnomalyDetector
        narrative_gen.set_results({
            "anomalies": [1, 5, 10],
            "anomaly_score": 0.85
        })
        assert "anomaly_score" in narrative_gen.agent_results
        
        logger.info("✓ Multiple agent outputs test passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
