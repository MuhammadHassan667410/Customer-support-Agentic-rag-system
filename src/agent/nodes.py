"""LangGraph node implementations for the NovaTech support agent.

This module defines the individual node functions used in the LangGraph workflow.
Each node receives the shared AgentState and returns state updates.
"""

from __future__ import annotations

# Standard library import for logging.
import logging

# LangChain message types for prompt construction and responses.
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

# Azure OpenAI chat model integration from LangChain.
from langchain_openai import AzureChatOpenAI

# Shared state schema for LangGraph nodes.
from src.agent.state import AgentState

# RAG tool exposed to the model for knowledge base retrieval.
from src.retriever.rag_retriever import search_company_knowledge_base

# Semantic cache writer for storing Q/A pairs.
from src.cache.semantic_cache import write_to_cache

# Long-term memory access function for user-specific context.
from src.memory.long_term_memory import get_user_memory
from src.memory.long_term_memory import save_to_memory

# Configuration values required to initialize Azure chat model.
from src.config import (
    AZURE_CHAT_DEPLOYMENT_NAME,
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_API_VERSION,
    AZURE_OPENAI_ENDPOINT,
)

# Module-level logger for consistent, centralized output.
LOGGER = logging.getLogger(__name__)

# Default assistant system prompt used for all reasoning steps.
_SYSTEM_PROMPT_HEADER = "You are NovaTech Solutions' customer support assistant."

# Error response used when the LLM call fails unexpectedly.
_LLM_ERROR_MESSAGE = (
    "I'm sorry — I ran into an internal error while processing your request."
)

# Limit text length in logs to keep output readable.
_LOG_PREVIEW_LENGTH = 50


def _build_system_prompt(memory_context: str, retrieved_context: str) -> str:
    """Construct the system prompt from memory and retrieved context.

    Args:
        memory_context: Formatted memory summary text from long-term memory.
        retrieved_context: Formatted RAG context returned by the retrieval tool.

    Returns:
        A system prompt string that provides the LLM with relevant context.
    """
    prompt_sections = [_SYSTEM_PROMPT_HEADER]

    # Add memory context if it exists.
    if memory_context:
        prompt_sections.append(f"Memory context:\n{memory_context}")

    # Add retrieved context if available (typically after a tool call).
    if retrieved_context:
        prompt_sections.append(f"Retrieved context:\n{retrieved_context}")

    return "\n\n".join(prompt_sections)


def _prepare_messages_for_llm(state: AgentState) -> tuple[list[BaseMessage], list[BaseMessage]]:
    """Prepare the message list for LLM invocation and state updates.

    Args:
        state: The current AgentState containing messages and user input.

    Returns:
        A tuple of (messages_for_llm, messages_to_append_to_state).
    """
    existing_messages = list(state.get("messages", []))
    messages_to_append: list[BaseMessage] = []

    # If no messages exist yet, add the current user message.
    if not existing_messages:
        user_message = state.get("user_message", "").strip()
        if user_message:
            human_message = HumanMessage(content=user_message)
            existing_messages.append(human_message)
            messages_to_append.append(human_message)

    return existing_messages, messages_to_append


def retrieve_memory_node(state: AgentState) -> dict:
    """Load long-term memory for the current user and update the state.

    Args:
        state: The current AgentState containing user_id and other context.

    Returns:
        A partial state update dict containing the memory_context string.
    """
    # Extract the user identifier from the incoming state.
    user_id = state.get("user_id", "")

    try:
        # Load memory context from Supabase using the configured helper.
        memory_context = get_user_memory(user_id)
    except Exception as error:
        # Log unexpected errors and fall back to empty memory context.
        LOGGER.exception("Failed to retrieve memory for user '%s': %s", user_id, str(error))
        memory_context = ""

    # Return the partial state update expected by LangGraph.
    return {"memory_context": memory_context}


