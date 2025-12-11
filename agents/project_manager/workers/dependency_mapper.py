"""DependencyMapper Worker - Maps and analyzes project dependencies."""

from pathlib import Path
from typing import Dict, List, Any, Set
import ast

from core.logger import get_logger


class DependencyMapper:
    """Maps project dependencies and imports."""

    def __init__(self, logger=None):
        self.logger = logger or get_logger("DependencyMapper")
        self.project_root = Path(__file__).parent.parent.parent.parent

    def map_dependencies(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Map all project dependencies."""
        external_deps = set()
        internal_deps = {}
        
        agents = structure.get("agents", {})
        for agent_name, info in agents.items():
            agent_path = Path(info["path"])
            main_file = Path(info["main_file"])
            
            if main_file.exists():
                deps = self._extract_imports(main_file)
                internal_deps[agent_name] = deps
                external_deps.update(self._filter_external(deps))

        return {
            "external_dependencies": sorted(list(external_deps)),
            "internal_dependencies": internal_deps,
            "total_external": len(external_deps),
        }

    def _extract_imports(self, file_path: Path) -> List[str]:
        """Extract all imports from a file."""
        imports = []
        try:
            with open(file_path, "r") as f:
                tree = ast.parse(f.read())
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
        except:
            pass
        
        return list(set(imports))

    def _filter_external(self, imports: List[str]) -> Set[str]:
        """Filter to only external dependencies."""
        stdlib_modules = {
            'os', 'sys', 'pathlib', 'typing', 'json', 'datetime',
            'ast', 'shutil', 'abc', 'collections', 'functools',
            're', 'itertools', 'threading', 'subprocess', 'logging'
        }
        
        internal_modules = {'core', 'agents'}
        
        external = set()
        for imp in imports:
            base = imp.split(".")[0]
            if base not in stdlib_modules and base not in internal_modules:
                external.add(base)
        
        return external
