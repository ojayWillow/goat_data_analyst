"""CodeAnalyzer Worker - Deep code inspection using AST.

Analyzes:
- Method signatures and expected patterns
- Type hints coverage
- Docstring quality
- Code complexity metrics
- Potential issues
"""

import ast
from pathlib import Path
from typing import Dict, List, Set, Any, Tuple

from core.logger import get_logger


class CodeAnalyzer:
    """Analyzes code using AST for deep insights."""

    def __init__(self, logger=None):
        self.logger = logger or get_logger("CodeAnalyzer")
        self.project_root = Path(__file__).parent.parent.parent.parent

    def analyze_agent(self, agent_path: Path) -> Dict[str, Any]:
        """Analyze an agent's code structure."""
        main_file = agent_path / f"{agent_path.name}.py"
        if not main_file.exists():
            # Try first .py file
            py_files = [f for f in agent_path.glob("*.py") if not f.name.startswith("_")]
            if not py_files:
                return self._empty_analysis()
            main_file = py_files[0]

        try:
            with open(main_file, "r") as f:
                source = f.read()
            tree = ast.parse(source)
            
            return {
                "main_file": str(main_file),
                "classes": self._extract_classes(tree),
                "functions": self._extract_functions(tree),
                "methods": self._extract_methods(tree),
                "type_hints_coverage": self._calculate_type_hints(tree),
                "docstring_coverage": self._calculate_docstrings(tree),
                "imports": self._extract_imports(tree),
                "complexity_score": self._calculate_complexity(tree),
                "issues": self._detect_issues(tree),
            }
        except Exception as e:
            self.logger.error(f"Failed to analyze {main_file}: {e}")
            return self._empty_analysis()

    def analyze_workers(self, agent_path: Path) -> Dict[str, Dict[str, Any]]:
        """Analyze all worker files in an agent."""
        workers = {}
        workers_dir = agent_path / "workers"
        
        if not workers_dir.exists():
            return workers

        for worker_file in workers_dir.glob("*.py"):
            if worker_file.name.startswith("_"):
                continue
            
            worker_name = worker_file.stem
            workers[worker_name] = self.analyze_code_file(worker_file)

        return workers

    def analyze_code_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a single Python file."""
        try:
            with open(file_path, "r") as f:
                source = f.read()
            tree = ast.parse(source)
            
            return {
                "file": str(file_path),
                "classes": self._extract_classes(tree),
                "functions": self._extract_functions(tree),
                "methods": self._extract_methods(tree),
                "type_hints_coverage": self._calculate_type_hints(tree),
                "docstring_coverage": self._calculate_docstrings(tree),
                "lines_of_code": len(source.split("\n")),
            }
        except Exception as e:
            self.logger.error(f"Failed to analyze {file_path}: {e}")
            return self._empty_analysis()

    def _extract_classes(self, tree: ast.AST) -> List[str]:
        """Extract class names from AST."""
        return [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]

    def _extract_functions(self, tree: ast.AST) -> List[str]:
        """Extract top-level function names."""
        return [
            node.name for node in tree.body
            if isinstance(node, ast.FunctionDef)
        ]

    def _extract_methods(self, tree: ast.AST) -> Dict[str, List[str]]:
        """Extract methods for each class."""
        methods = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods[node.name] = [
                    m.name for m in node.body
                    if isinstance(m, ast.FunctionDef)
                ]
        return methods

    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract all imports."""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        return list(set(imports))

    def _calculate_type_hints(self, tree: ast.AST) -> float:
        """Calculate percentage of functions with type hints."""
        functions = []
        has_hints = 0
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node)
                # Check if has return annotation or arg annotations
                if node.returns or any(arg.annotation for arg in node.args.args):
                    has_hints += 1
        
        return (has_hints / len(functions) * 100) if functions else 0.0

    def _calculate_docstrings(self, tree: ast.AST) -> float:
        """Calculate percentage of functions with docstrings."""
        functions = []
        has_docstring = 0
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                functions.append(node)
                if ast.get_docstring(node):
                    has_docstring += 1
        
        return (has_docstring / len(functions) * 100) if functions else 0.0

    def _calculate_complexity(self, tree: ast.AST) -> float:
        """Calculate cyclomatic complexity estimate (0-10 scale)."""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
                complexity += 1
        
        # Normalize to 0-10 scale
        return min(10.0, complexity / 2)

    def _detect_issues(self, tree: ast.AST) -> List[str]:
        """Detect potential code issues."""
        issues = []
        
        # Check for empty methods
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                    issues.append(f"Empty {type(node).__name__.lower()}: {node.name}")
        
        return issues

    def _empty_analysis(self) -> Dict[str, Any]:
        """Return empty analysis result."""
        return {
            "classes": [],
            "functions": [],
            "methods": {},
            "type_hints_coverage": 0.0,
            "docstring_coverage": 0.0,
            "imports": [],
            "complexity_score": 0.0,
            "issues": [],
        }
