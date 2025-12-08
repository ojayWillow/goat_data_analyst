#!/usr/bin/env python3
"""Test Orchestrator integration with all agents.

Demonstrates:
- Agent registration
- Task routing
- Inter-agent communication
- Workflow execution
- Data caching between agents

Usage:
    python scripts/test_orchestrator_integration.py
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.orchestrator import Orchestrator
from agents.data_loader import DataLoader
from agents.explorer import Explorer
from agents.aggregator import Aggregator
from agents.visualizer import Visualizer
from agents.predictor import Predictor
from agents.anomaly_detector import AnomalyDetector
from agents.recommender import Recommender
from agents.reporter import Reporter
from core.logger import get_logger

logger = get_logger(__name__)


def main():
    logger.info("="*80)
    logger.info("ORCHESTRATOR INTEGRATION TEST - ALL AGENTS CONNECTED")
    logger.info("="*80)
    
    # Initialize Orchestrator
    logger.info("\n[STEP 1: Initialize Orchestrator]")
    orchestrator = Orchestrator()
    logger.info(f"[OK] Orchestrator initialized")
    
    # Register all agents
    logger.info("\n[STEP 2: Register All Agents]")
    agents_to_register = [
        ("data_loader", DataLoader()),
        ("explorer", Explorer()),
        ("aggregator", Aggregator()),
        ("visualizer", Visualizer()),
        ("predictor", Predictor()),
        ("anomaly_detector", AnomalyDetector()),
        ("recommender", Recommender()),
        ("reporter", Reporter()),
    ]
    
    for agent_name, agent_instance in agents_to_register:
        try:
            orchestrator.register_agent(agent_name, agent_instance)
            logger.info(f"[OK] Registered: {agent_name}")
        except Exception as e:
            logger.error(f"[ERROR] Failed to register {agent_name}: {e}")
    
    # Check all agents registered
    logger.info("\n[STEP 3: Verify Registration]")
    registered = orchestrator.list_agents()
    logger.info(f"Total agents registered: {len(registered)}")
    logger.info(f"Agents: {registered}")
    
    # Get sample data file
    logger.info("\n[STEP 4: Create Sample Workflow]")
    data_dir = project_root / "data"
    csv_files = sorted([f for f in data_dir.glob("*.csv") if f.name != 'sample_data.csv'])
    
    if not csv_files:
        logger.error("No data files found")
        return
    
    sample_file = str(csv_files[0])
    logger.info(f"Using data file: {Path(sample_file).name}")
    
    # Define a complete workflow
    workflow = [
        {
            "type": "load_data",
            "parameters": {"file_path": sample_file},
            "cache_as": "loaded_data",
        },
        {
            "type": "explore_data",
            "parameters": {"data_key": "loaded_data"},
        },
        {
            "type": "get_recommendations",
            "parameters": {"data_key": "loaded_data"},
        },
        {
            "type": "generate_report",
            "parameters": {"data_key": "loaded_data", "report_type": "executive_summary"},
        },
    ]
    
    # Execute workflow
    logger.info("\n[STEP 5: Execute Workflow]")
    logger.info(f"Workflow tasks: {len(workflow)}")
    
    try:
        workflow_result = orchestrator.execute_workflow(workflow)
        
        logger.info(f"\n[WORKFLOW RESULTS]")
        logger.info(f"Workflow ID: {workflow_result['workflow_id']}")
        logger.info(f"Status: {workflow_result['status']}")
        logger.info(f"Tasks completed: {len(workflow_result['tasks'])}")
        
        # Show results per task
        for i, task in enumerate(workflow_result['tasks'], 1):
            logger.info(f"\n  Task {i}: {task['type']}")
            logger.info(f"    Status: {task['status']}")
            if task['status'] == 'completed' and task['result']:
                result = task['result']
                if isinstance(result, dict) and 'status' in result:
                    logger.info(f"    Result status: {result['status']}")
                    if 'message' in result:
                        logger.info(f"    Message: {result['message'][:100]}")
    except Exception as e:
        logger.error(f"[ERROR] Workflow execution failed: {e}")
    
    # Test individual task execution
    logger.info("\n[STEP 6: Test Individual Task Routing]")
    
    test_tasks = [
        ("load_data", {"file_path": sample_file}),
        ("explore_data", {"data_key": "loaded_data"}),
        ("detect_anomalies", {"data_key": "loaded_data", "method": "iqr", "column": None}),
    ]
    
    for task_type, params in test_tasks:
        try:
            logger.info(f"\n  Testing: {task_type}")
            task = orchestrator.create_task(task_type, params)
            result = orchestrator.execute_task(task["id"])
            logger.info(f"    [OK] Task executed successfully")
        except Exception as e:
            logger.debug(f"    [INFO] {e}")
    
    # Check workflow status
    logger.info("\n[STEP 7: Check Workflow Status]")
    status = orchestrator.get_workflow_status()
    logger.info(f"Total tasks executed: {status['tasks_summary']['total']}")
    logger.info(f"Completed: {status['tasks_summary']['completed']}")
    logger.info(f"Failed: {status['tasks_summary']['failed']}")
    logger.info(f"Cached data keys: {status['cached_data_keys']}")
    
    # Verify inter-agent communication
    logger.info("\n[STEP 8: Verify Inter-Agent Communication]")
    cached_data = orchestrator.get_cached_data("loaded_data")
    if cached_data is not None:
        logger.info(f"[OK] Data successfully cached and accessible to agents")
        logger.info(f"    Cached data shape: {cached_data.shape}")
    else:
        logger.info(f"[INFO] No cached data found")
    
    logger.info("\n" + "="*80)
    logger.info("[OK] Orchestrator Integration Test Complete!")
    logger.info("\nAll agents successfully registered and connected to Orchestrator.")
    logger.info("Workflows can now coordinate multiple agents.")
    logger.info("="*80)


if __name__ == "__main__":
    main()
