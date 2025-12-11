"""Test ErrorIntelligence - Tests success/error tracking and health calculation."""

import sys
import os
import json
import pandas as pd
import numpy as np
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.error_intelligence.main import ErrorIntelligence
from agents.error_intelligence.workers.error_tracker import ErrorTracker
from agents.error_intelligence.workers.worker_health import WorkerHealth


def test_error_tracker_track_success():
    """Test that track_success increments success counters, not failure."""
    print("\n=== Test 1: track_success increments success counters ===")
    tracker = ErrorTracker()
    
    # Track 3 successes
    for i in range(3):
        tracker.track_success(
            agent_name="test_agent",
            worker_name="test_worker",
            operation=f"operation_{i}",
            context={"iteration": i}
        )
    
    patterns = tracker.get_patterns()
    assert "test_agent" in patterns
    assert patterns["test_agent"]["successes"] == 3
    assert patterns["test_agent"]["failures"] == 0
    assert patterns["test_agent"]["total_runs"] == 3
    
    print(f"✓ Tracked 3 successes")
    print(f"  - Total runs: {patterns['test_agent']['total_runs']}")
    print(f"  - Successes: {patterns['test_agent']['successes']}")
    print(f"  - Failures: {patterns['test_agent']['failures']}")
    assert True


def test_error_tracker_track_error():
    """Test that track_error increments failure counters."""
    print("\n=== Test 2: track_error increments failure counters ===")
    tracker = ErrorTracker()
    
    # Track 2 errors
    for i in range(2):
        tracker.track_error(
            agent_name="test_agent",
            worker_name="test_worker",
            error_type="ValueError",
            error_message=f"Invalid value: {i}",
            context={"iteration": i}
        )
    
    patterns = tracker.get_patterns()
    assert patterns["test_agent"]["failures"] == 2
    assert patterns["test_agent"]["successes"] == 0
    assert patterns["test_agent"]["total_runs"] == 2
    
    print(f"✓ Tracked 2 errors")
    print(f"  - Total runs: {patterns['test_agent']['total_runs']}")
    print(f"  - Successes: {patterns['test_agent']['successes']}")
    print(f"  - Failures: {patterns['test_agent']['failures']}")
    assert True


def test_error_tracker_mixed_success_and_error():
    """Test mixed success and error tracking."""
    print("\n=== Test 3: Mixed success and error tracking ===")
    tracker = ErrorTracker()
    
    # Track 5 successes and 2 errors
    for i in range(5):
        tracker.track_success(
            agent_name="aggregator",
            worker_name="StatisticsWorker",
            operation="calculate_stats"
        )
    
    for i in range(2):
        tracker.track_error(
            agent_name="aggregator",
            worker_name="StatisticsWorker",
            error_type="KeyError",
            error_message=f"Column not found: col_{i}"
        )
    
    patterns = tracker.get_patterns()
    stats = tracker.get_agent_stats("aggregator")
    
    assert patterns["aggregator"]["total_runs"] == 7
    assert patterns["aggregator"]["successes"] == 5
    assert patterns["aggregator"]["failures"] == 2
    assert round(stats["success_rate"], 2) == 71.43  # 5/7 * 100
    
    print(f"✓ Mixed tracking: 5 successes + 2 errors")
    print(f"  - Total runs: {patterns['aggregator']['total_runs']}")
    print(f"  - Success rate: {stats['success_rate']:.2f}%")
    print(f"  - Failure rate: {stats['failure_rate']:.2f}%")
    assert True


def test_error_tracker_multiple_workers():
    """Test tracking across multiple workers."""
    print("\n=== Test 4: Multiple workers tracking ===")
    tracker = ErrorTracker()
    
    workers = [
        ("StatisticsWorker", 10, 1),
        ("CrossTabWorker", 8, 2),
        ("GroupByWorker", 9, 1),
    ]
    
    for worker_name, successes, failures in workers:
        for i in range(successes):
            tracker.track_success(
                agent_name="aggregator",
                worker_name=worker_name,
                operation=f"op_{i}"
            )
        for i in range(failures):
            tracker.track_error(
                agent_name="aggregator",
                worker_name=worker_name,
                error_type="RuntimeError",
                error_message=f"Error {i}"
            )
    
    patterns = tracker.get_patterns()
    agent_stats = patterns["aggregator"]
    
    total_successes = 10 + 8 + 9
    total_failures = 1 + 2 + 1
    total_runs = total_successes + total_failures
    
    assert agent_stats["successes"] == total_successes
    assert agent_stats["failures"] == total_failures
    assert agent_stats["total_runs"] == total_runs
    assert len(agent_stats["workers"]) == 3
    
    print(f"✓ Tracking {len(agent_stats['workers'])} workers")
    for worker_name, worker_data in agent_stats["workers"].items():
        success_rate = (worker_data["successes"] / (worker_data["successes"] + worker_data["failures"]) * 100) if (worker_data["successes"] + worker_data["failures"]) > 0 else 0
        print(f"  - {worker_name}: {worker_data['successes']}S / {worker_data['failures']}F ({success_rate:.1f}%)")
    assert True


