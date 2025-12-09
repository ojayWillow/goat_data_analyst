#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Session Summary Script - Show project state before/after session.

Run at START of session to capture 'before' state.
Run at END of session to show 'before' vs 'after' state.

Usage:
  python scripts/session_summary.py start   # At beginning
  python scripts/session_summary.py end     # At end
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.project_manager.project_manager import ProjectManager


class SessionTracker:
    """Track project state at session start and end."""

    def __init__(self):
        self.project_root = project_root
        self.state_file = self.project_root / ".session_state.json"
        self.pm = ProjectManager()

    def capture_state(self) -> Dict:
        """Capture current project state."""
        report = self.pm.execute()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "agents": len(report["structure"]["agents"]),
            "tests": len(report["structure"]["tests"]),
            "health_score": report["health"]["health_score"],
            "test_coverage": report["health"]["summary"]["test_coverage"],
            "files_organized": report["cleanup"]["total_moved"],
            "agent_list": list(report["structure"]["agents"].keys()),
            "test_list": list(report["structure"]["tests"].keys()),
        }

    def start_session(self) -> None:
        """Capture state at session start."""
        print("\n" + "=" * 60)
        print("SESSION START - Capturing project state...")
        print("=" * 60)

        state = self.capture_state()
        state["phase"] = "start"
        
        with open(self.state_file, "w") as f:
            json.dump(state, f, indent=2)

        print(f"\nProject State:")
        print(f"  Agents: {state['agents']}")
        print(f"  Tests: {state['tests']}")
        print(f"  Health: {state['health_score']}/100")
        print(f"  Test Coverage: {state['test_coverage']}%")
        print(f"  Files Organized: {state['files_organized']}")
        print(f"\nAgents: {', '.join(state['agent_list'])}")
        print(f"\nState saved to .session_state.json")
        print("\n" + "=" * 60 + "\n")

    def end_session(self) -> None:
        """Capture state at session end and show comparison."""
        if not self.state_file.exists():
            print("ERROR: No session start state found.")
            print("Run: python scripts/session_summary.py start")
            return

        print("\n" + "=" * 60)
        print("SESSION END - Comparing project states...")
        print("=" * 60)

        # Load start state
        with open(self.state_file, "r") as f:
            start_state = json.load(f)

        # Capture end state
        end_state = self.capture_state()
        end_state["phase"] = "end"

        # Compare
        print("\nBEFORE (Session Start):")
        print(f"  Agents: {start_state['agents']}")
        print(f"  Tests: {start_state['tests']}")
        print(f"  Health: {start_state['health_score']}/100")
        print(f"  Test Coverage: {start_state['test_coverage']}%")
        print(f"  Files Organized: {start_state['files_organized']}")

        print("\nAFTER (Session End):")
        print(f"  Agents: {end_state['agents']}")
        print(f"  Tests: {end_state['tests']}")
        print(f"  Health: {end_state['health_score']}/100")
        print(f"  Test Coverage: {end_state['test_coverage']}%")
        print(f"  Files Organized: {end_state['files_organized']}")

        # Changes
        print("\nCHANGES:")
        agent_diff = end_state['agents'] - start_state['agents']
        test_diff = end_state['tests'] - start_state['tests']
        health_diff = end_state['health_score'] - start_state['health_score']
        coverage_diff = end_state['test_coverage'] - start_state['test_coverage']
        files_diff = end_state['files_organized'] - start_state['files_organized']

        print(f"  Agents: {agent_diff:+d} (was {start_state['agents']}, now {end_state['agents']})")
        print(f"  Tests: {test_diff:+d} (was {start_state['tests']}, now {end_state['tests']})")
        print(f"  Health: {health_diff:+.1f} (was {start_state['health_score']}, now {end_state['health_score']})")
        print(f"  Coverage: {coverage_diff:+.1f}% (was {start_state['test_coverage']}%, now {end_state['test_coverage']}%)")
        print(f"  Files: {files_diff:+d} (was {start_state['files_organized']}, now {end_state['files_organized']})")

        # New agents
        new_agents = set(end_state['agent_list']) - set(start_state['agent_list'])
        removed_agents = set(start_state['agent_list']) - set(end_state['agent_list'])
        new_tests = set(end_state['test_list']) - set(start_state['test_list'])

        if new_agents:
            print(f"\nNew Agents: {', '.join(new_agents)}")
        if removed_agents:
            print(f"Removed Agents: {', '.join(removed_agents)}")
        if new_tests:
            print(f"New Tests: {', '.join(new_tests)}")

        # Summary
        if agent_diff == 0 and test_diff == 0:
            print("\nSession Status: Maintenance (no new agents/tests)")
        elif agent_diff > 0 or test_diff > 0:
            print(f"\nSession Status: Development ({agent_diff + test_diff} new items)")
        else:
            print("\nSession Status: Cleanup")

        print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/session_summary.py [start|end]")
        sys.exit(1)

    command = sys.argv[1].lower()
    tracker = SessionTracker()

    if command == "start":
        tracker.start_session()
    elif command == "end":
        tracker.end_session()
    else:
        print(f"Unknown command: {command}")
        print("Use: start or end")
        sys.exit(1)