def agent_reasoning_node(state: AgentState) -> dict:
    """Run the LLM reasoning step with tool access and update messages.

    Args:
        state: The current AgentState containing messages and context.

    Returns:
        A partial state update dict containing new messages and tool flag.
    """
    memory_context = state.get("memory_context", "")
    retrieved_context = state.get("retrieved_context", "")

    # Build the system prompt from memory and retrieval context.
    system_prompt = _build_system_prompt(memory_context, retrieved_context)
    system_message = SystemMessage(content=system_prompt)

    # Prepare the conversation messages for the LLM call.
    messages_for_llm, messages_to_append = _prepare_messages_for_llm(state)

    # Initialize the Azure OpenAI chat model with tool binding.
    llm = AzureChatOpenAI(
        azure_deployment=AZURE_CHAT_DEPLOYMENT_NAME,
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
    )
    llm_with_tools = llm.bind_tools([search_company_knowledge_base])

    try:
        # Invoke the model with system + conversation messages.
        ai_message = llm_with_tools.invoke([system_message, *messages_for_llm])
    except Exception as error:
        LOGGER.exception("LLM reasoning failed: %s", str(error))
        ai_message = AIMessage(content=_LLM_ERROR_MESSAGE)

    # Log a short preview of the assistant response for debugging.
    LOGGER.info(
        "LLM responded with %d tool calls. Preview: %s",
        len(getattr(ai_message, "tool_calls", []) or []),
        ai_message.content[:_LOG_PREVIEW_LENGTH] if ai_message.content else "",
    )

    # Determine whether the LLM requested a tool call.
    tool_called = bool(getattr(ai_message, "tool_calls", None))

    # If the LLM did not call a tool, treat this as the final answer.
    final_answer = ""
    if not tool_called and ai_message.content:
        final_answer = ai_message.content

    # Append the AI response (and any added human message) to state.
    return {
        "messages": [*messages_to_append, ai_message],
        "tool_called": tool_called,
        "final_answer": final_answer,
    }


def rag_tool_node(state: AgentState) -> dict:
    """Execute the RAG tool call and append its output to messages.

    Args:
        state: The current AgentState containing messages and tool call info.

    Returns:
        A partial state update dict containing the tool message and retrieved context.
    """
    messages = state.get("messages", [])

    if not messages:
        LOGGER.warning("RAG tool node invoked with empty message list.")
        return {"retrieved_context": "", "messages": []}

    last_message = messages[-1]

    # Ensure the last message is an AIMessage with tool calls.
    if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
        LOGGER.warning("RAG tool node invoked without tool calls.")
        return {"retrieved_context": "", "messages": []}

    # Use the first tool call for retrieval (single-tool workflow).
    tool_call = last_message.tool_calls[0]
    tool_call_id = tool_call.get("id", "")
    tool_args = tool_call.get("args", {})

    # The tool expects a "query" argument containing the user question.
    query = tool_args.get("query", "").strip()
    if not query:
        LOGGER.warning("RAG tool call missing 'query' argument.")
        return {"retrieved_context": "", "messages": []}

    try:
        retrieved_context = search_company_knowledge_base.invoke({"query": query})
    except Exception as error:
        LOGGER.exception("RAG tool execution failed: %s", str(error))
        retrieved_context = ""

    tool_message = ToolMessage(
        content=retrieved_context,
        tool_call_id=tool_call_id,
    )

    return {
        "retrieved_context": retrieved_context,
        "messages": [tool_message],
    }


def write_memory_node(state: AgentState) -> dict:
    """Persist the latest conversation turn into long-term memory.

    Args:
        state: The current AgentState containing user_id and messages.

    Returns:
        An empty dict because this node only performs a side effect.
    """
    user_id = state.get("user_id", "")
    user_message = state.get("user_message", "")

    # Prefer the most recent AI message content as the final answer.
    final_answer = ""
    for message in reversed(state.get("messages", [])):
        if isinstance(message, AIMessage) and message.content:
            final_answer = message.content
            break

    if not final_answer:
        LOGGER.warning("Memory write skipped because final_answer was empty.")
        return {}

    # Avoid persisting fallback error responses to long-term memory.
    if final_answer.strip() == _LLM_ERROR_MESSAGE:
        LOGGER.warning("Memory write skipped because response was an error fallback.")
        return {}

    save_to_memory(user_id=user_id, user_message=user_message, agent_answer=final_answer)
    return {}


def write_cache_node(state: AgentState) -> dict:
    """Persist the latest question/answer into the semantic cache.

    Args:
        state: The current AgentState containing the user message and response.

    Returns:
        An empty dict because this node only performs a side effect.
    """
    user_message = state.get("user_message", "")

    # Prefer the most recent AI message content as the final answer.
    final_answer = ""
    for message in reversed(state.get("messages", [])):
        if isinstance(message, AIMessage) and message.content:
            final_answer = message.content
            break

    if not final_answer:
        LOGGER.warning("Cache write skipped because final_answer was empty.")
        return {}

    write_to_cache(question=user_message, answer=final_answer)
    return {}


__all__ = [
    "retrieve_memory_node",
    "agent_reasoning_node",
    "rag_tool_node",
    "write_memory_node",
    "write_cache_node",
]
