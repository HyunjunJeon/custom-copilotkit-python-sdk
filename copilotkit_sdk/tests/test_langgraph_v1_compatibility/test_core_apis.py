"""
Test LangGraph v1.0 Core API Compatibility

Tests that verify the core LangGraph v1.0 APIs used by CopilotKit SDK
are working correctly.
"""
import pytest
from langgraph.graph import StateGraph, MessagesState
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import interrupt, Command


class TestMessagesStateCompatibility:
    """Test MessagesState inheritance and usage"""

    def test_messages_state_import(self):
        """Verify MessagesState can be imported"""
        assert MessagesState is not None

    def test_messages_state_with_state_graph(self):
        """Verify MessagesState can be used with StateGraph"""
        # This should work without errors in v1.0
        graph = StateGraph(MessagesState)
        assert graph is not None

    def test_copilotkit_state_inheritance(self):
        """Verify CopilotKitState can inherit from MessagesState"""
        from copilotkit.langgraph import CopilotKitState

        # Check that CopilotKitState has messages field
        assert "messages" in CopilotKitState.__annotations__

        # Should be able to create a graph with CopilotKitState
        graph = StateGraph(CopilotKitState)
        assert graph is not None


class TestCompiledGraphAPI:
    """Test CompiledStateGraph methods"""

    def test_compiled_graph_type(self, simple_graph):
        """Verify simple_graph is a CompiledStateGraph"""
        assert isinstance(simple_graph, CompiledStateGraph)

    @pytest.mark.asyncio
    async def test_astream_events_exists(self, simple_graph, initial_simple_state, basic_config):
        """Verify astream_events method exists and accepts version parameter"""
        # This is the key v1.0 streaming API
        assert hasattr(simple_graph, "astream_events")

        # Should accept version="v2" parameter
        event_count = 0
        async for event in simple_graph.astream_events(
            initial_simple_state,
            basic_config,
            version="v2"
        ):
            event_count += 1
            # Just verify events are coming through
            assert "event" in event

            if event_count >= 3:  # Limit to first few events
                break

        assert event_count > 0

    def test_aget_state_method_exists(self, simple_graph):
        """Verify aget_state method exists (requires checkpointer)"""
        # Just verify the method exists - actual usage requires checkpointer
        assert hasattr(simple_graph, "aget_state")
        assert callable(simple_graph.aget_state)

    def test_aupdate_state_method_exists(self, simple_graph):
        """Verify aupdate_state method exists (requires checkpointer)"""
        # Just verify the method exists - actual usage requires checkpointer
        assert hasattr(simple_graph, "aupdate_state")
        assert callable(simple_graph.aupdate_state)

    def test_schema_methods_exist(self, simple_graph):
        """Verify schema extraction methods exist"""
        assert hasattr(simple_graph, "get_input_jsonschema")
        assert hasattr(simple_graph, "get_output_jsonschema")
        assert hasattr(simple_graph, "config_schema")

        # Call them to ensure they work
        input_schema = simple_graph.get_input_jsonschema(None)
        assert input_schema is not None

        output_schema = simple_graph.get_output_jsonschema(None)
        assert output_schema is not None

        config_schema = simple_graph.config_schema()
        assert config_schema is not None


class TestInterruptAPI:
    """Test interrupt() function and Command pattern"""

    def test_interrupt_function_exists(self):
        """Verify interrupt() function can be imported"""
        assert interrupt is not None
        assert callable(interrupt)

    def test_command_class_exists(self):
        """Verify Command class can be imported"""
        assert Command is not None

    def test_command_creation_with_resume(self):
        """Verify Command can be created with resume parameter"""
        from langchain_core.messages import HumanMessage

        messages = [HumanMessage(content="test")]

        # This is the pattern used in CopilotKit SDK
        command = Command(resume=messages)

        assert command is not None
        assert hasattr(command, "resume")

    @pytest.mark.asyncio
    async def test_copilotkit_interrupt_usage(self):
        """Verify copilotkit_interrupt function works"""
        from copilotkit.langgraph import copilotkit_interrupt

        # This should not raise an error
        # (actual interrupt behavior is tested in interrupt_handling tests)
        assert copilotkit_interrupt is not None
        assert callable(copilotkit_interrupt)


class TestEnumSerialization:
    """Test that RuntimeEventTypes enum serializes correctly"""

    def test_runtime_event_types_enum(self):
        """Verify RuntimeEventTypes enum exists"""
        from copilotkit.protocol import RuntimeEventTypes

        assert RuntimeEventTypes is not None

    def test_enum_value_serialization(self):
        """Verify enum values are strings"""
        from copilotkit.protocol import RuntimeEventTypes

        # All enum values should be strings
        for event_type in RuntimeEventTypes:
            assert isinstance(event_type.value, str)

    def test_specific_event_types(self):
        """Verify specific event types exist"""
        from copilotkit.protocol import RuntimeEventTypes

        # Check some key event types
        assert hasattr(RuntimeEventTypes, "TEXT_MESSAGE_START")
        assert hasattr(RuntimeEventTypes, "ACTION_EXECUTION_START")
        assert hasattr(RuntimeEventTypes, "AGENT_STATE_MESSAGE")

        # Verify their string values
        assert RuntimeEventTypes.TEXT_MESSAGE_START.value == "TextMessageStart"
        assert RuntimeEventTypes.ACTION_EXECUTION_START.value == "ActionExecutionStart"
        assert RuntimeEventTypes.AGENT_STATE_MESSAGE.value == "AgentStateMessage"
