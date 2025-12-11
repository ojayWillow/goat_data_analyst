"""Test Contract Compliance Fixes

Verifies that critical contract mismatches are fixed.
"""

import pytest
from agents.narrative_generator.narrative_generator import NarrativeGenerator
from core.agent_interface import AgentInterface


class TestContractFixes:
    """Test critical contract fixes."""

    def test_narrative_generator_has_required_methods(self):
        """Verify NarrativeGenerator has all required methods."""
        ng = NarrativeGenerator()
        
        # CRITICAL: These methods were missing
        assert hasattr(ng, 'generate_narrative_from_results'), "Missing generate_narrative_from_results"
        assert hasattr(ng, 'generate_narrative_from_workflow'), "Missing generate_narrative_from_workflow"
        
        # Standard methods
        assert hasattr(ng, 'set_results')
        assert hasattr(ng, 'get_summary')
        
        print("✅ NarrativeGenerator has all required methods")

    def test_narrative_generator_implements_interface(self):
        """Verify NarrativeGenerator implements AgentInterface."""
        ng = NarrativeGenerator()
        assert isinstance(ng, AgentInterface), "NarrativeGenerator must implement AgentInterface"
        print("✅ NarrativeGenerator implements AgentInterface")

    def test_generate_narrative_from_results_returns_dict(self):
        """Verify generate_narrative_from_results returns standardized Dict."""
        ng = NarrativeGenerator()
        
        test_results = {
            'anomalies': [1, 2, 3],
            'summary': 'Test summary'
        }
        
        response = ng.generate_narrative_from_results(test_results)
        
        # Check standardized format
        assert isinstance(response, dict), "Must return dict"
        assert 'status' in response, "Must have 'status' field"
        assert 'data' in response, "Must have 'data' field"
        assert 'message' in response, "Must have 'message' field"
        assert response['status'] in ['success', 'error', 'partial'], "Status must be valid"
        
        print(f"✅ Response has standardized format: {response['status']}")

    def test_generate_narrative_from_workflow_returns_dict(self):
        """Verify generate_narrative_from_workflow returns standardized Dict."""
        ng = NarrativeGenerator()
        
        test_workflow = {
            'tasks': [{'type': 'load', 'status': 'completed'}],
            'results': {'data': 'test'}
        }
        
        response = ng.generate_narrative_from_workflow(test_workflow)
        
        # Check standardized format
        assert isinstance(response, dict), "Must return dict"
        assert 'status' in response, "Must have 'status' field"
        assert response['status'] in ['success', 'error', 'partial'], "Status must be valid"
        
        print(f"✅ Workflow response has standardized format: {response['status']}")

    def test_agent_interface_response_methods(self):
        """Verify AgentInterface response methods work."""
        # Test success_response
        success = AgentInterface.success_response(
            data={'key': 'value'},
            message="Test success"
        )
        assert success['status'] == 'success'
        assert success['data'] == {'key': 'value'}
        
        # Test error_response
        error = AgentInterface.error_response(
            message="Test error",
            error_type="test_error"
        )
        assert error['status'] == 'error'
        assert error['data'] is None
        
        print("✅ AgentInterface response methods work correctly")

    def test_orchestrator_can_call_narrative_methods(self):
        """Verify Orchestrator can successfully call NarrativeGenerator methods."""
        from agents.orchestrator.orchestrator import Orchestrator
        
        orch = Orchestrator()
        ng = NarrativeGenerator()
        
        # Simulate workflow results
        workflow_results = {
            'tasks': [{'type': 'load', 'status': 'completed'}],
            'results': {'anomalies': [], 'summary': 'Test'}
        }
        
        # This should NOT crash anymore
        try:
            result = ng.generate_narrative_from_workflow(workflow_results)
            assert result['status'] in ['success', 'error'], "Should return valid response"
            print("✅ Orchestrator can call generate_narrative_from_workflow()")
        except AttributeError as e:
            pytest.fail(f"Method missing: {e}")

    def test_narrative_generator_data_flow(self):
        """Verify complete data flow in NarrativeGenerator."""
        ng = NarrativeGenerator()
        
        # Step 1: Set results
        results = {
            'anomalies': [{'id': 1, 'value': 'high'}],
            'predictions': [{'next': 100}],
            'summary': 'Test analysis'
        }
        ng.set_results(results)
        
        # Step 2: Generate narrative
        response = ng.generate_narrative_from_results(results)
        
        # Step 3: Verify output
        assert response['status'] == 'success'
        assert 'full_narrative' in response['data']
        assert 'sections' in response['data']
        assert len(response['data']['sections']) > 0
        
        print("✅ Complete data flow works correctly")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("CONTRACT COMPLIANCE TEST SUITE")
    print("="*70 + "\n")
    pytest.main([__file__, "-v", "-s"])
