"""
pytest configuration and shared fixtures

This file provides common fixtures used across all tests.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from langgraph.graph.state import CompiledStateGraph
from langchain_core.messages import HumanMessage, AIMessage

# Import fixture modules
from tests.fixtures.sample_actions import (
    create_simple_action,
    create_action_with_parameters,
    create_async_action,
    get_all_sample_actions
)
from tests.fixtures.sample_messages import (
    get_sample_human_message,
    get_sample_ai_message,
    get_sample_ai_message_with_tool_calls,
    get_sample_tool_message,
    get_sample_message_sequence,
    get_sample_copilotkit_text_message,
    get_sample_copilotkit_message_sequence
)
from tests.fixtures.sample_graphs import (
    create_simple_graph,
    create_messages_state_graph,
    get_initial_simple_state,
    get_initial_messages_state
)
from tests.fixtures.sample_configs import (
    get_basic_config,
    get_config_with_metadata,
    get_config_for_streaming_test
)


# ===== Action Fixtures =====

@pytest.fixture
def simple_action():
    """Simple action without parameters"""
    return create_simple_action()


@pytest.fixture
def action_with_params():
    """Action with required and optional parameters"""
    return create_action_with_parameters()


@pytest.fixture
def async_action():
    """Action with async handler"""
    return create_async_action()


@pytest.fixture
def sample_actions_list():
    """List of all sample actions"""
    return get_all_sample_actions()


# ===== Message Fixtures =====

@pytest.fixture
def human_message():
    """Sample human message"""
    return get_sample_human_message()


@pytest.fixture
def ai_message():
    """Sample AI message"""
    return get_sample_ai_message()


@pytest.fixture
def ai_message_with_tools():
    """AI message with tool calls"""
    return get_sample_ai_message_with_tool_calls()


@pytest.fixture
def tool_message():
    """Sample tool message"""
    return get_sample_tool_message()


@pytest.fixture
def message_sequence():
    """Full conversation message sequence"""
    return get_sample_message_sequence()


@pytest.fixture
def copilotkit_text_message():
    """CopilotKit text message"""
    return get_sample_copilotkit_text_message()


@pytest.fixture
def copilotkit_message_sequence():
    """CopilotKit message sequence"""
    return get_sample_copilotkit_message_sequence()


# ===== Graph Fixtures =====

@pytest.fixture
def simple_graph():
    """Simple compiled LangGraph graph"""
    return create_simple_graph()


@pytest.fixture
def messages_state_graph():
    """Graph using MessagesState"""
    return create_messages_state_graph()


@pytest.fixture
def initial_simple_state():
    """Initial state for simple graph"""
    return get_initial_simple_state()


@pytest.fixture
def initial_messages_state():
    """Initial state for messages graph"""
    return get_initial_messages_state()


# ===== Config Fixtures =====

@pytest.fixture
def basic_config():
    """Basic RunnableConfig"""
    return get_basic_config()


@pytest.fixture
def config_with_metadata():
    """Config with CopilotKit metadata"""
    return get_config_with_metadata()


@pytest.fixture
def streaming_config():
    """Config for streaming tests"""
    return get_config_for_streaming_test()


# ===== Mock Fixtures =====

@pytest.fixture
def mock_compiled_graph():
    """Mock CompiledStateGraph for testing"""
    mock_graph = MagicMock(spec=CompiledStateGraph)

    # Mock astream_events
    async def mock_astream_events(*args, **kwargs):
        """Mock event stream"""
        yield {
            "event": "on_chat_model_stream",
            "data": {"chunk": {"content": "test"}},
            "metadata": {}
        }
        yield {
            "event": "on_chain_end",
            "data": {"output": {"messages": [AIMessage(content="Done")]}},
            "metadata": {}
        }

    mock_graph.astream_events = AsyncMock(side_effect=mock_astream_events)

    # Mock aget_state
    async def mock_aget_state(*args, **kwargs):
        """Mock state getter"""
        return MagicMock(
            values={"messages": [HumanMessage(content="test")], "counter": 1},
            config={"configurable": {"thread_id": "test"}}
        )

    mock_graph.aget_state = AsyncMock(side_effect=mock_aget_state)

    # Mock aupdate_state
    async def mock_aupdate_state(*args, **kwargs):
        """Mock state updater"""
        return {"configurable": {"thread_id": "test"}}

    mock_graph.aupdate_state = AsyncMock(side_effect=mock_aupdate_state)

    # Mock schema methods
    mock_graph.get_input_jsonschema = MagicMock(return_value={
        "title": "InputSchema",
        "properties": {"messages": {"type": "array"}}
    })
    mock_graph.get_output_jsonschema = MagicMock(return_value={
        "title": "OutputSchema",
        "properties": {"messages": {"type": "array"}}
    })
    mock_graph.config_schema = MagicMock(return_value={
        "title": "ConfigSchema",
        "properties": {"thread_id": {"type": "string"}}
    })

    return mock_graph


@pytest.fixture
def mock_state():
    """Mock state object"""
    return {
        "messages": [
            HumanMessage(content="Hello", id="msg-1"),
            AIMessage(content="Hi there", id="msg-2")
        ],
        "counter": 2
    }


# ===== SDK Fixtures =====

@pytest.fixture
def sdk_with_actions(sample_actions_list):
    """CopilotKitSDK with sample actions"""
    from copilotkit import CopilotKitSDK
    return CopilotKitSDK(actions=sample_actions_list)


@pytest.fixture
def sdk_with_agent(simple_graph):
    """CopilotKitSDK with a LangGraph agent"""
    from copilotkit import CopilotKitSDK, LangGraphAgent

    agent = LangGraphAgent(
        name="test_agent",
        description="A test agent",
        graph=simple_graph
    )

    return CopilotKitSDK(agents=[agent])


# ===== Pytest Hooks =====

def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "v1_compat: LangGraph v1.0 호환성 테스트"
    )
    config.addinivalue_line(
        "markers", "unit: 단위 테스트"
    )
    config.addinivalue_line(
        "markers", "integration: 통합 테스트"
    )
    config.addinivalue_line(
        "markers", "slow: 느린 테스트"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection"""
    for item in items:
        # Auto-mark tests in test_langgraph_v1_compatibility/
        if "test_langgraph_v1_compatibility" in str(item.fspath):
            item.add_marker(pytest.mark.v1_compat)
            item.add_marker(pytest.mark.unit)

        # Auto-mark integration tests
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)


# ===== Helper Functions =====

def assert_message_has_content(message, expected_content: str):
    """Helper to assert message content"""
    assert hasattr(message, "content")
    assert expected_content in message.content


def assert_tool_call_exists(message, tool_name: str):
    """Helper to assert tool call exists"""
    assert hasattr(message, "tool_calls")
    assert any(tc["name"] == tool_name for tc in message.tool_calls)
