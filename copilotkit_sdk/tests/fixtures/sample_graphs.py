"""
Sample LangGraph graphs for testing

Provides mock LangGraph graphs and compiled graphs for testing LangGraph v1.0 compatibility.
"""
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, MessagesState
from langgraph.graph.state import CompiledStateGraph
from langchain_core.messages import HumanMessage, AIMessage


# Simple state for testing
class SimpleState(TypedDict):
    """Simple state with messages"""
    messages: Annotated[list, "messages"]
    counter: int


def create_simple_graph() -> CompiledStateGraph:
    """Create a simple LangGraph graph for testing

    Returns a compiled graph with basic nodes.
    """
    def node_1(state: SimpleState):
        """First node"""
        return {
            "messages": state["messages"] + [AIMessage(content="Node 1 response")],
            "counter": state.get("counter", 0) + 1
        }

    def node_2(state: SimpleState):
        """Second node"""
        return {
            "messages": state["messages"] + [AIMessage(content="Node 2 response")],
            "counter": state.get("counter", 0) + 1
        }

    # Create graph
    graph = StateGraph(SimpleState)
    graph.add_node("node_1", node_1)
    graph.add_node("node_2", node_2)

    graph.set_entry_point("node_1")
    graph.add_edge("node_1", "node_2")
    graph.set_finish_point("node_2")

    return graph.compile()


def create_messages_state_graph() -> CompiledStateGraph:
    """Create a graph using MessagesState

    Returns a compiled graph that uses the standard MessagesState.
    """
    def chat_node(state: MessagesState):
        """Chat node using MessagesState"""
        last_message = state["messages"][-1]
        return {
            "messages": [AIMessage(content=f"Response to: {last_message.content}")]
        }

    # Create graph
    graph = StateGraph(MessagesState)
    graph.add_node("chat", chat_node)

    graph.set_entry_point("chat")
    graph.set_finish_point("chat")

    return graph.compile()


def create_conditional_graph() -> CompiledStateGraph:
    """Create a graph with conditional edges

    Returns a compiled graph with branching logic.
    """
    class ConditionalState(TypedDict):
        messages: Annotated[list, "messages"]
        route: str

    def router_node(state: ConditionalState):
        """Node that determines routing"""
        last_message = state["messages"][-1]
        # Simple routing logic based on message content
        if "urgent" in last_message.content.lower():
            return {"route": "urgent"}
        return {"route": "normal"}

    def urgent_node(state: ConditionalState):
        """Handle urgent requests"""
        return {
            "messages": [AIMessage(content="Handling urgent request")]
        }

    def normal_node(state: ConditionalState):
        """Handle normal requests"""
        return {
            "messages": [AIMessage(content="Handling normal request")]
        }

    def should_route_urgent(state: ConditionalState):
        """Conditional edge function"""
        return state.get("route", "normal")

    # Create graph
    graph = StateGraph(ConditionalState)
    graph.add_node("router", router_node)
    graph.add_node("urgent", urgent_node)
    graph.add_node("normal", normal_node)

    graph.set_entry_point("router")
    graph.add_conditional_edges(
        "router",
        should_route_urgent,
        {
            "urgent": "urgent",
            "normal": "normal"
        }
    )
    graph.set_finish_point("urgent")
    graph.set_finish_point("normal")

    return graph.compile()


def create_graph_with_error() -> CompiledStateGraph:
    """Create a graph that raises an error for testing

    Returns a compiled graph that will fail during execution.
    """
    def error_node(state: SimpleState):
        """Node that raises an error"""
        raise ValueError("Intentional test error from graph node")

    # Create graph
    graph = StateGraph(SimpleState)
    graph.add_node("error", error_node)

    graph.set_entry_point("error")
    graph.set_finish_point("error")

    return graph.compile()


# Helper function to get initial state
def get_initial_simple_state() -> SimpleState:
    """Get initial state for SimpleState graph"""
    return {
        "messages": [HumanMessage(content="Hello")],
        "counter": 0
    }


def get_initial_messages_state() -> MessagesState:
    """Get initial state for MessagesState graph"""
    return {
        "messages": [HumanMessage(content="Test message")]
    }
