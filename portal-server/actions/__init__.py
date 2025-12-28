"""
Action registry and base classes for portal actions.
"""

from typing import Dict, Any, Optional
import logging

from actions.daily_note import DailyNoteAction

logger = logging.getLogger(__name__)


class ActionRegistry:
    """Registry for portal actions."""
    
    def __init__(self, repo_path: str):
        """
        Initialize the action registry.
        
        Args:
            repo_path: Path to the wintermute repository
        """
        self.repo_path = repo_path
        self.actions = {
            'open_daily': DailyNoteAction(repo_path),
        }
    
    async def execute(self, action_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an action.
        
        Args:
            action_name: Name of the action to execute
            data: Action parameters from the request
            
        Returns:
            Dictionary with 'success', 'message', and action-specific data
        """
        if action_name not in self.actions:
            logger.error(f"Unknown action: {action_name}")
            return {
                'success': False,
                'error': f'Unknown action: {action_name}',
                'message': f'Action {action_name} is not registered'
            }
        
        action = self.actions[action_name]
        
        try:
            result = await action.execute(data)
            return result
        except Exception as e:
            logger.exception(f"Error executing action {action_name}: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to execute action {action_name}'
            }

