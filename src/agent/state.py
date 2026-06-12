"""LangGraph agent state schema for the NovaTech support agent.

This module defines the complete shape of the state object that flows through
every LangGraph node and edge in the agent workflow.
"""

from __future__ import annotations

# Standard library imports for typing and reducer behavior.
from typing import Annotated, List, TypedDict
import operator

# LangChain message types for chat history and tool interactions.
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """State container passed between all LangGraph nodes.

    Each field represents a piece of shared state required by the agent workflow.
    """

    # Raw user input for the current turn.
    user_message: str
    # Unique user identifier for memory retrieval and storage.
    user_id: str
    # Conversation messages for the current reasoning cycle.
    messages: Annotated[List[BaseMessage], operator.add]
    # Memory context loaded from Supabase for this user.
    memory_context: str
    # Retrieved RAG context (formatted string of top-K chunks).
    retrieved_context: str
    # Final answer produced by the agent.
    final_answer: str
    # Flag indicating if a tool call was issued by the LLM.
    tool_called: bool


__all__ = ["AgentState"]
