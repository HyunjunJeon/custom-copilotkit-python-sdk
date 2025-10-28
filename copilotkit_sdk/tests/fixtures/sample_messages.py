"""
Sample messages for testing LangGraph v1.0 compatibility

Provides sample LangChain messages and CopilotKit messages for testing.
"""
from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    ToolMessage,
    SystemMessage,
)


def get_sample_human_message():
    """Simple human message"""
    return HumanMessage(
        content="Hello, I need help with a search",
        id="msg-human-1"
    )


def get_sample_ai_message():
    """AI message without tool calls"""
    return AIMessage(
        content="Sure, I can help you with that. What would you like to search for?",
        id="msg-ai-1"
    )


def get_sample_ai_message_with_tool_calls():
    """AI message with tool calls"""
    return AIMessage(
        content="I'll search the database for you",
        id="msg-ai-2",
        tool_calls=[
            {
                "id": "call-123",
                "name": "search_database",
                "args": {"query": "test query"}
            }
        ]
    )


def get_sample_tool_message():
    """Tool response message"""
    return ToolMessage(
        content='{"results": ["result1", "result2"]}',
        tool_call_id="call-123",
        id="msg-tool-1"
    )


def get_sample_system_message():
    """System message"""
    return SystemMessage(
        content="You are a helpful assistant",
        id="msg-system-1"
    )


def get_sample_message_sequence():
    """Full conversation sequence"""
    return [
        get_sample_system_message(),
        get_sample_human_message(),
        get_sample_ai_message_with_tool_calls(),
        get_sample_tool_message(),
        AIMessage(
            content="Based on the search results, here's what I found...",
            id="msg-ai-3"
        )
    ]


# CopilotKit message samples
def get_sample_copilotkit_text_message():
    """CopilotKit text message"""
    return {
        "id": "ck-msg-1",
        "role": "user",
        "content": "Hello, I need help",
    }


def get_sample_copilotkit_action_message():
    """CopilotKit action execution message"""
    return {
        "id": "ck-action-1",
        "role": "assistant",
        "name": "search_database",
        "arguments": {"query": "test"},
        "scope": "global"
    }


def get_sample_copilotkit_result_message():
    """CopilotKit action result message"""
    return {
        "id": "ck-result-1",
        "role": "function",
        "name": "search_database",
        "content": '{"results": ["result1", "result2"]}',
        "isError": False
    }


def get_sample_copilotkit_message_sequence():
    """CopilotKit message sequence"""
    return [
        get_sample_copilotkit_text_message(),
        get_sample_copilotkit_action_message(),
        get_sample_copilotkit_result_message(),
    ]
