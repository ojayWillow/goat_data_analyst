"""Cleaner Worker - Organizes project files into proper folders.

Automatically moves documentation, test outputs, and other files
into appropriate directories to keep project root clean.
"""

import shutil
from pathlib import Path
from typing import Dict, List, Any


class Cleaner:
    """Organizes project files into proper folders."""

    def __init__(self, logger, project_root: Path):
        self.logger = logger
        self.project_root = project_root
        self.moved_files = []
        self.errors = []

    def organize_files(self) -> Dict[str, Any]:
        """Organize all files in project root.
        
        Returns:
            Dict with files moved, errors, and summary
        """
        self.logger.info("Starting file organization...")
        
        # Define file organization rules
        rules = {
            "docs": {
                "patterns": [
                    "*_SUMMARY.md",
                    "SETUP_GUIDE.md",
                    "STEP*.md",
                    "PROJECT_MANAGER_GUIDE.md",
                ],
                "description": "Documentation files",
            },
            "logs": {
                "patterns": [
                    "*_output.txt",
                    "test_*.txt",
                ],
                "description": "Test output files",
            },
        }

        # Apply rules
        for folder_name, rule in rules.items():
            self._move_files(folder_name, rule["patterns"], rule["description"])

        # Summary
        summary = {
            "total_moved": len(self.moved_files),
            "moved_files": self.moved_files,
            "errors": self.errors,
            "status": "success" if not self.errors else "partial",
        }

        if self.moved_files:
            self.logger.info(f"Moved {len(self.moved_files)} files")
        if self.errors:
            self.logger.warning(f"Encountered {len(self.errors)} errors")

        return summary

    def _move_files(self, folder_name: str, patterns: List[str], description: str) -> None:
        """Move files matching patterns to folder.
        
        Args:
            folder_name: Target folder name (e.g., 'docs')
            patterns: List of glob patterns to match
            description: Human-readable description
        """
        # Create target folder
        target_folder = self.project_root / folder_name
        target_folder.mkdir(exist_ok=True)

        # Find and move files
        for pattern in patterns:
            for file_path in self.project_root.glob(pattern):
                # Skip if already in target folder
                if file_path.parent == target_folder:
                    continue

                # Skip if it's a directory
                if file_path.is_dir():
                    continue

                try:
                    dest = target_folder / file_path.name
                    shutil.move(str(file_path), str(dest))
                    self.moved_files.append(
                        {
                            "file": file_path.name,
                            "from": "root",
                            "to": folder_name,
                            "description": description,
                        }
                    )
                    self.logger.debug(f"Moved {file_path.name} to {folder_name}/")
                except Exception as e:
                    self.errors.append(
                        {
                            "file": file_path.name,
                            "error": str(e),
                        }
                    )
                    self.logger.error(f"Failed to move {file_path.name}: {e}")

    def get_summary(self) -> str:
        """Get human-readable summary of cleanup.
        
        Returns:
            Formatted summary string
        """
        if not self.moved_files and not self.errors:
            return "No files to organize."

        summary = f"Organized {len(self.moved_files)} files:\n"
        for item in self.moved_files:
            summary += f"  - {item['file']} -> {item['to']}/\n"

        if self.errors:
            summary += f"\nErrors: {len(self.errors)}\n"
            for error in self.errors:
                summary += f"  - {error['file']}: {error['error']}\n"

        return summary
