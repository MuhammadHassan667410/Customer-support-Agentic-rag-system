"""LangGraph assembly for the NovaTech support agent workflow.

This module wires the agent nodes into a StateGraph and exposes a convenience
invoke function for running the compiled graph.
"""

from __future__ import annotations

# Standard library imports for logging.
import logging

# LangGraph core primitives for graph construction.
from langgraph.graph import END, START, StateGraph

# Agent state schema and node functions.
from src.agent.state import AgentState
from src.agent.nodes import (
    agent_reasoning_node,
    rag_tool_node,
    retrieve_memory_node,
    write_cache_node,
    write_memory_node,
)

# Configuration for loop-guard recursion limit.
from src.config import GRAPH_RECURSION_LIMIT

# Module-level logger for consistent, centralized output.
LOGGER = logging.getLogger(__name__)

# Node name constants to avoid typos in edge wiring.
_NODE_RETRIEVE_MEMORY = "retrieve_memory"
_NODE_REASON = "agent_reasoning"
_NODE_RAG_TOOL = "rag_tool"
_NODE_WRITE_MEMORY = "write_memory"
_NODE_WRITE_CACHE = "write_cache"


def _route_after_reasoning(state: AgentState) -> str:
    """Route to the next node based on whether a tool was called.

    Args:
        state: The current AgentState after the reasoning node.

    Returns:
        The next node name for the graph to execute.
    """
    if state.get("tool_called"):
        return _NODE_RAG_TOOL
    return _NODE_WRITE_MEMORY


def build_graph() -> StateGraph:
    """Construct and return the LangGraph StateGraph for the agent.

    Returns:
        A StateGraph object configured with nodes and edges.
    """
    graph = StateGraph(AgentState)

    # Register all nodes with descriptive names.
    graph.add_node(_NODE_RETRIEVE_MEMORY, retrieve_memory_node)
    graph.add_node(_NODE_REASON, agent_reasoning_node)
    graph.add_node(_NODE_RAG_TOOL, rag_tool_node)
    graph.add_node(_NODE_WRITE_MEMORY, write_memory_node)
    graph.add_node(_NODE_WRITE_CACHE, write_cache_node)

    # Entry edge: start -> retrieve memory.
    graph.add_edge(START, _NODE_RETRIEVE_MEMORY)

    # Memory -> reasoning.
    graph.add_edge(_NODE_RETRIEVE_MEMORY, _NODE_REASON)

    # Conditional routing after reasoning.
    graph.add_conditional_edges(
        _NODE_REASON,
        _route_after_reasoning,
        path_map=[_NODE_RAG_TOOL, _NODE_WRITE_MEMORY],
    )

    # Tool -> reasoning loop for RAG retrieval.
    graph.add_edge(_NODE_RAG_TOOL, _NODE_REASON)

    # Finalization: write memory -> write cache -> end.
    graph.add_edge(_NODE_WRITE_MEMORY, _NODE_WRITE_CACHE)
    graph.add_edge(_NODE_WRITE_CACHE, END)

    return graph


def invoke_agent(user_message: str, user_id: str) -> str:
    """Run the compiled graph with initial state and return final answer.

    Args:
        user_message: The user's raw message for this turn.
        user_id: Unique identifier for the user.

    Returns:
        The final assistant response string.
    """
    compiled_graph = build_graph().compile()

    initial_state: AgentState = {
        "user_message": user_message,
        "user_id": user_id,
        "messages": [],
        "memory_context": "",
        "retrieved_context": "",
        "final_answer": "",
        "tool_called": False,
    }

    result_state = compiled_graph.invoke(
        initial_state,
        {"recursion_limit": GRAPH_RECURSION_LIMIT},
    )
    final_answer = result_state.get("final_answer", "")

    if not final_answer:
        LOGGER.warning("Graph invocation returned empty final_answer.")

    return final_answer


__all__ = ["build_graph", "invoke_agent"]
