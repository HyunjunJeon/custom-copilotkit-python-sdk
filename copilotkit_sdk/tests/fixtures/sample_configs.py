"""
Sample RunnableConfig objects for testing

Provides sample configuration objects used in LangGraph execution.
"""
from langchain_core.runnables import RunnableConfig


def get_basic_config() -> RunnableConfig:
    """Basic RunnableConfig with thread_id"""
    return {
        "configurable": {
            "thread_id": "test-thread-123"
        }
    }


def get_config_with_checkpoint() -> RunnableConfig:
    """Config with checkpoint information"""
    return {
        "configurable": {
            "thread_id": "test-thread-456",
            "checkpoint_id": "checkpoint-abc",
            "checkpoint_ns": ""
        }
    }


def get_config_with_metadata() -> RunnableConfig:
    """Config with CopilotKit metadata"""
    return {
        "configurable": {
            "thread_id": "test-thread-789"
        },
        "metadata": {
            "copilotkit:emit-messages": True,
            "copilotkit:emit-tool-calls": True,
            "copilotkit:emit-state": True,
            "copilotkit:agent-name": "test_agent",
            "copilotkit:run-id": "run-xyz-123"
        }
    }


def get_config_with_callbacks() -> RunnableConfig:
    """Config with callbacks"""
    return {
        "configurable": {
            "thread_id": "test-thread-callback"
        },
        "callbacks": [],
        "tags": ["test", "copilotkit"],
        "metadata": {
            "test": True
        }
    }


def get_multiple_thread_configs():
    """Get multiple configs with different thread IDs"""
    return [
        {
            "configurable": {
                "thread_id": f"thread-{i}"
            }
        }
        for i in range(5)
    ]


def get_config_for_agent_state_test() -> RunnableConfig:
    """Config specifically for agent state tests"""
    return {
        "configurable": {
            "thread_id": "state-test-thread",
            "checkpoint_id": None
        },
        "metadata": {
            "copilotkit:emit-state": True,
            "copilotkit:state-render": "full"
        }
    }


def get_config_for_interrupt_test() -> RunnableConfig:
    """Config for testing interrupt/resume functionality"""
    return {
        "configurable": {
            "thread_id": "interrupt-test-thread"
        },
        "metadata": {
            "copilotkit:handle-interrupts": True,
            "copilotkit:interrupt-mode": "user-input"
        }
    }


def get_config_for_streaming_test() -> RunnableConfig:
    """Config for streaming event tests"""
    return {
        "configurable": {
            "thread_id": "stream-test-thread"
        },
        "metadata": {
            "copilotkit:stream-events": True,
            "copilotkit:stream-version": "v2"
        }
    }
