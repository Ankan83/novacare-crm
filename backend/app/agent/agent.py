"""
Nova Agent

Creates the LangGraph ReAct agent.
"""

from langgraph.prebuilt import create_react_agent # type: ignore

from app.agent.system_prompt import SYSTEM_PROMPT
from app.agent.tools import TOOLS
from app.services.llm import llm


class NovaAgent:
    """
    Wrapper around the LangGraph ReAct agent.
    """

    def __init__(self):

        self.agent = create_react_agent(
            model=llm,
            tools=TOOLS,
            prompt=SYSTEM_PROMPT,
        )

    def invoke(
        self,
        *,
        state: dict,
    ) -> dict:
        """
        Execute Nova.

        Parameters
        ----------
        state
            ConversationState dictionary.

        Returns
        -------
        LangGraph state.
        """

        return self.agent.invoke(state)


nova_agent = NovaAgent()