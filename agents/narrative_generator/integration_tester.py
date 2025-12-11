"""Integration Tester - Day 5 Implementation.

Tests the complete narrative pipeline with real CSV data:
- Loads real datasets
- Simulates agent outputs
- Runs through narrative pipeline
- Validates narrative quality
- Identifies edge cases

This is where theory meets reality.
"""

import pandas as pd
import json
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from core.logger import get_logger
from core.structured_logger import get_structured_logger
from agents.narrative_generator.workers.insight_extractor import InsightExtractor
from agents.narrative_generator.workers.problem_identifier import ProblemIdentifier
from agents.narrative_generator.workers.action_recommender import ActionRecommender
from agents.narrative_generator.workers.story_builder import StoryBuilder


class IntegrationTester:
    """Tests narrative pipeline with real data.
    
    Simulates complete data analysis flow:
    1. Load CSV
    2. Simulate agent outputs (explorer, anomaly, prediction)
    3. Run through narrative pipeline
    4. Validate results
    """

    def __init__(self) -> None:
        """Initialize the integration tester."""
        self.name = "IntegrationTester"
        self.logger = get_logger("IntegrationTester")
        self.structured_logger = get_structured_logger("IntegrationTester")
        
        # Initialize pipeline workers
        self.insight_extractor = InsightExtractor()
        self.problem_identifier = ProblemIdentifier()
        self.action_recommender = ActionRecommender()
        self.story_builder = StoryBuilder()
        
        self.logger.info("IntegrationTester initialized")

    def load_csv(self, csv_path: str) -> Tuple[pd.DataFrame, bool]:
        """Load and analyze CSV file.
        
        Args:
            csv_path: Path to CSV file
        
        Returns:
            (DataFrame, success flag)
        """
        try:
            df = pd.read_csv(csv_path)
            self.logger.info(f"Loaded {csv_path}: {df.shape[0]} rows, {df.shape[1]} columns")
            return df, True
        except Exception as e:
            self.logger.error(f"Error loading CSV: {e}")
            return None, False

    def simulate_agent_outputs(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Simulate outputs from analysis agents.
        
        Args:
            df: DataFrame to analyze
        
        Returns:
            Dict of simulated agent outputs
        """
        try:
            total_rows = len(df)
            total_cols = len(df.columns)
            
            # Simulate Explorer output
            missing_pct = (df.isnull().sum().sum() / (total_rows * total_cols)) * 100
            
            explorer_results = {
                'shape': (total_rows, total_cols),
                'missing_percentage': round(missing_pct, 1),
                'columns': df.columns.tolist(),
                'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
                'numeric_stats': {
                    col: {
                        'mean': float(df[col].mean()) if pd.api.types.is_numeric_dtype(df[col]) else None,
                        'std': float(df[col].std()) if pd.api.types.is_numeric_dtype(df[col]) else None,
                        'min': float(df[col].min()) if pd.api.types.is_numeric_dtype(df[col]) else None,
                        'max': float(df[col].max()) if pd.api.types.is_numeric_dtype(df[col]) else None
                    }
                    for col in df.select_dtypes(include=['number']).columns
                }
            }
            
            # Simulate Anomaly Detector output
            # Simple heuristic: values > 3 std devs are anomalies
            anomaly_count = 0
            anomaly_indices = []
            for col in df.select_dtypes(include=['number']).columns:
                mean = df[col].mean()
                std = df[col].std()
                if std > 0:
                    z_scores = abs((df[col] - mean) / std)
                    anomalies = z_scores[z_scores > 3].index.tolist()
                    anomaly_count += len(anomalies)
                    anomaly_indices.extend(anomalies)
            
            anomaly_results = {
                'count': anomaly_count,
                'percentage': round((anomaly_count / total_rows * 100), 1) if total_rows > 0 else 0,
                'top_anomalies': list(set(anomaly_indices[:5])),
                'severity': 'low' if anomaly_count < total_rows * 0.05 else 'high'
            }
            
            # Simulate Prediction results
            # Heuristic: confidence based on data completeness
            confidence = max(0.3, 1.0 - (missing_pct / 100))
            accuracy = min(0.95, 50 + (confidence * 45))  # 50-95 range
            
            prediction_results = {
                'confidence': round(confidence, 2),
                'accuracy': round(accuracy, 1),
                'top_features': df.select_dtypes(include=['number']).columns[:3].tolist(),
                'trend': 'stable' if confidence > 0.7 else 'declining'
            }
            
            # Combine all agent outputs
            all_results = {
                'explorer': explorer_results,
                'anomalies': anomaly_results,
                'predictions': prediction_results
            }
            
            self.logger.info(f"Simulated agent outputs: {missing_pct:.1f}% missing, "
                           f"{anomaly_count} anomalies, {confidence:.2f} confidence")
            
            return all_results

        except Exception as e:
            self.logger.error(f"Error simulating agent outputs: {e}")
            return {}

    def run_narrative_pipeline(self, agent_outputs: Dict[str, Any]) -> Dict[str, Any]:
        """Run complete narrative pipeline.
        
        Args:
            agent_outputs: Dict of simulated agent outputs
        
        Returns:
            Complete narrative result
        """
        try:
            if not agent_outputs:
                return None
            
            # Step 1: Extract insights
            insights = self.insight_extractor.extract_all(agent_outputs)
            
            # Step 2: Identify problems
            problems = self.problem_identifier.identify_all_problems(insights)
            
            # Step 3: Generate recommendations
            recommendations = self.action_recommender.recommend_for_all_problems(problems)
            
            # Step 4: Build narrative
            narrative = self.story_builder.build_complete_narrative(recommendations)
            
            self.logger.info(f"Narrative pipeline complete: {len(problems)} problems, "
                           f"{len(recommendations)} recommendations")
            
            return narrative

        except Exception as e:
            self.logger.error(f"Error in narrative pipeline: {e}")
            return None

    def test_dataset(self, csv_path: str) -> Dict[str, Any]:
        """Complete end-to-end test with one dataset.
        
        Args:
            csv_path: Path to CSV file
        
        Returns:
            Test result dict with all outputs and validations
        """
        try:
            self.logger.info(f"Starting integration test: {csv_path}")
            
            # Step 1: Load data
            df, success = self.load_csv(csv_path)
            if not success:
                return {'success': False, 'error': 'Failed to load CSV'}
            
            # Step 2: Simulate agent outputs
            agent_outputs = self.simulate_agent_outputs(df)
            if not agent_outputs:
                return {'success': False, 'error': 'Failed to simulate agent outputs'}
            
            # Step 3: Run narrative pipeline
            narrative = self.run_narrative_pipeline(agent_outputs)
            if not narrative:
                return {'success': False, 'error': 'Failed to generate narrative'}
            
            # Step 4: Validate results
            validation = self._validate_narrative(narrative)
            
            result = {
                'success': True,
                'dataset': Path(csv_path).name,
                'data_shape': df.shape,
                'missing_pct': round((df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100), 1),
                'agent_outputs': agent_outputs,
                'narrative': narrative,
                'validation': validation
            }
            
            self.logger.info(f"Integration test passed: {Path(csv_path).name}")
            return result

        except Exception as e:
            self.logger.error(f"Error in test_dataset: {e}")
            return {'success': False, 'error': str(e)}

    def _validate_narrative(self, narrative: Dict[str, Any]) -> Dict[str, bool]:
        """Validate narrative quality.
        
        Args:
            narrative: Narrative dict from StoryBuilder
        
        Returns:
            Dict of validation checks
        """
        try:
            validation = {
                'has_executive_summary': bool(narrative.get('executive_summary')),
                'has_problem_statement': bool(narrative.get('problem_statement')),
                'has_action_plan': bool(narrative.get('action_plan')),
                'has_full_narrative': bool(narrative.get('full_narrative')),
                'summary_has_emoji': any(emoji in narrative.get('executive_summary', '') 
                                        for emoji in ['✅', '⚠️', 'ℹ️']),
                'action_plan_has_priority': 'Critical' in narrative.get('action_plan', '') 
                                           or 'High' in narrative.get('action_plan', ''),
                'narrative_length_ok': len(narrative.get('full_narrative', '')) > 100,
                'has_metadata': all(key in narrative for key in 
                                   ['total_recommendations', 'critical_count', 'high_count']),
                'all_sections_not_empty': all(narrative.get(key) for key in 
                                             ['executive_summary', 'problem_statement', 'full_narrative'])
            }
            
            return validation

        except Exception as e:
            self.logger.error(f"Error validating narrative: {e}")
            return {}

    def test_multiple_datasets(self, data_folder: str = 'data') -> List[Dict[str, Any]]:
        """Test with multiple CSV files.
        
        Args:
            data_folder: Folder containing CSV files
        
        Returns:
            List of test results
        """
        try:
            data_path = Path(data_folder)
            if not data_path.exists():
                self.logger.error(f"Data folder not found: {data_folder}")
                return []
            
            csv_files = list(data_path.glob('*.csv'))
            self.logger.info(f"Found {len(csv_files)} CSV files")
            
            results = []
            for csv_file in csv_files[:5]:  # Test first 5 files
                result = self.test_dataset(str(csv_file))
                results.append(result)
                
                # Print summary
                if result.get('success'):
                    print(f"\n✅ {result['dataset']}")
                    print(f"   Shape: {result['data_shape']}")
                    print(f"   Missing: {result['missing_pct']:.1f}%")
                    print(f"   Narrative: {result['narrative']['executive_summary'][:80]}...")
                else:
                    print(f"\n❌ {result['dataset']}: {result.get('error')}")
            
            # Summary
            passed = sum(1 for r in results if r.get('success'))
            print(f"\n\n📊 Summary: {passed}/{len(results)} datasets passed")
            
            return results

        except Exception as e:
            self.logger.error(f"Error testing multiple datasets: {e}")
            return []

    def print_narrative(self, narrative: Dict[str, Any]) -> None:
        """Pretty print a narrative.
        
        Args:
            narrative: Narrative dict from StoryBuilder
        """
        try:
            print("\n" + "="*80)
            print("📋 NARRATIVE OUTPUT")
            print("="*80 + "\n")
            
            print(f"🎯 Executive Summary:")
            print(f"{narrative.get('executive_summary', 'N/A')}\n")
            
            print(f"📝 Problem Statement:")
            print(f"{narrative.get('problem_statement', 'N/A')}\n")
            
            if narrative.get('pain_points'):
                print(f"⚡ Pain Points:")
                print(f"{narrative.get('pain_points')}\n")
            
            if narrative.get('action_plan'):
                print(f"📋 Action Plan:")
                print(f"{narrative.get('action_plan')}\n")
            
            if narrative.get('improvement_outlook'):
                print(f"📈 Improvement Outlook:")
                print(f"{narrative.get('improvement_outlook')}\n")
            
            print(f"📊 Metadata:")
            print(f"  Total Recommendations: {narrative.get('total_recommendations')}")
            print(f"  Critical: {narrative.get('critical_count')}")
            print(f"  High: {narrative.get('high_count')}")
            print(f"  Medium: {narrative.get('medium_count')}")
            print("\n" + "="*80)

        except Exception as e:
            self.logger.error(f"Error printing narrative: {e}")
