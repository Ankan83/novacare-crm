"""
Nova Tool Executor

The LLM never executes tools directly.

Instead, it returns structured tool requests which are
executed safely here.
"""

from typing import Any

from app.tools.search_hcp import search_hcp
from app.tools.save_interaction import save_interaction
from app.database import SessionLocal # type: ignore


class ToolExecutor:
    """
    Executes approved Nova tools.
    """

    def __init__(self):
        self._tools = {
            "search_hcp": self._search_hcp,
            "save_interaction": self._save_interaction,
        }

    def execute(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Execute a registered tool.

        Returns:
            Tool result.
        """

        if tool_name not in self._tools:
            raise ValueError(f"Unknown tool: {tool_name}")

        return self._tools[tool_name](**arguments)

    # --------------------------------------------------
    # Internal Tool Wrappers
    # --------------------------------------------------

    def _search_hcp(
        self,
        doctor_name: str,
    ) -> dict[str, Any]:

        with SessionLocal() as db:

            return search_hcp(
                db=db,
                doctor_name=doctor_name,
            )

    def _save_interaction(
        self,
        draft: dict,
    ) -> dict[str, Any]:

        with SessionLocal() as db:

            return save_interaction(
                db=db,
                draft=draft,
            )


tool_executor = ToolExecutor()