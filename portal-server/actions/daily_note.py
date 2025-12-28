"""
Daily note creation action.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import shutil
import re

logger = logging.getLogger(__name__)


class DailyNoteAction:
    """Action to create or open the daily note."""
    
    def __init__(self, repo_path: str):
        """
        Initialize the daily note action.
        
        Args:
            repo_path: Path to the wintermute repository
        """
        self.repo_path = Path(repo_path)
        self.template_path = self.repo_path / '0_admin' / '02_templates' / 'daily_note_2026.md'
        self.journal_path = self.repo_path / '1_life' / '13_journal'
    
    def _get_today_filename(self) -> str:
        """Get today's date in YYYY-MM-DD format."""
        return datetime.now().strftime('%Y-%m-%d')
    
    def _get_daily_note_path(self) -> Path:
        """Get the path to today's daily note."""
        date_str = self._get_today_filename()
        return self.journal_path / f'{date_str}.md'
    
    def _replace_placeholders(self, content: str, date_str: str) -> str:
        """
        Replace placeholders in template content.
        
        Args:
            content: Template content
            date_str: Date string in YYYY-MM-DD format
            
        Returns:
            Content with placeholders replaced
        """
        # Common placeholders
        replacements = {
            '{{date}}': date_str,
            '{{DATE}}': date_str,
            '{{title}}': date_str,
            '{{TITLE}}': date_str,
            # Format: Monday, January 1, 2025
            '{{date_long}}': datetime.now().strftime('%A, %B %d, %Y'),
            '{{DATE_LONG}}': datetime.now().strftime('%A, %B %d, %Y'),
            # Format: 2025-01-01
            '{{date_iso}}': date_str,
            '{{DATE_ISO}}': date_str,
        }
        
        result = content
        for placeholder, value in replacements.items():
            result = result.replace(placeholder, value)
        
        return result
    
    async def _ensure_template_exists(self) -> bool:
        """
        Verify that the template file exists.
        
        Returns:
            True if template exists, False otherwise
        """
        if not self.template_path.exists():
            logger.error(f"Daily note template not found: {self.template_path}")
            return False
        return True
    
    async def _create_daily_note(self) -> Dict[str, Any]:
        """
        Create today's daily note from template.
        
        Returns:
            Dictionary with success status and file path
        """
        date_str = self._get_today_filename()
        daily_note_path = self._get_daily_note_path()
        
        # Check if note already exists
        if daily_note_path.exists():
            logger.info(f"Daily note already exists: {daily_note_path}")
            return {
                'success': True,
                'message': f'Daily note already exists for {date_str}',
                'file_path': str(daily_note_path.relative_to(self.repo_path)),
                'created': False
            }
        
        # Ensure template exists
        if not await self._ensure_template_exists():
            return {
                'success': False,
                'error': 'Template not found',
                'message': f'Daily note template not found: {self.template_path}'
            }
        
        # Ensure journal directory exists
        self.journal_path.mkdir(parents=True, exist_ok=True)
        
        # Read template
        try:
            with open(self.template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
        except Exception as e:
            logger.error(f"Error reading template: {e}")
            return {
                'success': False,
                'error': 'Template read error',
                'message': f'Failed to read template: {e}'
            }
        
        # Replace placeholders
        content = self._replace_placeholders(template_content, date_str)
        
        # Write daily note
        try:
            with open(daily_note_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Created daily note: {daily_note_path}")
        except Exception as e:
            logger.error(f"Error writing daily note: {e}")
            return {
                'success': False,
                'error': 'File write error',
                'message': f'Failed to write daily note: {e}'
            }
        
        return {
            'success': True,
            'message': f'Created daily note for {date_str}',
            'file_path': str(daily_note_path.relative_to(self.repo_path)),
            'created': True
        }
    
    async def _git_add_commit_push(self, file_path: Path, commit_message: str) -> Dict[str, Any]:
        """
        Execute git add, commit, and push operations.
        
        Args:
            file_path: Path to the file to commit
            commit_message: Commit message
            
        Returns:
            Dictionary with success status
        """
        from config import Config
        
        repo_path = self.repo_path
        
        # Git commands to run
        commands = [
            # Add the file
            ['git', '-C', str(repo_path), 'add', str(file_path.relative_to(repo_path))],
            # Commit
            ['git', '-C', str(repo_path), 'commit', '-m', commit_message],
            # Push
            ['git', '-C', str(repo_path), 'push'],
        ]
        
        for cmd in commands:
            try:
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=str(repo_path)
                )
                
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    error_msg = stderr.decode('utf-8') if stderr else 'Unknown error'
                    logger.error(f"Git command failed: {' '.join(cmd)} - {error_msg}")
                    return {
                        'success': False,
                        'error': 'Git operation failed',
                        'message': f'Git command failed: {error_msg}',
                        'command': ' '.join(cmd)
                    }
                
                logger.debug(f"Git command succeeded: {' '.join(cmd)}")
                
            except Exception as e:
                logger.exception(f"Error executing git command: {' '.join(cmd)}")
                return {
                    'success': False,
                    'error': 'Git execution error',
                    'message': f'Failed to execute git command: {e}',
                    'command': ' '.join(cmd)
                }
        
        return {
            'success': True,
            'message': 'Git operations completed successfully'
        }
    
    async def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the daily note action.
        
        Args:
            data: Action parameters (may include portal_id, action, etc.)
            
        Returns:
            Dictionary with success status and file information
        """
        # Create the daily note
        result = await self._create_daily_note()
        
        if not result.get('success'):
            return result
        
        # If note was created, commit and push
        if result.get('created'):
            date_str = self._get_today_filename()
            daily_note_path = self._get_daily_note_path()
            commit_message = f'create daily note {date_str}'
            
            git_result = await self._git_add_commit_push(daily_note_path, commit_message)
            
            if not git_result.get('success'):
                # Note: We still return success for note creation, but include git error
                result['git_error'] = git_result.get('message')
                result['warning'] = 'Daily note created but git operations failed'
            else:
                result['git_success'] = True
        
        return result

