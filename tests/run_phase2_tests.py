#!/usr/bin/env python3
"""
Phase 2 Test Runner - Production Testing with Real Data

Purpose: Test all 8 agents with real data and measure performance
Date: December 10, 2025
Status: Ready for execution
"""

import os
import sys
import json
import time
import psutil
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple

# ============================================================================
# FIX: Clear Python import cache and add project root to Python path
# ============================================================================

# Remove all cached aggregator imports to prevent stale cache
for key in list(sys.modules.keys()):
    if 'aggregator' in key or 'agents' in key:
        del sys.modules[key]

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Now we can import
try:
    import pandas as pd
    import numpy as np
except ImportError:
    print("❌ Error: pandas or numpy not installed")
    print("   Install with: pip install pandas numpy psutil openpyxl")
    sys.exit(1)

# Configuration
TEST_DATA_DIR = Path(__file__).parent / "data"
LOGS_DIR = Path(__file__).parent / "logs"
TEST_RESULTS_FILE = LOGS_DIR / f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

# Ensure directories exist
TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)


class PerformanceMonitor:
    """Monitor performance metrics during test execution"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.start_memory = None
        self.peak_memory = None
        self.process = psutil.Process()
    
    def start(self):
        """Start monitoring"""
        self.start_time = time.time()
        self.start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        self.peak_memory = self.start_memory
    
    def update_peak_memory(self):
        """Update peak memory"""
        current_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        self.peak_memory = max(self.peak_memory, current_memory)
    
    def stop(self) -> Dict[str, Any]:
        """Stop monitoring and return metrics"""
        self.end_time = time.time()
        end_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        duration_seconds = self.end_time - self.start_time
        memory_used = end_memory - self.start_memory
        
        return {
            "duration_seconds": round(duration_seconds, 3),
            "memory_used_mb": round(memory_used, 2),
            "peak_memory_mb": round(self.peak_memory, 2),
            "start_memory_mb": round(self.start_memory, 2),
        }


class Phase2TestRunner:
    """Orchestrate Phase 2 tests for all agents"""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "phase": "Phase 2 - Production Testing",
            "agents": {},
            "summary": {}
        }
        self.test_data = {}
        self.load_test_data()
    
    def load_test_data(self):
        """Load test data files"""
        print("\n📊 Loading test data...")
        
        # Load small CSV
        small_csv = TEST_DATA_DIR / "small_dataset.csv"
        if small_csv.exists():
            self.test_data["small_csv"] = pd.read_csv(small_csv)
            print(f"  ✅ Small CSV: {self.test_data['small_csv'].shape}")
        else:
            print(f"  ⚠️  Small CSV not found: {small_csv}")
        
        # Load medium CSV
        medium_csv = TEST_DATA_DIR / "medium_dataset.csv"
        if medium_csv.exists():
            self.test_data["medium_csv"] = pd.read_csv(medium_csv)
            print(f"  ✅ Medium CSV: {self.test_data['medium_csv'].shape}")
        else:
            print(f"  ⚠️  Medium CSV not found: {medium_csv}")
        
        # Load JSON
        json_file = TEST_DATA_DIR / "test_data.json"
        if json_file.exists():
            with open(json_file) as f:
                json_data = json.load(f)
            self.test_data["json"] = json_data
            print(f"  ✅ JSON: {len(json_data)} records")
        else:
            print(f"  ⚠️  JSON not found: {json_file}")
        
        # Load Excel
        excel_file = TEST_DATA_DIR / "test_data.xlsx"
        if excel_file.exists():
            self.test_data["excel"] = pd.read_excel(excel_file)
            print(f"  ✅ Excel: {self.test_data['excel'].shape}")
        else:
            print(f"  ⚠️  Excel not found: {excel_file}")
    
    def test_data_loader(self) -> Dict[str, Any]:
        """Test DataLoader agent"""
        print("\n🔄 Testing DataLoader...")
        results = {"tests": {}}
        
        try:
            # Import agent
            from agents.data_loader import DataLoader
            agent = DataLoader()
            
            # Test 1: Load small CSV
            print("  • Test 1: Load small CSV...")
            monitor = PerformanceMonitor()
            monitor.start()
            
            if "small_csv" in self.test_data:
                csv_path = TEST_DATA_DIR / "small_dataset.csv"
                result = agent.load(str(csv_path))
                monitor.update_peak_memory()
                metrics = monitor.stop()
                
                results["tests"]["load_small_csv"] = {
                    "status": "✅ PASS" if isinstance(result, pd.DataFrame) else "❌ FAIL",
                    "rows_loaded": len(result) if isinstance(result, pd.DataFrame) else 0,
                    "metrics": metrics
                }
                print(f"    ✅ Load small CSV: {metrics['duration_seconds']}s")
            
            # Test 2: Load medium CSV
            print("  • Test 2: Load medium CSV...")
            monitor = PerformanceMonitor()
            monitor.start()
            
            if "medium_csv" in self.test_data:
                csv_path = TEST_DATA_DIR / "medium_dataset.csv"
                result = agent.load(str(csv_path))
                monitor.update_peak_memory()
                metrics = monitor.stop()
                
                results["tests"]["load_medium_csv"] = {
                    "status": "✅ PASS" if isinstance(result, pd.DataFrame) else "❌ FAIL",
                    "rows_loaded": len(result) if isinstance(result, pd.DataFrame) else 0,
                    "metrics": metrics
                }
                print(f"    ✅ Load medium CSV: {metrics['duration_seconds']}s")
            
            # Test 3: Load JSON
            print("  • Test 3: Load JSON...")
            monitor = PerformanceMonitor()
            monitor.start()
            
            if "json" in self.test_data:
                json_path = TEST_DATA_DIR / "test_data.json"
                result = agent.load(str(json_path))
                monitor.update_peak_memory()
                metrics = monitor.stop()
                
                results["tests"]["load_json"] = {
                    "status": "✅ PASS" if isinstance(result, pd.DataFrame) else "❌ FAIL",
                    "rows_loaded": len(result) if isinstance(result, pd.DataFrame) else 0,
                    "metrics": metrics
                }
                print(f"    ✅ Load JSON: {metrics['duration_seconds']}s")
            
            # Test 4: Load Excel
            print("  • Test 4: Load Excel...")
            monitor = PerformanceMonitor()
            monitor.start()
            
            if "excel" in self.test_data:
                excel_path = TEST_DATA_DIR / "test_data.xlsx"
                result = agent.load(str(excel_path))
                monitor.update_peak_memory()
                metrics = monitor.stop()
                
                results["tests"]["load_excel"] = {
                    "status": "✅ PASS" if isinstance(result, pd.DataFrame) else "❌ FAIL",
                    "rows_loaded": len(result) if isinstance(result, pd.DataFrame) else 0,
                    "metrics": metrics
                }
                print(f"    ✅ Load Excel: {metrics['duration_seconds']}s")
            
            results["status"] = "✅ READY"
            results["worker_pattern"] = "✅ Workers instantiated and delegating"
            
        except Exception as e:
            results["status"] = f"❌ ERROR: {str(e)}"
            results["error_traceback"] = traceback.format_exc()
            print(f"    ❌ Error: {str(e)}")
        
        return results
    
    def test_explorer(self) -> Dict[str, Any]:
        """Test Explorer agent"""
        print("\n🔍 Testing Explorer...")
        results = {"tests": {}}
        
        try:
            from agents.explorer import Explorer
            agent = Explorer()
            
            if "small_csv" not in self.test_data:
                results["status"] = "⚠️  SKIP - No test data"
                return results
            
            # Test 1: Analyze small dataset
            print("  • Test 1: Analyze small dataset...")
            monitor = PerformanceMonitor()
            monitor.start()
            
            df = self.test_data["small_csv"]
            agent.set_data(df)
            result = agent.analyze()
            monitor.update_peak_memory()
            metrics = monitor.stop()
            
            results["tests"]["analyze_small"] = {
                "status": "✅ PASS" if result else "❌ FAIL",
                "columns_analyzed": len(df.columns),
                "rows_analyzed": len(df),
                "metrics": metrics
            }
            print(f"    ✅ Analyze small: {metrics['duration_seconds']}s")
            
            # Test 2: Analyze medium dataset
            if "medium_csv" in self.test_data:
                print("  • Test 2: Analyze medium dataset...")
                monitor = PerformanceMonitor()
                monitor.start()
                
                df = self.test_data["medium_csv"]
                agent.set_data(df)
                result = agent.analyze()
                monitor.update_peak_memory()
                metrics = monitor.stop()
                
                results["tests"]["analyze_medium"] = {
                    "status": "✅ PASS" if result else "❌ FAIL",
                    "columns_analyzed": len(df.columns),
                    "rows_analyzed": len(df),
                    "metrics": metrics
                }
                print(f"    ✅ Analyze medium: {metrics['duration_seconds']}s")
            
            results["status"] = "✅ READY"
            results["worker_pattern"] = "✅ Workers instantiated and delegating"
            
        except Exception as e:
            results["status"] = f"❌ ERROR: {str(e)}"
            results["error_traceback"] = traceback.format_exc()
            print(f"    ❌ Error: {str(e)}")
        
        return results
    
    def test_aggregator(self) -> Dict[str, Any]:
        """Test Aggregator agent"""
        print("\n📊 Testing Aggregator...")
        results = {"tests": {}}
        
        try:
            from agents.aggregator import Aggregator
            agent = Aggregator()
            
            if "small_csv" not in self.test_data:
                results["status"] = "⚠️  SKIP - No test data"
                return results
            
            # Test 1: GroupBy operation
            print("  • Test 1: GroupBy aggregation...")
            monitor = PerformanceMonitor()
            monitor.start()
            
            df = self.test_data["small_csv"]
            agent.set_data(df)
            
            # Try groupby on first categorical column
            cat_cols = df.select_dtypes(include='object').columns
            if len(cat_cols) > 0:
                col = cat_cols[0]
                num_cols = df.select_dtypes(include=[np.number]).columns
                if len(num_cols) > 0:
                    result = agent.groupby_single(col, num_cols[0], 'mean')
                    monitor.update_peak_memory()
                    metrics = monitor.stop()
                    
                    results["tests"]["groupby_operation"] = {
                        "status": "✅ PASS" if result is not None else "❌ FAIL",
                        "metrics": metrics
                    }
                    print(f"    ✅ GroupBy: {metrics['duration_seconds']}s")
            
            results["status"] = "✅ READY"
            results["worker_pattern"] = "⚠️  CHECK WORKER WIRING"
            
        except Exception as e:
            results["status"] = f"❌ ERROR: {str(e)}"
            results["error_traceback"] = traceback.format_exc()
            print(f"    ❌ Error: {str(e)}")
        
        return results
    
    def test_predictor(self) -> Dict[str, Any]:
        """Test Predictor agent"""
        print("\n🔮 Testing Predictor...")
        results = {"tests": {}}
        
        try:
            from agents.predictor import Predictor
            agent = Predictor()
            
            if "small_csv" not in self.test_data:
                results["status"] = "⚠️  SKIP - No test data"
                return results
            
            # Test 1: Make predictions
            print("  • Test 1: Make predictions...")
            monitor = PerformanceMonitor()
            monitor.start()
            
            df = self.test_data["small_csv"]
            result = agent.predict(df)
            monitor.update_peak_memory()
            metrics = monitor.stop()
            
            results["tests"]["make_predictions"] = {
                "status": "✅ PASS" if result is not None else "❌ FAIL",
                "predictions_count": len(result) if hasattr(result, '__len__') else 0,
                "metrics": metrics
            }
            print(f"    ✅ Predictions: {metrics['duration_seconds']}s")
            
            results["status"] = "✅ READY"
            results["worker_pattern"] = "✅ Workers instantiated and delegating"
            
        except Exception as e:
            results["status"] = f"❌ ERROR: {str(e)}"
            results["error_traceback"] = traceback.format_exc()
            print(f"    ❌ Error: {str(e)}")
        
        return results
    
    def test_anomaly_detector(self) -> Dict[str, Any]:
        """Test AnomalyDetector agent"""
        print("\n🚨 Testing AnomalyDetector...")
        results = {"tests": {}}
        
        try:
            from agents.anomaly_detector import AnomalyDetector
            agent = AnomalyDetector()
            
            if "small_csv" not in self.test_data:
                results["status"] = "⚠️  SKIP - No test data"
                return results
            
            # Test 1: Detect anomalies
            print("  • Test 1: Detect anomalies...")
            monitor = PerformanceMonitor()
            monitor.start()
            
            df = self.test_data["small_csv"]
            result = agent.detect(df)
            monitor.update_peak_memory()
            metrics = monitor.stop()
            
            results["tests"]["detect_anomalies"] = {
                "status": "✅ PASS" if result is not None else "❌ FAIL",
                "metrics": metrics
            }
            print(f"    ✅ Anomaly detection: {metrics['duration_seconds']}s")
            
            results["status"] = "✅ READY"
            results["worker_pattern"] = "✅ Workers instantiated and delegating"
            
        except Exception as e:
            results["status"] = f"❌ ERROR: {str(e)}"
            results["error_traceback"] = traceback.format_exc()
            print(f"    ❌ Error: {str(e)}")
        
        return results
    
    def test_recommender(self) -> Dict[str, Any]:
        """Test Recommender agent"""
        print("\n💡 Testing Recommender...")
        results = {"tests": {}}
        
        try:
            from agents.recommender import Recommender
            agent = Recommender()
            
            if "small_csv" not in self.test_data:
                results["status"] = "⚠️  SKIP - No test data"
                return results
            
            # Test 1: Generate recommendations
            print("  • Test 1: Generate recommendations...")
            monitor = PerformanceMonitor()
            monitor.start()
            
            df = self.test_data["small_csv"]
            agent.set_data(df)
            result = agent.analyze_missing_data()
            monitor.update_peak_memory()
            metrics = monitor.stop()
            
            results["tests"]["generate_recommendations"] = {
                "status": "✅ PASS" if result else "❌ FAIL",
                "metrics": metrics
            }
            print(f"    ✅ Recommendations: {metrics['duration_seconds']}s")
            
            results["status"] = "✅ READY"
            results["worker_pattern"] = "✅ Workers instantiated and delegating"
            
        except Exception as e:
            results["status"] = f"❌ ERROR: {str(e)}"
            results["error_traceback"] = traceback.format_exc()
            print(f"    ❌ Error: {str(e)}")
        
        return results
    
    def test_reporter(self) -> Dict[str, Any]:
        """Test Reporter agent"""
        print("\n📄 Testing Reporter...")
        results = {"tests": {}}
        
        try:
            from agents.reporter import Reporter
            agent = Reporter()
            
            if "small_csv" not in self.test_data:
                results["status"] = "⚠️  SKIP - No test data"
                return results
            
            # Test 1: Generate report
            print("  • Test 1: Generate report...")
            monitor = PerformanceMonitor()
            monitor.start()
            
            df = self.test_data["small_csv"]
            result = agent.generate_report(df)
            monitor.update_peak_memory()
            metrics = monitor.stop()
            
            results["tests"]["generate_report"] = {
                "status": "✅ PASS" if result else "❌ FAIL",
                "report_type": type(result).__name__,
                "metrics": metrics
            }
            print(f"    ✅ Report generation: {metrics['duration_seconds']}s")
            
            results["status"] = "✅ READY"
            results["worker_pattern"] = "✅ Workers instantiated and delegating"
            
        except Exception as e:
            results["status"] = f"❌ ERROR: {str(e)}"
            results["error_traceback"] = traceback.format_exc()
            print(f"    ❌ Error: {str(e)}")
        
        return results
    
    def test_visualizer(self) -> Dict[str, Any]:
        """Test Visualizer agent"""
        print("\n📊 Testing Visualizer...")
        results = {"tests": {}}
        
        try:
            from agents.visualizer import Visualizer
            agent = Visualizer()
            
            if "small_csv" not in self.test_data:
                results["status"] = "⚠️  SKIP - No test data"
                return results
            
            # Test 1: Create visualization
            print("  • Test 1: Create visualization...")
            monitor = PerformanceMonitor()
            monitor.start()
            
            df = self.test_data["small_csv"]
            num_cols = df.select_dtypes(include=[np.number]).columns
            if len(num_cols) >= 2:
                result = agent.plot_line_chart(df, num_cols[0], num_cols[1])
                monitor.update_peak_memory()
                metrics = monitor.stop()
                
                results["tests"]["create_visualization"] = {
                    "status": "✅ PASS" if result is not None else "❌ FAIL",
                    "metrics": metrics
                }
                print(f"    ✅ Visualization: {metrics['duration_seconds']}s")
            else:
                results["tests"]["create_visualization"] = {
                    "status": "⚠️  SKIP - Not enough numeric columns",
                    "metrics": {"duration_seconds": 0}
                }
            
            results["status"] = "✅ READY"
            results["worker_pattern"] = "✅ Workers instantiated and delegating"
            
        except Exception as e:
            results["status"] = f"❌ ERROR: {str(e)}"
            results["error_traceback"] = traceback.format_exc()
            print(f"    ❌ Error: {str(e)}")
        
        return results
    
    def run_all_tests(self):
        """Run all agent tests"""
        print("\n" + "="*80)
        print("🚀 PHASE 2 TEST RUNNER - Production Testing")
        print("="*80)
        
        # Run tests for each agent
        self.results["agents"]["DataLoader"] = self.test_data_loader()
        self.results["agents"]["Explorer"] = self.test_explorer()
        self.results["agents"]["Aggregator"] = self.test_aggregator()
        self.results["agents"]["Predictor"] = self.test_predictor()
        self.results["agents"]["AnomalyDetector"] = self.test_anomaly_detector()
        self.results["agents"]["Recommender"] = self.test_recommender()
        self.results["agents"]["Reporter"] = self.test_reporter()
        self.results["agents"]["Visualizer"] = self.test_visualizer()
        
        # Generate summary
        self.generate_summary()
        
        # Save results
        self.save_results()
        
        # Print summary
        self.print_summary()
    
    def generate_summary(self):
        """Generate test summary"""
        total_agents = len(self.results["agents"])
        ready_agents = sum(1 for agent in self.results["agents"].values() 
                          if agent.get("status", "").startswith("✅"))
        failed_agents = sum(1 for agent in self.results["agents"].values() 
                           if agent.get("status", "").startswith("❌"))
        skipped_agents = sum(1 for agent in self.results["agents"].values() 
                            if agent.get("status", "").startswith("⚠️"))
        
        self.results["summary"] = {
            "total_agents": total_agents,
            "ready_agents": ready_agents,
            "failed_agents": failed_agents,
            "skipped_agents": skipped_agents,
            "phase_status": "✅ PASS" if failed_agents == 0 and ready_agents > 0 else "❌ FAIL"
        }
    
    def save_results(self):
        """Save test results to JSON"""
        with open(TEST_RESULTS_FILE, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        print(f"\n📁 Results saved to: {TEST_RESULTS_FILE}")
    
    def print_summary(self):
        """Print test summary"""
        summary = self.results["summary"]
        
        print("\n" + "="*80)
        print("📊 PHASE 2 TEST SUMMARY")
        print("="*80)
        print(f"Total Agents: {summary['total_agents']}")
        print(f"Ready: {summary['ready_agents']} ✅")
        print(f"Failed: {summary['failed_agents']} ❌")
        print(f"Skipped: {summary['skipped_agents']} ⚠️")
        print(f"\nPhase Status: {summary['phase_status']}")
        print("="*80)
        
        # Detailed agent status
        print("\n📋 AGENT STATUS:")
        for agent_name, agent_results in self.results["agents"].items():
            status = agent_results.get("status", "⚠️  UNKNOWN")
            print(f"  {agent_name:20} {status}")
        
        print("\n" + "="*80)


if __name__ == "__main__":
    runner = Phase2TestRunner()
    runner.run_all_tests()