def test_worker_health_calculation():
    """Test health score calculation."""
    print("\n=== Test 5: Worker health calculation ===")
    tracker = ErrorTracker()
    
    # Healthy worker: 90 successes, 10 errors = 90% success rate
    for i in range(90):
        tracker.track_success(
            agent_name="aggregator",
            worker_name="HealthyWorker",
            operation="work"
        )
    for i in range(10):
        tracker.track_error(
            agent_name="aggregator",
            worker_name="HealthyWorker",
            error_type="Error",
            error_message="error"
        )
    
    # Degraded worker: 70 successes, 30 errors = 70% success rate
    for i in range(70):
        tracker.track_success(
            agent_name="aggregator",
            worker_name="DegradedWorker",
            operation="work"
        )
    for i in range(30):
        tracker.track_error(
            agent_name="aggregator",
            worker_name="DegradedWorker",
            error_type="Error",
            error_message="error"
        )
    
    # Broken worker: 40 successes, 60 errors = 40% success rate
    for i in range(40):
        tracker.track_success(
            agent_name="aggregator",
            worker_name="BrokenWorker",
            operation="work"
        )
    for i in range(60):
        tracker.track_error(
            agent_name="aggregator",
            worker_name="BrokenWorker",
            error_type="Error",
            error_message="error"
        )
    
    patterns = tracker.get_patterns()
    health = WorkerHealth().calculate(patterns)
    
    healthy_health = health["aggregator"]["workers"]["HealthyWorker"]
    degraded_health = health["aggregator"]["workers"]["DegradedWorker"]
    broken_health = health["aggregator"]["workers"]["BrokenWorker"]
    
    assert healthy_health["status"] == "HEALTHY"
    assert degraded_health["status"] == "DEGRADED"
    assert broken_health["status"] == "BROKEN"
    
    print(f"✓ Health statuses calculated correctly")
    print(f"  - HealthyWorker (90%): {healthy_health['status']}")
    print(f"  - DegradedWorker (70%): {degraded_health['status']}")
    print(f"  - BrokenWorker (40%): {broken_health['status']}")
    assert True


def test_error_intelligence_api():
    """Test ErrorIntelligence public API."""
    print("\n=== Test 6: ErrorIntelligence API ===")
    ei = ErrorIntelligence()
    
    # Clear previous patterns
    ei.error_tracker.clear()
    
    # Test track_success API
    ei.track_success(
        agent_name="test_agent",
        worker_name="test_worker",
        operation="test_operation",
        context={"test": "data"}
    )
    
    # Test track_error API
    ei.track_error(
        agent_name="test_agent",
        worker_name="test_worker",
        error_type="TestError",
        error_message="Test error message",
        context={"test": "data"}
    )
    
    patterns = ei.error_tracker.get_patterns()
    assert patterns["test_agent"]["successes"] == 1
    assert patterns["test_agent"]["failures"] == 1
    
    print(f"✓ ErrorIntelligence API working")
    print(f"  - track_success: ✓")
    print(f"  - track_error: ✓")
    assert True


def test_error_intelligence_health_report():
    """Test full health report generation."""
    print("\n=== Test 7: Full health report ===")
    ei = ErrorIntelligence()
    ei.error_tracker.clear()
    
    # Simulate multiple workers with different success rates
    workers_data = [
        ("Worker1", 95, 5),
        ("Worker2", 80, 20),
        ("Worker3", 50, 50),
    ]
    
    for worker_name, successes, failures in workers_data:
        for i in range(successes):
            ei.track_success(
                agent_name="aggregator",
                worker_name=worker_name,
                operation="execute"
            )
        for i in range(failures):
            ei.track_error(
                agent_name="aggregator",
                worker_name=worker_name,
                error_type="Error",
                error_message="error"
            )
    
    health = ei.get_worker_health()
    agent_health = health["aggregator"]["agent_health"]
    workers_health = health["aggregator"]["workers"]
    
    print(f"✓ Agent overall health: {agent_health['status']}")
    print(f"  - Total runs: {agent_health['total_runs']}")
    print(f"  - Success rate: {agent_health['success_rate']}%")
    print(f"  - Worker breakdown:")
    for worker_name, worker_health in workers_health.items():
        print(f"    • {worker_name}: {worker_health['success_rate']}% ({worker_health['status']})")
    
    assert True


if __name__ == "__main__":
    print("\n" + "="*70)
    print("ERROR INTELLIGENCE TEST SUITE")
    print("="*70)
    
    try:
        test_error_tracker_track_success()
        test_error_tracker_track_error()
        test_error_tracker_mixed_success_and_error()
        test_error_tracker_multiple_workers()
        test_worker_health_calculation()
        test_error_intelligence_api()
        test_error_intelligence_health_report()
        
        print("\n" + "="*70)
        print("✓ ALL TESTS PASSED (7/7)")
        print("="*70 + "\n")
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
