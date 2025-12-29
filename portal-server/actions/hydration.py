"""
Hydration tracking action.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple
import logging

import yaml

from actions.daily_note import DailyNoteAction

logger = logging.getLogger(__name__)


class HydrationAction:
    """Action to increment oz_water in the daily note frontmatter."""

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.daily_action = DailyNoteAction(repo_path)

    def _split_frontmatter(self, content: str) -> Tuple[Dict[str, Any], str]:
        """Split YAML frontmatter from content, returning (frontmatter, body)."""
        if not content.startswith("---"):
            return {}, content

        lines = content.splitlines(keepends=True)
        if not lines or lines[0].strip() != "---":
            return {}, content

        for index in range(1, len(lines)):
            if lines[index].strip() == "---":
                frontmatter_text = "".join(lines[1:index])
                body = "".join(lines[index + 1:])
                data = yaml.safe_load(frontmatter_text) or {}
                if not isinstance(data, dict):
                    data = {}
                return data, body

        return {}, content

    def _build_frontmatter(self, data: Dict[str, Any]) -> str:
        """Serialize YAML frontmatter."""
        yaml_text = yaml.safe_dump(
            data,
            sort_keys=False,
            default_flow_style=False,
        )
        return f"---\n{yaml_text}---\n"

    def _resolve_delta(self, payload: Dict[str, Any]) -> int:
        """Resolve the delta to add to oz_water."""
        delta = payload.get("delta")
        if delta is None:
            delta = payload.get("config", {}).get("delta")
        if delta is None:
            delta = 64
        try:
            return int(delta)
        except (TypeError, ValueError):
            return 64

    def _is_dry_run(self, payload: Dict[str, Any]) -> bool:
        """Check whether this request should skip file writes."""
        dry_run = payload.get("dry_run")
        if dry_run is None:
            dry_run = payload.get("config", {}).get("dry_run")
        return bool(dry_run)

    async def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Increment oz_water in today's daily note frontmatter."""
        daily_note_path = self.daily_action._get_daily_note_path()
        delta = self._resolve_delta(data)
        dry_run = self._is_dry_run(data)

        if not daily_note_path.exists():
            if dry_run:
                return {
                    "success": True,
                    "message": "Dry run: daily note not found",
                    "oz_water": None,
                    "exists": False,
                }
            create_result = await self.daily_action._create_daily_note()
            if not create_result.get("success"):
                return create_result

        try:
            content = daily_note_path.read_text(encoding="utf-8")
        except Exception as exc:
            logger.error("Failed to read daily note: %s", exc)
            return {
                "success": False,
                "error": "File read error",
                "message": f"Failed to read daily note: {exc}",
            }

        frontmatter, body = self._split_frontmatter(content)

        try:
            current = int(frontmatter.get("oz_water") or 0)
        except (TypeError, ValueError):
            current = 0

        next_value = current + delta
        frontmatter["oz_water"] = next_value

        if dry_run:
            return {
                "success": True,
                "message": "Dry run: no changes applied",
                "oz_water": current,
                "oz_water_next": next_value,
                "file_path": str(daily_note_path.relative_to(self.repo_path)),
                "gitea_url": self.daily_action._build_gitea_url(daily_note_path),
            }

        try:
            new_content = f"{self._build_frontmatter(frontmatter)}{body}"
            daily_note_path.write_text(new_content, encoding="utf-8")
        except Exception as exc:
            logger.error("Failed to write daily note: %s", exc)
            return {
                "success": False,
                "error": "File write error",
                "message": f"Failed to write daily note: {exc}",
            }

        commit_message = (
            f"add water {datetime.now().strftime('%Y-%m-%d')} +{delta}oz"
        )
        git_result = await self.daily_action._git_add_commit_push(
            daily_note_path,
            commit_message,
        )
        if not git_result.get("success"):
            result = {
                "success": True,
                "message": "Water added but git operations failed",
                "oz_water": frontmatter["oz_water"],
                "git_error": git_result.get("message"),
            }
        else:
            result = {
                "success": True,
                "message": f"Added {delta}oz of water",
                "oz_water": frontmatter["oz_water"],
                "git_success": True,
            }

        result["file_path"] = str(daily_note_path.relative_to(self.repo_path))
        result["working_copy_url"] = self.daily_action._build_working_copy_url(
            daily_note_path
        )
        result["obsidian_uri"] = self.daily_action._build_obsidian_uri(daily_note_path)
        result["gitea_url"] = self.daily_action._build_gitea_url(daily_note_path)

        return result
