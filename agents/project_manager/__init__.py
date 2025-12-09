"""ProjectManager Agent - Self-aware project coordinator.

Features:
- Auto-discovers project structure
- Learns patterns from existing code
- Validates new agents automatically
- Tracks changes and health
- Zero maintenance - grows with project
"""

from .project_manager import ProjectManager

__all__ = ['ProjectManager']
