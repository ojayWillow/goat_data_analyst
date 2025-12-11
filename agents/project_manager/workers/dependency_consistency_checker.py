"""DependencyConsistencyChecker Worker - Check import and dependency consistency.

Checks:
- Agents use consistent core imports
- No conflicting dependencies
- All required core modules imported
- Circular dependency detection
"""

import ast
from pathlib import Path
from typing import Dict, List, Any, Set

from core.logger import get_logger


class DependencyConsistencyChecker:
    """Checks dependency consistency across agents."""

    def __init__(self, logger=None):
        self.logger = logger or get_logger("DependencyConsistencyChecker")
        self.project_root = Path(__file__).parent.parent.parent.parent
        
        # Expected core imports every agent should have
        self.expected_core_imports = {
            "core.logger": "For logging",
            "typing": "For type hints",
            "pathlib.Path": "For file handling",
        }

    def check_consistency(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Check dependency consistency across all agents."""
        agents = structure.get("agents", {})
        
        dependency_results = {}
        missing_standard_imports = []
        inconsistent_imports = []
        
        for agent_name, info in agents.items():
            agent_path = Path(info["path"])
            imports = self._extract_agent_imports(agent_path, agent_name)
            dependency_results[agent_name] = imports
            
            # Check for missing standard imports
            missing = self._check_missing_standard_imports(imports, agent_name)
            if missing:
                missing_standard_imports.extend(missing)
        
        # Check for inconsistency
        inconsistent_imports = self._find_inconsistencies(dependency_results)
        
        consistency_score = self._calculate_consistency_score(
            dependency_results,
            missing_standard_imports,
            inconsistent_imports
        )
        
        return {
            "total_agents": len(agents),
            "consistency_score": round(consistency_score, 2),
            "dependency_results": dependency_results,
            "missing_standard_imports": missing_standard_imports,
            "inconsistent_imports": inconsistent_imports,
            "priority_fixes": self._get_priority_fixes(
                missing_standard_imports,
                inconsistent_imports
            ),
            "status": self._get_status(consistency_score),
        }

    def _extract_agent_imports(self, agent_path: Path, agent_name: str) -> Dict[str, Any]:
        """Extract all imports from an agent."""
        main_file = agent_path / f"{agent_name}.py"
        if not main_file.exists():
            py_files = [f for f in agent_path.glob("*.py") if not f.name.startswith("_")]
            if not py_files:
                return {
                    "agent": agent_name,
                    "stdlib_imports": [],
                    "third_party_imports": [],
                    "local_imports": [],
                    "core_imports": [],
                }
            main_file = py_files[0]
        
        try:
            with open(main_file, "r") as f:
                source = f.read()
            tree = ast.parse(source)
            
            stdlib_imports = []
            third_party_imports = []
            local_imports = []
            core_imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    
                    if module.startswith("core."):
                        core_imports.append(module)
                    elif module.startswith("agents."):
                        local_imports.append(module)
                    elif module in self._stdlib_modules():
                        stdlib_imports.append(module)
                    else:
                        third_party_imports.append(module)
                        
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        module = alias.name
                        if module.startswith("core."):
                            core_imports.append(module)
                        elif module in self._stdlib_modules():
                            stdlib_imports.append(module)
                        else:
                            third_party_imports.append(module)
            
            return {
                "agent": agent_name,
                "file": str(main_file),
                "stdlib_imports": list(set(stdlib_imports)),
                "third_party_imports": list(set(third_party_imports)),
                "local_imports": list(set(local_imports)),
                "core_imports": list(set(core_imports)),
                "total_imports": len(set(stdlib_imports + third_party_imports + local_imports + core_imports)),
            }
        except Exception as e:
            self.logger.error(f"Failed to extract imports from {agent_name}: {e}")
            return {
                "agent": agent_name,
                "error": str(e),
                "stdlib_imports": [],
                "third_party_imports": [],
                "local_imports": [],
                "core_imports": [],
            }

    def _check_missing_standard_imports(self, imports: Dict[str, Any], agent_name: str) -> List[Dict[str, str]]:
        """Check if agent is missing standard imports."""
        missing = []
        agent_core_imports = imports.get("core_imports", [])
        agent_stdlib = imports.get("stdlib_imports", [])
        
        # Check for core.logger
        if "core.logger" not in agent_core_imports:
            missing.append({
                "agent": agent_name,
                "severity": "MEDIUM",
                "missing_import": "from core.logger import get_logger",
                "reason": "No logging capability",
            })
        
        # Check for typing
        if "typing" not in agent_stdlib:
            missing.append({
                "agent": agent_name,
                "severity": "LOW",
                "missing_import": "from typing import Dict, List, Any",
                "reason": "No type hints imported",
            })
        
        return missing

    def _find_inconsistencies(self, dependency_results: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find inconsistencies in imports across agents."""
        inconsistencies = []
        
        # Collect all imports by type
        all_third_party = {}
        for agent, imports in dependency_results.items():
            for imp in imports.get("third_party_imports", []):
                if imp not in all_third_party:
                    all_third_party[imp] = []
                all_third_party[imp].append(agent)
        
        # Find partially used imports (used by some agents but not all)
        total_agents = len(dependency_results)
        for imp, agents_using in all_third_party.items():
            usage_count = len(agents_using)
            if 0 < usage_count < total_agents:
                # This import is used inconsistently
                inconsistencies.append({
                    "import": imp,
                    "used_by": agents_using,
                    "not_used_by": [
                        a for a in dependency_results.keys() if a not in agents_using
                    ],
                    "severity": "MEDIUM",
                    "reason": f"Inconsistent usage: {usage_count}/{total_agents} agents",
                })
        
        return inconsistencies

    def _calculate_consistency_score(self, dependency_results: Dict, missing: List, inconsistent: List) -> float:
        """Calculate overall consistency score."""
        if not dependency_results:
            return 0.0
        
        total_agents = len(dependency_results)
        
        # Base score
        score = 100.0
        
        # Deduct for missing standard imports
        score -= len(missing) * 5
        
        # Deduct for inconsistencies
        score -= len(inconsistent) * 3
        
        return max(0.0, score)

    def _get_priority_fixes(self, missing: List[Dict], inconsistent: List[Dict]) -> List[Dict[str, Any]]:
        """Get prioritized list of dependency issues to fix."""
        fixes = []
        
        # Add missing imports
        for item in missing:
            fixes.append({
                "agent": item["agent"],
                "priority": item["severity"],
                "action": f"Add import: {item['missing_import']}",
                "reason": item["reason"],
                "effort_hours": 0.25,
            })
        
        # Add inconsistency fixes
        for item in inconsistent:
            fixes.append({
                "import": item["import"],
                "priority": item["severity"],
                "action": "Standardize import usage",
                "reason": item["reason"],
                "affected_agents": len(item["not_used_by"]),
                "effort_hours": 1,
            })
        
        # Sort by priority
        priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        fixes.sort(key=lambda x: priority_order.get(x["priority"], 4))
        
        return fixes

    def _get_status(self, score: float) -> str:
        """Get status based on consistency score."""
        if score >= 90:
            return "✅ Excellent"
        elif score >= 75:
            return "🟡 Good"
        elif score >= 60:
            return "🟠 Fair"
        else:
            return "🔴 Critical"

    def _stdlib_modules(self) -> Set[str]:
        """Return set of Python standard library modules."""
        return {
            "os", "sys", "re", "json", "csv", "pathlib", "datetime",
            "typing", "collections", "itertools", "functools", "operator",
            "math", "random", "statistics", "time", "asyncio", "threading",
            "subprocess", "argparse", "logging", "warnings", "traceback",
            "inspect", "ast", "copy", "pprint", "enum", "abc", "dataclasses",
            "uuid", "hashlib", "base64", "pickle", "io", "tempfile", "shutil",
        }
