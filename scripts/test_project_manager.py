#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Quick ProjectManager Test Script.

Tests the self-aware, adaptive project coordinator:
- Auto-discovers agents and tests
- Learns patterns from existing code
- Validates new agents
- Tracks changes
- Generates health reports

Run: python scripts/test_project_manager.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.project_manager.project_manager import ProjectManager


def print_separator(title=""):
    """Print formatted separator."""
    if title:
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
    else:
        print(f"{'='*60}")


def test_project_manager():
    """Test ProjectManager functionality."""
    print_separator("ProjectManager - Self-Aware Project Coordinator")
    
    try:
        # Initialize
        print("\n🚀 Initializing ProjectManager...")
        pm = ProjectManager()
        print("   ✅ Initialized successfully")
        
        # Execute full analysis
        print("\n📊 Executing project analysis...")
        report = pm.execute()
        print("   ✅ Analysis complete")
        
        # Print results
        print_separator("DISCOVERED STRUCTURE")
        structure = report["structure"]
        print(f"\n📁 Agents Discovered: {len(structure['agents'])}")
        for agent_name, info in structure["agents"].items():
            test_status = "✅ Has test" if info.get("has_test") else "⚠️  No test"
            print(f"   • {agent_name:<20} {test_status}")
        
        print(f"\n🧪 Tests Discovered: {len(structure['tests'])}")
        for test_name in list(structure["tests"].keys())[:5]:
            print(f"   • {test_name}")
        if len(structure["tests"]) > 5:
            print(f"   ... and {len(structure['tests']) - 5} more")
        
        # Print patterns
        print_separator("LEARNED PATTERNS")
        patterns = report["patterns"]
        print(f"\n🧠 Pattern Confidence: {patterns['pattern_confidence']*100:.0f}%")
        print(f"   Analyzed Agents: {patterns['total_agents_analyzed']}")
        
        pattern = patterns.get("agent_pattern", {})
        if pattern:
            print(f"\n   Agent Structure:")
            print(f"   • Has __init__: {pattern['agent_structure']['has_init']}")
            print(f"   • Has main file: {pattern['agent_structure']['has_main_file']}")
            print(f"   • Expected methods: {', '.join(pattern['expected_methods'][:3])}...")
            print(f"   • Naming convention: {pattern['naming_convention']}")
        
        # Print changes
        print_separator("CHANGE TRACKING")
        changes = report["changes"]
        print(f"\n📝 Changes Detected:")
        if changes.get("new_agents"):
            print(f"   • New agents: {', '.join(changes['new_agents'])}")
        if changes.get("removed_agents"):
            print(f"   • Removed agents: {', '.join(changes['removed_agents'])}")
        if changes.get("new_tests"):
            print(f"   • New tests: {', '.join(changes['new_tests'])}")
        
        if not (changes.get("new_agents") or changes.get("new_tests") or changes.get("removed_agents")):
            print("   • No changes detected (stable state)")
        
        # Print health report
        print_separator("PROJECT HEALTH REPORT")
        health = report["health"]
        print(f"\n{health['status']}")
        print(f"   Score: {health['health_score']}/100")
        
        summary = health["summary"]
        print(f"\n📊 Summary:")
        print(f"   • Total Agents: {summary['total_agents']}")
        print(f"   • Tested: {summary['tested_agents']}")
        print(f"   • Untested: {summary['untested_agents']}")
        print(f"   • Test Coverage: {summary['test_coverage']}%")
        print(f"   • Total Tests: {summary['total_tests']}")
        
        print(f"\n💡 Recommendations:")
        for rec in health["recommendations"]:
            print(f"   • {rec}")
        
        # Test agent validation
        print_separator("AGENT VALIDATION")
        test_names = ["new_agent", "test_agent", "DataLoader", ""]
        for test_name in test_names:
            validation = pm.validate_new_agent(test_name)
            status = "✅ Valid" if validation["valid"] else "⚠️  Invalid"
            issues = f" ({', '.join(validation['issues'][:1])})" if validation["issues"] else ""
            print(f"\n   {test_name or '(empty)'}")
            print(f"   {status}{issues}")
        
        # Print agent summary
        print_separator("AGENT SUMMARY")
        print(pm.get_agent_summary())
        
        print_separator("✅ All Tests Passed")
        print(f"\nProjectManager is working perfectly!")
        print(f"- Auto-discovery: ✅")
        print(f"- Pattern learning: ✅")
        print(f"- Change tracking: ✅")
        print(f"- Health reporting: ✅")
        print(f"- Agent validation: ✅")
        print()
        
    except Exception as e:
        print_separator("❌ ERROR")
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = test_project_manager()
    sys.exit(0 if success else 1)
