"""Tests for StoryBuilder Worker - Day 4 Implementation.

Tests:
1. Build empathetic problem summary
2. Build business impact explanation (pain points)
3. Build prioritized action plan
4. Build concrete next steps
5. Build improvement outlook
6. Build complete narrative with all sections
7. Handle empty recommendations
8. Executive summary based on severity
9. Narrative formatted for export
10. Multiple recommendations organized
11. Action plan includes time estimates
12. Narrative contains specific details
"""

import pytest
from agents.narrative_generator.workers.story_builder import StoryBuilder


class TestStoryBuilder:
    """Test suite for StoryBuilder worker."""

    @pytest.fixture
    def builder(self):
        """Create StoryBuilder instance."""
        return StoryBuilder()

    @pytest.fixture
    def sample_recommendations(self):
        """Sample recommendations for testing."""
        return [
            {
                'problem_type': 'missing_data',
                'priority': 5,
                'action': 'Implement missing data handling strategy',
                'detail': 'Missing 25% of data. Choose: remove rows, impute, or use advanced methods.',
                'impact': 'Makes data usable for reliable model training',
                'effort': 'high',
                'time_estimate': '1-2 days'
            },
            {
                'problem_type': 'anomalies',
                'priority': 4,
                'action': 'Review and handle significant anomalies',
                'detail': 'Found 15 anomalies. Review each one.',
                'impact': 'Improves model accuracy by ~5-7%',
                'effort': 'medium',
                'time_estimate': '2-4 hours'
            },
            {
                'problem_type': 'low_prediction_confidence',
                'priority': 3,
                'action': 'Fine-tune model hyperparameters',
                'detail': 'Try hyperparameter optimization.',
                'impact': 'Improves confidence by ~5-10%',
                'effort': 'medium',
                'time_estimate': '4-8 hours'
            }
        ]

    # === PROBLEM SUMMARY TESTS ===

    def test_build_problem_summary_with_issues(self, builder, sample_recommendations):
        """Test building empathetic problem summary."""
        summary = builder.build_problem_summary(sample_recommendations)

        assert summary is not None
        assert 'data' in summary.lower()
        assert 'issue' in summary.lower() or 'problem' in summary.lower()
        assert len(summary) > 50  # Substantial summary

    def test_build_problem_summary_no_issues(self, builder):
        """Test problem summary with no issues."""
        summary = builder.build_problem_summary([])

        assert summary is not None
        assert 'good' in summary.lower()
        assert 'no major issues' in summary.lower()

    def test_problem_summary_mentions_impact(self, builder, sample_recommendations):
        """Test that summary mentions business impact."""
        summary = builder.build_problem_summary(sample_recommendations)

        # Should mention consequences
        assert 'bad data' in summary.lower() or 'issues' in summary.lower()

    # === PAIN POINTS TESTS ===

    def test_build_pain_points(self, builder, sample_recommendations):
        """Test building pain points section."""
        pain_points = builder.build_pain_points(sample_recommendations)

        assert pain_points is not None
        assert 'Why This Matters' in pain_points
        assert len(pain_points) > 0

    def test_pain_points_include_impacts(self, builder, sample_recommendations):
        """Test that pain points include specific impacts."""
        pain_points = builder.build_pain_points(sample_recommendations)

        # Should include impact statements
        assert 'impact' in pain_points.lower() or 'improve' in pain_points.lower()

    def test_pain_points_empty_recommendations(self, builder):
        """Test pain points with no recommendations."""
        pain_points = builder.build_pain_points([])

        assert pain_points == ""

    # === ACTION PLAN TESTS ===

    def test_build_action_plan(self, builder, sample_recommendations):
        """Test building prioritized action plan."""
        plan = builder.build_action_plan(sample_recommendations)

        assert plan is not None
        assert 'Path Forward' in plan
        assert 'Critical' in plan  # Priority label
        assert 'High' in plan  # Priority label

    def test_action_plan_includes_time_estimates(self, builder, sample_recommendations):
        """Test that action plan includes time estimates."""
        plan = builder.build_action_plan(sample_recommendations)

        assert 'Time:' in plan
        assert 'hour' in plan.lower() or 'day' in plan.lower()

    def test_action_plan_ordered_by_priority(self, builder, sample_recommendations):
        """Test that actions are ordered by priority."""
        plan = builder.build_action_plan(sample_recommendations)

        # Critical should come before High
        critical_pos = plan.find('Critical')
        high_pos = plan.find('High')
        assert critical_pos < high_pos

    def test_action_plan_no_recommendations(self, builder):
        """Test action plan with no recommendations."""
        plan = builder.build_action_plan([])

        assert 'No actions needed' in plan

    # === NEXT STEPS TESTS ===

    def test_build_next_steps(self, builder, sample_recommendations):
        """Test building concrete next steps."""
        steps = builder.build_next_steps(sample_recommendations)

        assert steps is not None
        assert 'Start Here' in steps
        assert len(steps) > 50

    def test_next_steps_focus_on_critical(self, builder, sample_recommendations):
        """Test that next steps focus on critical action."""
        steps = builder.build_next_steps(sample_recommendations)

        # Should mention the critical/high priority problem
        assert 'missing_data' in steps.lower() or 'data' in steps.lower()

    def test_next_steps_include_detail(self, builder, sample_recommendations):
        """Test that next steps include action details."""
        steps = builder.build_next_steps(sample_recommendations)

        # Should be specific, not generic
        assert len(steps) > 80
        assert 'choose' in steps.lower() or 'remove' in steps.lower() or 'impute' in steps.lower()

    # === IMPROVEMENT OUTLOOK TESTS ===

    def test_build_improvement_outlook(self, builder, sample_recommendations):
        """Test building improvement outlook."""
        outlook = builder.build_improvement_outlook(sample_recommendations)

        assert outlook is not None
        assert 'What Gets Better' in outlook or outlook != ""

    def test_improvement_includes_specific_gains(self, builder, sample_recommendations):
        """Test that improvements are specific, not generic."""
        outlook = builder.build_improvement_outlook(sample_recommendations)

        # Should include percentage improvements or specific gains
        assert '%' in outlook or 'improve' in outlook.lower()

    # === COMPLETE NARRATIVE TESTS ===

    def test_build_complete_narrative(self, builder, sample_recommendations):
        """Test building complete narrative."""
        narrative = builder.build_complete_narrative(sample_recommendations)

        assert narrative is not None
        assert 'executive_summary' in narrative
        assert 'problem_statement' in narrative
        assert 'pain_points' in narrative
        assert 'action_plan' in narrative
        assert 'next_steps' in narrative
        assert 'improvement_outlook' in narrative
        assert 'full_narrative' in narrative

    def test_executive_summary_critical(self, builder, sample_recommendations):
        """Test executive summary indicates critical issues."""
        narrative = builder.build_complete_narrative(sample_recommendations)

        assert 'Critical' in narrative['executive_summary'] or '⚠️' in narrative['executive_summary']

    def test_executive_summary_no_issues(self, builder):
        """Test executive summary when no issues."""
        narrative = builder.build_complete_narrative([])

        assert 'good' in narrative['executive_summary'].lower() or '✅' in narrative['executive_summary']

    def test_narrative_metadata(self, builder, sample_recommendations):
        """Test narrative includes metadata."""
        narrative = builder.build_complete_narrative(sample_recommendations)

        assert 'total_recommendations' in narrative
        assert 'critical_count' in narrative
        assert 'high_count' in narrative
        assert 'medium_count' in narrative
        assert narrative['total_recommendations'] == len(sample_recommendations)

    def test_narrative_is_cohesive(self, builder, sample_recommendations):
        """Test that full narrative reads as coherent story."""
        narrative = builder.build_complete_narrative(sample_recommendations)
        full = narrative['full_narrative']

        # Should have multiple sentences/sections
        assert len(full) > 200
        # Should flow logically
        assert 'problem' in full.lower() or 'issue' in full.lower()

    # === EXPORT TESTS ===

    def test_narrative_for_export(self, builder, sample_recommendations):
        """Test formatting narrative for export."""
        narrative = builder.build_complete_narrative(sample_recommendations)
        export_text = builder.build_narrative_for_export(narrative)

        assert export_text is not None
        assert len(export_text) > 100
        assert 'Report' in export_text or 'Summary' in export_text

    def test_export_is_markdown_formatted(self, builder, sample_recommendations):
        """Test that export uses markdown formatting."""
        narrative = builder.build_complete_narrative(sample_recommendations)
        export_text = builder.build_narrative_for_export(narrative)

        # Should have markdown headers
        assert '#' in export_text

    # === HELPER METHOD TESTS ===

    def test_priority_to_label(self, builder):
        """Test priority to label conversion."""
        assert builder._priority_to_label(5) == "Critical"
        assert builder._priority_to_label(4) == "High"
        assert builder._priority_to_label(3) == "Medium"
        assert builder._priority_to_label(2) == "Low"
        assert builder._priority_to_label(1) == "Monitor"

    # === SPECIFICITY TESTS ===

    def test_narrative_is_specific_not_generic(self, builder, sample_recommendations):
        """Test that narrative includes specific details."""
        narrative = builder.build_complete_narrative(sample_recommendations)
        full = narrative['full_narrative']

        # Should include specific problems and actions
        assert 'missing' in full.lower() or 'anomal' in full.lower()
        assert not full.startswith("Your data has issues")

    def test_action_plan_includes_effort_levels(self, builder, sample_recommendations):
        """Test that action plan specifies effort."""
        plan = builder.build_action_plan(sample_recommendations)

        # Should include effort levels
        assert 'Effort:' in plan
        assert 'High' in plan or 'Medium' in plan or 'Low' in plan

    # === ERROR HANDLING TESTS ===

    def test_handle_malformed_recommendations(self, builder):
        """Test handling recommendations with missing fields."""
        bad_recs = [
            {
                'priority': 5
                # Missing other fields
            }
        ]

        narrative = builder.build_complete_narrative(bad_recs)
        assert narrative is not None
        assert 'executive_summary' in narrative

    def test_build_narrative_graceful_degradation(self, builder):
        """Test that narrative still works with partial data."""
        partial_recs = [
            {
                'problem_type': 'test',
                'priority': 5,
                'action': 'Test action'
                # Missing detail, impact, effort, time_estimate
            }
        ]

        narrative = builder.build_complete_narrative(partial_recs)
        assert narrative is not None
        assert len(narrative['full_narrative']) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
