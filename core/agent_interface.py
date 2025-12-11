"""Standard Agent Interface - All agents must follow this.

Ensures contract compliance across all agents.
Use as parent class or reference for implementation.
"""

from typing import Any, Dict, Optional
from abc import ABC, abstractmethod


class AgentInterface(ABC):
    """Standard interface all agents must implement."""
    
    def __init__(self) -> None:
        """Initialize agent."""
        self.name: str = "Agent"
        self.data: Any = None
    
    # ===== STANDARDIZED METHODS (REQUIRED) =====
    
    def set_data(self, data: Any) -> None:
        """Set data for agent to process.
        
        Args:
            data: Input data (DataFrame, dict, etc.)
        """
        self.data = data
    
    def get_data(self) -> Optional[Any]:
        """Get current data.
        
        Returns:
            Current data or None
        """
        return self.data
    
    def get_summary(self) -> str:
        """Get human-readable summary.
        
        Returns:
            Summary string
        """
        return f"{self.name} Summary: No data" if self.data is None else f"{self.name} Summary: Ready"
    
    # ===== STANDARDIZED RESPONSE FORMAT =====
    
    @staticmethod
    def success_response(data: Any, message: str = "Success", metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create standardized success response.
        
        Args:
            data: Result data
            message: Success message
            metadata: Additional metadata
            
        Returns:
            {status: 'success', data: data, message: message, metadata: metadata}
        """
        return {
            'status': 'success',
            'data': data,
            'message': message,
            'metadata': metadata or {}
        }
    
    @staticmethod
    def error_response(message: str, error_type: str = "error", metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create standardized error response.
        
        Args:
            message: Error message
            error_type: Type of error
            metadata: Additional metadata
            
        Returns:
            {status: 'error', data: None, message: message, error_type: error_type}
        """
        return {
            'status': 'error',
            'data': None,
            'message': message,
            'error_type': error_type,
            'metadata': metadata or {}
        }
    
    @staticmethod
    def partial_response(data: Any, message: str = "Partial results", completed: int = 0, total: int = 0) -> Dict[str, Any]:
        """Create standardized partial response (for incomplete operations).
        
        Args:
            data: Partial result data
            message: Status message
            completed: Number of completed items
            total: Total items
            
        Returns:
            Partial response dict
        """
        return {
            'status': 'partial',
            'data': data,
            'message': message,
            'progress': {'completed': completed, 'total': total},
            'metadata': {}
        }
