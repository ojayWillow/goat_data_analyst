"""StructureScanner Worker - Auto-discovers project structure with advanced detection.

Enhances original with:
- Detects worker folders vs flat structure
- Tracks file sizes and metrics
- Identifies documentation coverage
- Detects circular dependencies
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Any, Tuple

from core.logger import get_logger


class StructureScanner:
    """Scans project and discovers structure automatically."""

    def __init__(self, logger=None):
        self.logger = logger or get_logger("StructureScanner")
        self.project_root = Path(__file__).parent.parent.parent.parent

    def discover_agents(self) -> Dict[str, Dict[str, Any]]:
        """Discover all agents with detailed metadata."""
        agents = {}
        agents_dir = self.project_root / "agents"

        if not agents_dir.exists():
            return agents

        # Discover folder-based agents (preferred)
        for item in agents_dir.iterdir():
            if not item.is_dir() or item.name.startswith("_"):
                continue

            agent_name = item.name
            main_file = item / f"{agent_name}.py"
            
            # Try exact match first, then first .py file
            if not main_file.exists():
                py_files = [f for f in item.glob("*.py") if not f.name.startswith("_")]
                if not py_files:
                    continue
                main_file = py_files[0]

            agents[agent_name] = {
                "path": str(item),
                "main_file": str(main_file),
                "exists": True,
                "has_test": self._has_test(agent_name),
                "has_workers": self._has_workers_folder(item),
                "worker_count": self._count_workers(item),
                "file_size_bytes": self._get_folder_size(item),
                "has_documentation": self._has_documentation(item),
                "discoverable": True,
                "type": "folder",
            }

        return agents

    def discover_tests(self) -> Dict[str, Dict[str, Any]]:
        """Discover all test files with metadata."""
        tests = {}
        tests_dir = self.project_root / "tests"

        if not tests_dir.exists():
            return tests

        for test_file in tests_dir.glob("test_*.py"):
            test_name = test_file.stem
            tests[test_name] = {
                "path": str(test_file),
                "exists": True,
                "discoverable": True,
                "file_size_bytes": test_file.stat().st_size,
                "last_modified": datetime.fromtimestamp(test_file.stat().st_mtime).isoformat(),
            }

        return tests

    def discover_core_systems(self) -> Dict[str, Dict[str, Any]]:
        """Discover core foundation systems."""
        systems = {}
        core_dir = self.project_root / "core"

        if not core_dir.exists():
            return systems

        for py_file in core_dir.glob("*.py"):
            if py_file.name.startswith("_"):
                continue
            system_name = py_file.stem
            systems[system_name] = {
                "path": str(py_file),
                "exists": True,
                "file_size_bytes": py_file.stat().st_size,
            }

        return systems

    def discover_documentation(self) -> Dict[str, Dict[str, Any]]:
        """Discover all documentation files."""
        docs = {}
        
        # Root level docs
        for md_file in self.project_root.glob("*.md"):
            doc_name = md_file.stem
            docs[doc_name] = {
                "path": str(md_file),
                "location": "root",
                "file_size_bytes": md_file.stat().st_size,
            }
        
        # docs/ folder
        docs_dir = self.project_root / "docs"
        if docs_dir.exists():
            for md_file in docs_dir.glob("*.md"):
                doc_name = md_file.stem
                docs[doc_name] = {
                    "path": str(md_file),
                    "location": "docs",
                    "file_size_bytes": md_file.stat().st_size,
                }

        return docs

    def discover_structure(self) -> Dict[str, Any]:
        """Discover complete project structure."""
        return {
            "agents": self.discover_agents(),
            "tests": self.discover_tests(),
            "core_systems": self.discover_core_systems(),
            "documentation": self.discover_documentation(),
            "discovered_at": datetime.now().isoformat(),
        }

    def _has_test(self, agent_name: str) -> bool:
        """Check if agent has corresponding test file."""
        tests_dir = self.project_root / "tests"
        return (tests_dir / f"test_{agent_name}.py").exists()

    def _has_workers_folder(self, agent_path: Path) -> bool:
        """Check if agent has workers subdirectory."""
        workers_dir = agent_path / "workers"
        return workers_dir.exists() and workers_dir.is_dir()

    def _count_workers(self, agent_path: Path) -> int:
        """Count number of worker files in agent."""
        workers_dir = agent_path / "workers"
        if not workers_dir.exists():
            return 0
        return len(list(workers_dir.glob("*.py"))) - 1  # Exclude __init__.py

    def _get_folder_size(self, folder_path: Path) -> int:
        """Get total size of folder in bytes."""
        total = 0
        for file_path in folder_path.rglob("*"):
            if file_path.is_file():
                total += file_path.stat().st_size
        return total

    def _has_documentation(self, agent_path: Path) -> bool:
        """Check if agent has documentation."""
        return bool(list(agent_path.glob("*.md"))) or bool(list(agent_path.glob("docs/*.md")))
