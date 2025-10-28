"""
LangGraph/LangChain 통합 유틸리티

이 모듈은 CopilotKit과 LangGraph/LangChain 프레임워크를 연결하는 핵심 유틸리티를 제공합니다.
주요 기능은 메시지 형식 변환, 상태 관리, 이벤트 방출, 인터럽트 처리 등입니다.

LangGraph Agent를 사용할 때 가장 자주 사용되는 모듈로, 메시지 변환과 상태 동기화의
핵심 로직이 포함되어 있습니다.

주요 구성요소:
- CopilotKitState: LangGraph 상태 정의 (messages + copilotkit 필드)
- 메시지 변환 함수: CopilotKit ↔ LangChain 형식 변환
- 이벤트 방출 함수: 상태, 메시지, 도구 호출 이벤트 전송
- 인터럽트 처리: 사용자 입력 대기 및 재개

Message Conversion Flow:
```mermaid
graph LR
    subgraph "CopilotKit Format"
    A[TextMessage]
    B[ActionExecutionMessage]
    C[ResultMessage]
    end

    subgraph "Conversion Layer"
    D[copilotkit_messages_to_langchain]
    E[langchain_messages_to_copilotkit]
    end

    subgraph "LangChain Format"
    F[HumanMessage]
    G[SystemMessage]
    H[AIMessage]
    I[ToolMessage]
    end

    A -->|role: user| D
    A -->|role: assistant| D
    B -->|tool_calls or function_call| D
    C -->|tool result| D

    D --> F
    D --> G
    D --> H
    D --> I

    F --> E
    G --> E
    H --> E
    I --> E

    E --> A
    E --> B
    E --> C

    style D fill:#e1f5ff
    style E fill:#ffe1f5
```

Interrupt Handling Flow:
```mermaid
sequenceDiagram
    participant G as LangGraph Node
    participant I as copilotkit_interrupt
    participant C as Client
    participant R as Resume

    G->>I: copilotkit_interrupt(value)
    I->>I: interrupt(value)
    Note over I: LangGraph interrupts execution
    I-->>C: on_copilotkit_interrupt event

    Note over C: User provides input

    C->>R: POST /agent/name (with meta_events)
    R->>R: Detect LangGraphInterruptEvent
    R->>R: Command(resume=response)
    R->>G: Resume execution with user input

    G->>G: Continue processing
```

Event Emission Flow:
```mermaid
graph TD
    subgraph "Graph Execution"
    A[LangGraph Node]
    end

    subgraph "Event Emission Functions"
    B[copilotkit_emit_state]
    C[copilotkit_emit_message]
    D[copilotkit_emit_tool_call]
    E[copilotkit_exit]
    end

    subgraph "Event Dispatch"
    F[adispatch_custom_event]
    end

    subgraph "Client"
    G[Frontend]
    end

    A --> B
    A --> C
    A --> D
    A --> E

    B -->|copilotkit_manually_emit_intermediate_state| F
    C -->|copilotkit_manually_emit_message| F
    D -->|copilotkit_manually_emit_tool_call| F
    E -->|copilotkit_exit| F

    F --> G

    style B fill:#fff4e1
    style C fill:#fff4e1
    style D fill:#fff4e1
    style E fill:#ffe1e1
```

Key Functions:

1. 메시지 변환 (Message Conversion):
   - `copilotkit_messages_to_langchain()`: CopilotKit → LangChain
     - TextMessage → HumanMessage/AIMessage/SystemMessage
     - ActionExecutionMessage → AIMessage(tool_calls)
     - ResultMessage → ToolMessage
   - `langchain_messages_to_copilotkit()`: LangChain → CopilotKit
     - 역변환 수행
     - AI 모델별 메시지 형식 차이 처리 (Anthropic, OpenAI 등)

2. 설정 커스터마이징 (Configuration):
   - `copilotkit_customize_config()`:
     - 메타데이터 추가 (emit-intermediate-state, emit-messages 등)
     - 노드별 동작 제어

3. 이벤트 방출 (Event Emission):
   - `copilotkit_emit_state()`: 중간 상태를 클라이언트에 전송
   - `copilotkit_emit_message()`: 커스텀 메시지 전송
   - `copilotkit_emit_tool_call()`: 도구 호출 정보 표시
   - `copilotkit_exit()`: 에이전트 종료 시그널

4. 인터럽트 처리 (Interrupt Handling):
   - `copilotkit_interrupt()`: 실행 일시 중지 및 사용자 입력 대기

Usage Examples:

    # 메시지 변환
    from copilotkit.langgraph import copilotkit_messages_to_langchain

    converter = copilotkit_messages_to_langchain(use_function_call=False)
    langchain_msgs = converter(copilotkit_messages)

    # 상태 정의
    from copilotkit.langgraph import CopilotKitState
    from langgraph.graph import StateGraph

    graph = StateGraph(CopilotKitState)
    graph.add_node("agent", my_agent_node)

    # 중간 상태 방출
    from copilotkit.langgraph import copilotkit_emit_state

    async def my_node(state: CopilotKitState, config: RunnableConfig):
        await copilotkit_emit_state(config, {"progress": 50})
        return state

    # 사용자 입력 대기
    from copilotkit.langgraph import copilotkit_interrupt

    async def approval_node(state: CopilotKitState, config: RunnableConfig):
        user_response = await copilotkit_interrupt(
            config,
            "Proceed with deletion?"
        )
        # user_response에 사용자 입력이 담김
        return state
"""

import uuid
import json
import warnings
import asyncio
from typing import List, Optional, Any, Union, Dict, Callable, cast
from typing_extensions import TypedDict
from langgraph.graph import MessagesState


from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
    BaseMessage,
    AIMessage,
    ToolMessage
)
from langchain_core.runnables import RunnableConfig
from langchain_core.callbacks.manager import adispatch_custom_event
from langgraph.types import interrupt

from .types import Message, IntermediateStateConfig
from .logging import get_logger

logger = get_logger(__name__)

class CopilotContextItem(TypedDict):
    """
    컨텍스트 아이템 구조

    클라이언트로부터 전달받은 컨텍스트 정보를 담는 구조입니다.
    예: 현재 페이지 URL, 선택된 텍스트, 사용자 설정 등

    Attributes
    ----------
    description : str
        컨텍스트에 대한 설명 (예: "Current page URL")
    value : Any
        실제 컨텍스트 값 (문자열, 객체 등 any type)
    """
    description: str
    value: Any

class CopilotKitProperties(TypedDict):
    """
    CopilotKit 전용 상태 속성

    LangGraph 상태의 'copilotkit' 필드에 저장되는 정보입니다.
    클라이언트가 사용할 수 있는 액션 목록과 컨텍스트를 포함합니다.

    Attributes
    ----------
    actions : List[Any]
        사용 가능한 액션(도구) 목록
        클라이언트에서 이 액션들을 UI로 표시하거나 AI가 호출할 수 있습니다
    context : List[CopilotContextItem]
        현재 컨텍스트 정보 목록
        클라이언트의 상태 정보를 에이전트에 전달합니다
    """
    actions: List[Any]
    context: List[CopilotContextItem]

class CopilotKitState(MessagesState):
    """
    CopilotKit LangGraph 상태 정의

    LangGraph의 MessagesState를 확장하여 CopilotKit 전용 필드를 추가한 상태입니다.
    모든 CopilotKit 에이전트는 이 상태 구조를 사용하거나 이를 확장해야 합니다.

    Attributes
    ----------
    messages : List[BaseMessage]
        대화 메시지 목록 (MessagesState로부터 상속)
        LangChain의 BaseMessage 타입을 사용합니다
    copilotkit : CopilotKitProperties
        CopilotKit 전용 속성 (actions, context)

    Examples
    --------
    >>> from copilotkit.langgraph import CopilotKitState
    >>> from langgraph.graph import StateGraph
    >>>
    >>> # 기본 상태 사용
    >>> graph = StateGraph(CopilotKitState)
    >>>
    >>> # 확장 상태 정의
    >>> class MyState(CopilotKitState):
    ...     step: int
    ...     data: dict
    >>>
    >>> graph = StateGraph(MyState)
    """
    copilotkit: CopilotKitProperties


def copilotkit_messages_to_langchain(
        use_function_call: bool = False
    ) -> Callable[[List[Message]], List[BaseMessage]]:
    """
    CopilotKit 메시지를 LangChain 메시지로 변환

    CopilotKit 클라이언트로부터 전달받은 메시지들을 LangChain/LangGraph가 이해할 수 있는
    형식으로 변환합니다. 이 함수는 Converter 함수를 반환하므로, 실제 변환은 반환된 함수를
    호출하여 수행합니다.

    변환 매핑:
    - TextMessage (role: user) → HumanMessage
    - TextMessage (role: assistant) → AIMessage
    - TextMessage (role: system) → SystemMessage
    - ActionExecutionMessage → AIMessage (tool_calls 또는 function_call 포함)
    - ResultMessage → ToolMessage

    ActionExecutionMessage 처리:
    - use_function_call=False (기본값): 같은 parentMessageId를 가진 여러 도구 호출을
      하나의 AIMessage로 통합하고 tool_calls 리스트에 담습니다. (OpenAI 스타일)
    - use_function_call=True: 각 도구 호출을 별도의 AIMessage로 만들고
      additional_kwargs['function_call']에 담습니다. (Legacy 스타일)

    Parameters
    ----------
    use_function_call : bool, optional
        True이면 legacy function_call 형식 사용, False이면 tool_calls 형식 사용.
        기본값은 False (tool_calls 권장)

    Returns
    -------
    Callable[[List[Message]], List[BaseMessage]]
        실제 변환을 수행하는 converter 함수.
        이 함수에 CopilotKit 메시지 리스트를 전달하면 LangChain 메시지 리스트를 반환합니다.

    Examples
    --------
    >>> from copilotkit.langgraph import copilotkit_messages_to_langchain
    >>>
    >>> # Converter 함수 생성
    >>> converter = copilotkit_messages_to_langchain(use_function_call=False)
    >>>
    >>> # CopilotKit 메시지
    >>> copilotkit_msgs = [
    ...     {"type": "TextMessage", "role": "user", "content": "Hello", "id": "1"},
    ...     {"type": "TextMessage", "role": "assistant", "content": "Hi!", "id": "2"}
    ... ]
    >>>
    >>> # LangChain 메시지로 변환
    >>> langchain_msgs = converter(copilotkit_msgs)
    >>> # [HumanMessage(content="Hello", id="1"), AIMessage(content="Hi!", id="2")]

    Notes
    -----
    - 같은 parentMessageId를 가진 ActionExecutionMessage들은 하나의 AIMessage로 통합됩니다
    - 이미 처리된 parentMessageId는 건너뛰어 중복을 방지합니다
    - 메시지 ID는 원본 CopilotKit 메시지의 ID를 그대로 유지합니다

    See Also
    --------
    langchain_messages_to_copilotkit : 역변환 함수 (LangChain → CopilotKit)
    """
    def _copilotkit_messages_to_langchain(messages: List[Message]) -> List[BaseMessage]:
        result = []
        processed_action_executions = set()
        for message in cast(Any, messages):
            if message["type"] == "TextMessage":
                if message["role"] == "user":
                    result.append(HumanMessage(content=message["content"], id=message["id"]))
                elif message["role"] == "system":
                    result.append(SystemMessage(content=message["content"], id=message["id"]))
                elif message["role"] == "assistant":
                    result.append(AIMessage(content=message["content"], id=message["id"]))
            elif message["type"] == "ActionExecutionMessage":
                if use_function_call:
                    result.append(AIMessage(
                        id=message["id"],
                        content="",
                        additional_kwargs={
                            'function_call':{
                                'name': message["name"],
                                'arguments': json.dumps(message["arguments"]),
                            }
                        } 
                    ))
                else:
                    # convert multiple tool calls to a single message
                    message_id = message.get("parentMessageId")
                    if message_id is None:
                        message_id = message["id"]

                    if message_id in processed_action_executions:
                        continue

                    processed_action_executions.add(message_id)

                    all_tool_calls = []

                    # Find all tool calls for this message
                    for msg in messages:
                        if msg.get("parentMessageId", None) == message_id or msg["id"] == message_id:
                            all_tool_calls.append(msg)

                    tool_calls = [{
                        "name": t["name"],
                        "args": t["arguments"],
                        "id": t["id"],
                    } for t in all_tool_calls]

                    result.append(
                        AIMessage(
                            id=message_id,
                            content="",
                            tool_calls=tool_calls
                        )
                    )

            elif message["type"] == "ResultMessage":
                result.append(ToolMessage(
                    id=message["id"],
                    content=message["result"],
                    name=message["actionName"],
                    tool_call_id=message["actionExecutionId"]
                ))

        return result

    return _copilotkit_messages_to_langchain


def langchain_messages_to_copilotkit(
        messages: List[BaseMessage]
    ) -> List[Message]:
    """
    LangChain 메시지를 CopilotKit 메시지로 역변환

    LangGraph 에이전트가 생성한 LangChain 메시지들을 CopilotKit 클라이언트가
    이해할 수 있는 형식으로 변환합니다. 이 함수는 다양한 AI 모델의 메시지 형식 차이를
    처리하여 일관된 CopilotKit 형식으로 통일합니다.

    변환 매핑:
    - HumanMessage → TextMessage (role: user)
    - SystemMessage → TextMessage (role: system)
    - AIMessage → TextMessage (role: assistant) 또는 ActionExecutionMessage
    - ToolMessage → ResultMessage

    AIMessage 처리 로직:
    - tool_calls가 있는 경우: 각 tool_call을 ActionExecutionMessage로 분리
    - tool_calls가 없는 경우: 일반 TextMessage로 변환

    다중 도구 호출 처리:
    - 하나의 AIMessage에 여러 tool_calls가 있으면 각각을 별도 메시지로 분리
    - 각 ActionExecutionMessage는 부모 메시지 ID를 parentMessageId로 저장
    - ResultMessage는 해당하는 ActionExecutionMessage 바로 뒤에 배치되도록 재정렬

    모델별 content 형식 처리:
    - Anthropic: content가 dict 형식 ({"text": "..."}) → "text" 키 추출
    - OpenAI: content가 문자열 또는 리스트 → 첫 번째 요소 사용
    - 기타: 표준 문자열 형식 사용

    Parameters
    ----------
    messages : List[BaseMessage]
        변환할 LangChain 메시지 리스트

    Returns
    -------
    List[Message]
        CopilotKit 형식으로 변환된 메시지 리스트.
        메시지 순서는 재정렬되어 도구 호출과 결과가 인접하게 배치됩니다.

    Examples
    --------
    >>> from copilotkit.langgraph import langchain_messages_to_copilotkit
    >>> from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
    >>>
    >>> # LangChain 메시지
    >>> langchain_msgs = [
    ...     HumanMessage(content="Search for Python", id="1"),
    ...     AIMessage(content="", tool_calls=[
    ...         {"id": "call_1", "name": "search", "args": {"query": "Python"}}
    ...     ], id="2"),
    ...     ToolMessage(content="Found results", tool_call_id="call_1", id="3")
    ... ]
    >>>
    >>> # CopilotKit 메시지로 변환
    >>> copilotkit_msgs = langchain_messages_to_copilotkit(langchain_msgs)
    >>> # [
    >>> #   {"role": "user", "content": "Search for Python", "id": "1"},
    >>> #   {"id": "call_1", "name": "search", "arguments": {"query": "Python"}, "parentMessageId": "2"},
    >>> #   {"actionExecutionId": "call_1", "actionName": "search", "result": "Found results", "id": "3"}
    >>> # ]

    Notes
    -----
    - 도구 호출과 결과는 자동으로 재정렬되어 순서가 보장됩니다
    - tool_call_names 딕셔너리를 사용하여 ToolMessage에 도구 이름을 매핑합니다
    - content가 리스트인 경우 첫 번째 요소만 사용합니다 (Anthropic Claude 모델 호환)
    - 결과 메시지를 찾지 못한 경우 경고 로그를 출력합니다

    See Also
    --------
    copilotkit_messages_to_langchain : 정방향 변환 함수 (CopilotKit → LangChain)
    """
    result = []
    tool_call_names = {}

    for message in messages:
        if isinstance(message, AIMessage):
            for tool_call in message.tool_calls or []:
                tool_call_names[tool_call["id"]] = tool_call["name"]

    for message in messages:
        content = None

        if hasattr(message, "content"):
            content = message.content

            # Check if content is a list and use the first element
            if isinstance(content, list):
                content = content[0] if content else ""

            # Anthropic models return a dict with a "text" key
            if isinstance(content, dict):
                content = content.get("text", "")

        if isinstance(message, HumanMessage):
            result.append({
                "role": "user",
                "content": content,
                "id": message.id,
            })
        elif isinstance(message, SystemMessage):
            result.append({
                "role": "system",
                "content": content,
                "id": message.id,
            })
        elif isinstance(message, AIMessage):
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    result.append({
                        "id": tool_call["id"],
                        "name": tool_call["name"],
                        "arguments": tool_call["args"],
                        "parentMessageId": message.id,
                    })
            else:
                result.append({
                    "role": "assistant",
                    "content": content,
                    "id": message.id,
                    "parentMessageId": message.id,
                })
        elif isinstance(message, ToolMessage):
            result.append({
                "actionExecutionId": message.tool_call_id,
                "actionName": tool_call_names.get(message.tool_call_id, message.name or ""),
                "result": content,
                "id": message.id,
            })

    # Create a dictionary to map message ids to their corresponding messages
    results_dict = {msg["actionExecutionId"]: msg for msg in result if "actionExecutionId" in msg}


    # since we are splitting multiple tool calls into multiple messages,
    # we need to reorder the corresponding result messages to be after the tool call
    reordered_result = []

    for msg in result:

        # add all messages that are not tool call results
        if not "actionExecutionId" in msg:
            reordered_result.append(msg)

        # if the message is a tool call, also add the corresponding result message
        # immediately after the tool call
        if "arguments" in msg:
            msg_id = msg["id"]
            if msg_id in results_dict:
                reordered_result.append(results_dict[msg_id])
            else:
                logger.warning("Tool call result message not found for id: %s", msg_id)

    return reordered_result

def copilotkit_customize_config(
        base_config: Optional[RunnableConfig] = None,
        *,
        emit_messages: Optional[bool] = None,
        emit_tool_calls: Optional[Union[bool, str, List[str]]] = None,
        emit_intermediate_state: Optional[List[IntermediateStateConfig]] = None,
        emit_all: Optional[bool] = None, # deprecated
    ) -> RunnableConfig:
    """
    LangGraph 설정을 CopilotKit에 맞게 커스터마이징

    LangGraph의 RunnableConfig에 CopilotKit 전용 메타데이터를 추가합니다.
    이 메타데이터는 메시지 방출, 도구 호출 표시, 중간 상태 스트리밍 등의 동작을 제어합니다.

    주요 메타데이터 키:
    - copilotkit:emit-messages: 메시지를 클라이언트에 전송할지 여부
    - copilotkit:emit-tool-calls: 도구 호출을 표시할지 여부 (전체/일부/비활성화)
    - copilotkit:emit-intermediate-state: 도구 호출 결과를 상태로 스트리밍

    메시지 방출 제어:
    - emit_messages=True (기본값): 모든 메시지를 클라이언트에 전송
    - emit_messages=False: 메시지 전송 비활성화 (상태만 업데이트)

    도구 호출 방출 제어:
    - emit_tool_calls=True (기본값): 모든 도구 호출 표시
    - emit_tool_calls=False: 도구 호출 표시 안 함
    - emit_tool_calls="search": "search" 도구만 표시
    - emit_tool_calls=["search", "calc"]: 특정 도구들만 표시

    중간 상태 스트리밍:
    도구 호출의 인자를 LangGraph 상태 키로 매핑하여 실시간 스트리밍합니다.
    예: SearchTool의 "steps" 인자를 state["steps"]에 저장

    Parameters
    ----------
    base_config : Optional[RunnableConfig], optional
        커스터마이징할 기본 설정. None이면 새 설정을 생성합니다.
    emit_messages : Optional[bool], optional
        메시지 방출 여부. 기본값은 True (모든 메시지 방출)
    emit_tool_calls : Optional[Union[bool, str, List[str]]], optional
        도구 호출 방출 설정:
        - True: 모든 도구 호출 표시 (기본값)
        - False: 도구 호출 숨김
        - "tool_name": 특정 도구만 표시
        - ["tool1", "tool2"]: 여러 도구 선택적 표시
    emit_intermediate_state : Optional[List[IntermediateStateConfig]], optional
        중간 상태 스트리밍 설정 리스트. 각 항목은:
        - state_key: 상태에 저장할 키 이름
        - tool: 도구 이름
        - tool_argument: (선택) 특정 인자만 추출, 생략 시 모든 인자
    emit_all : Optional[bool], optional
        (Deprecated) 모든 이벤트 방출 여부. 대신 emit_messages, emit_tool_calls 사용 권장

    Returns
    -------
    RunnableConfig
        CopilotKit 메타데이터가 추가된 설정 객체

    Examples
    --------
    >>> from copilotkit.langgraph import copilotkit_customize_config
    >>>
    >>> # 메시지와 도구 호출 비활성화
    >>> config = copilotkit_customize_config(
    ...     config,
    ...     emit_messages=False,
    ...     emit_tool_calls=False
    ... )
    >>>
    >>> # 특정 도구만 표시
    >>> config = copilotkit_customize_config(
    ...     config,
    ...     emit_tool_calls=["SearchTool", "CalculatorTool"]
    ... )
    >>>
    >>> # 도구 호출 결과를 상태로 스트리밍
    >>> config = copilotkit_customize_config(
    ...     config,
    ...     emit_intermediate_state=[
    ...         {
    ...             "state_key": "search_steps",
    ...             "tool": "SearchTool",
    ...             "tool_argument": "steps"
    ...         },
    ...         {
    ...             "state_key": "analysis_result",
    ...             "tool": "AnalyzeTool"
    ...             # tool_argument 생략 시 모든 인자가 저장됨
    ...         }
    ...     ]
    ... )

    Notes
    -----
    - 이 함수는 기존 config를 변경하지 않고 새 객체를 반환합니다
    - 메타데이터는 LangGraph 실행 중 LangGraphAgent에서 읽어 동작을 제어합니다
    - emit_all은 deprecated되었으며 향후 버전에서 제거될 예정입니다
    """
    if emit_all is not None:
        warnings.warn(
            "The `emit_all` parameter is deprecated and will be removed in a future version. "
            "CopilotKit will now emit all messages and tool calls by default.",
            DeprecationWarning,
            stacklevel=2
        )
    metadata = base_config.get("metadata", {}) if base_config else {}

    if emit_all is True:
        metadata["copilotkit:emit-tool-calls"] = True
        metadata["copilotkit:emit-messages"] = True
    else:
        if emit_tool_calls is not None:
            metadata["copilotkit:emit-tool-calls"] = emit_tool_calls
        if emit_messages is not None:
            metadata["copilotkit:emit-messages"] = emit_messages

    if emit_intermediate_state:
        metadata["copilotkit:emit-intermediate-state"] = emit_intermediate_state

    base_config = base_config or {}

    return {
        **base_config,
        "metadata": metadata
    }


async def copilotkit_exit(config: RunnableConfig):
    """
    에이전트 실행 종료 시그널 전송

    현재 실행 중인 에이전트를 종료하도록 CopilotKit에 시그널을 보냅니다.
    이 함수를 호출해도 즉시 에이전트가 중단되지는 않습니다. 대신, 현재 실행이 완료된 후
    에이전트를 종료하도록 표시합니다.

    동작 방식:
    1. "copilotkit_exit" 커스텀 이벤트를 dispatch
    2. CopilotKit 클라이언트가 이 이벤트를 감지
    3. 현재 노드 실행 완료 후 에이전트 종료
    4. 추가 노드 실행이 예약되어 있어도 취소됨

    사용 시나리오:
    - 목표 달성 후 에이전트 자동 종료
    - 에러 발생 시 안전하게 종료
    - 특정 조건 만족 시 조기 종료

    Parameters
    ----------
    config : RunnableConfig
        LangGraph 실행 설정 객체

    Returns
    -------
    bool
        항상 True를 반환 (비동기)

    Examples
    --------
    >>> from copilotkit.langgraph import copilotkit_exit
    >>> from copilotkit.langgraph import CopilotKitState
    >>> from langchain_core.runnables import RunnableConfig
    >>>
    >>> async def final_node(state: CopilotKitState, config: RunnableConfig):
    ...     # 작업 완료 메시지
    ...     result = {"messages": [AIMessage(content="Task completed!")]}
    ...
    ...     # 에이전트 종료 시그널
    ...     await copilotkit_exit(config)
    ...
    ...     return result
    >>>
    >>> # 조건부 종료
    >>> async def decision_node(state: CopilotKitState, config: RunnableConfig):
    ...     if state.get("goal_achieved"):
    ...         await copilotkit_exit(config)
    ...     return state

    Notes
    -----
    - 호출 즉시 반환되며 현재 노드는 계속 실행됩니다
    - 0.02초의 짧은 대기(asyncio.sleep)로 이벤트 전파를 보장합니다
    - 에이전트가 종료되면 클라이언트는 더 이상 스트리밍을 받지 않습니다
    """

    await adispatch_custom_event(
        "copilotkit_exit",
        {},
        config=config,
    )
    await asyncio.sleep(0.02)

    return True

async def copilotkit_emit_state(config: RunnableConfig, state: Any):
    """
    중간 상태를 클라이언트에 실시간 전송

    장시간 실행되는 노드에서 현재 진행 상황을 사용자에게 업데이트할 때 유용합니다.
    노드 실행이 완료되기 전에 중간 상태를 스트리밍하여 사용자 경험을 개선합니다.

    동작 방식:
    1. "copilotkit_manually_emit_intermediate_state" 이벤트로 상태 전송
    2. 클라이언트가 실시간으로 상태를 수신하고 UI 업데이트
    3. 노드는 계속 실행되며 최종 상태는 노드 완료 시 반환

    사용 시나리오:
    - 진행률 표시 (progress bar)
    - 다단계 작업의 현재 단계 표시
    - 검색/분석 중간 결과 미리보기
    - 장시간 작업 시 사용자에게 피드백 제공

    Parameters
    ----------
    config : RunnableConfig
        LangGraph 실행 설정 객체
    state : Any
        전송할 상태 데이터 (JSON 직렬화 가능해야 함)
        일반적으로 dict 형태: {"progress": 50, "step": "analysis"}

    Returns
    -------
    bool
        항상 True를 반환 (비동기)

    Examples
    --------
    >>> from copilotkit.langgraph import copilotkit_emit_state
    >>> from copilotkit.langgraph import CopilotKitState
    >>> from langchain_core.runnables import RunnableConfig
    >>>
    >>> # 진행률 업데이트
    >>> async def long_running_node(state: CopilotKitState, config: RunnableConfig):
    ...     for i in range(10):
    ...         # 작업 수행
    ...         await some_operation(i)
    ...
    ...         # 진행률 전송
    ...         await copilotkit_emit_state(config, {
    ...             "progress": (i + 1) / 10 * 100,
    ...             "current_step": f"Processing item {i+1}"
    ...         })
    ...
    ...     return state
    >>>
    >>> # 다단계 분석 상태 업데이트
    >>> async def analysis_node(state: CopilotKitState, config: RunnableConfig):
    ...     await copilotkit_emit_state(config, {"step": "데이터 수집 중..."})
    ...     data = await collect_data()
    ...
    ...     await copilotkit_emit_state(config, {"step": "분석 중...", "data_size": len(data)})
    ...     result = await analyze(data)
    ...
    ...     await copilotkit_emit_state(config, {"step": "완료", "result": result})
    ...     return {"messages": [AIMessage(content=f"분석 완료: {result}")]}

    Notes
    -----
    - state는 반드시 JSON 직렬화 가능해야 합니다 (dict, list, str, int, bool, None 등)
    - 0.02초의 짧은 대기로 이벤트 전파를 보장합니다
    - 클라이언트는 useCopilotReadable 훅 등으로 이 상태를 구독할 수 있습니다
    - 이 함수는 노드의 최종 반환값을 대체하지 않습니다
    """

    await adispatch_custom_event(
        "copilotkit_manually_emit_intermediate_state",
        state,
        config=config,
    )
    await asyncio.sleep(0.02)

    return True

async def copilotkit_emit_message(config: RunnableConfig, message: str):
    """
    커스텀 메시지를 클라이언트에 즉시 전송

    장시간 실행되는 노드에서 사용자에게 진행 상황을 텍스트로 알릴 때 유용합니다.
    노드가 완료되기 전에 메시지를 미리 전송하여 실시간 피드백을 제공합니다.

    중요: 이 함수로 메시지를 방출해도 노드에서 최종적으로 messages를 반환해야 합니다.
    방출된 메시지는 UI에 즉시 표시되지만, 상태에는 노드의 반환값이 저장됩니다.

    동작 방식:
    1. "copilotkit_manually_emit_message" 이벤트로 메시지 전송
    2. 클라이언트가 즉시 메시지를 수신하여 채팅 UI에 표시
    3. 메시지에 자동으로 UUID가 할당되고 role은 "assistant"로 설정됨
    4. 노드 완료 시 반환된 메시지가 실제 상태에 저장됨

    사용 시나리오:
    - 다단계 작업의 진행 메시지 ("Step 1 완료", "Step 2 시작...")
    - 검색 중 발견한 정보를 즉시 표시
    - 분석 중간 결과를 사용자에게 알림
    - 장시간 작업 시 "아직 작업 중입니다..." 메시지

    Parameters
    ----------
    config : RunnableConfig
        LangGraph 실행 설정 객체
    message : str
        전송할 메시지 내용 (문자열)

    Returns
    -------
    bool
        항상 True를 반환 (비동기)

    Examples
    --------
    >>> from copilotkit.langgraph import copilotkit_emit_message
    >>> from copilotkit.langgraph import CopilotKitState
    >>> from langchain_core.messages import AIMessage
    >>> from langchain_core.runnables import RunnableConfig
    >>>
    >>> # 다단계 작업에서 진행 메시지 전송
    >>> async def multi_step_node(state: CopilotKitState, config: RunnableConfig):
    ...     # Step 1
    ...     await copilotkit_emit_message(config, "1단계: 데이터 수집 중...")
    ...     data = await collect_data()
    ...
    ...     # Step 2
    ...     await copilotkit_emit_message(config, "2단계: 분석 중...")
    ...     result = await analyze(data)
    ...
    ...     # 최종 메시지는 반드시 반환해야 함
    ...     final_message = f"분석 완료! 결과: {result}"
    ...     await copilotkit_emit_message(config, final_message)
    ...
    ...     return {
    ...         "messages": [AIMessage(content=final_message)]
    ...     }
    >>>
    >>> # 검색 중 중간 결과 표시
    >>> async def search_node(state: CopilotKitState, config: RunnableConfig):
    ...     await copilotkit_emit_message(config, "검색을 시작합니다...")
    ...
    ...     results = []
    ...     for query in queries:
    ...         result = await search(query)
    ...         results.append(result)
    ...         await copilotkit_emit_message(config, f"'{query}' 검색 완료 ({len(result)}개 발견)")
    ...
    ...     summary = f"총 {len(results)}개 항목을 찾았습니다."
    ...     return {"messages": [AIMessage(content=summary)]}

    Notes
    -----
    - 방출한 메시지는 UI에 즉시 표시되지만 상태에는 저장되지 않습니다
    - 노드는 반드시 최종 메시지를 messages 필드로 반환해야 합니다
    - 각 메시지에는 자동으로 UUID가 생성되고 role="assistant"가 설정됩니다
    - 0.02초의 짧은 대기로 이벤트 전파를 보장합니다
    """
    await adispatch_custom_event(
        "copilotkit_manually_emit_message",
        {
            "message": message,
            "message_id": str(uuid.uuid4()),
            "role": "assistant"
        },
        config=config,
    )
    await asyncio.sleep(0.02)

    return True


async def copilotkit_emit_tool_call(config: RunnableConfig, *, name: str, args: Dict[str, Any]):
    """
    도구 호출 정보를 클라이언트에 수동으로 전송

    LangGraph가 자동으로 감지하지 못하는 도구 호출을 명시적으로 클라이언트에 알립니다.
    주로 커스텀 로직으로 도구를 직접 호출할 때 UI에 표시하기 위해 사용합니다.

    동작 방식:
    1. "copilotkit_manually_emit_tool_call" 이벤트로 도구 정보 전송
    2. 클라이언트가 도구 호출을 수신하여 UI에 표시 (로딩 스피너, 도구 이름 등)
    3. 자동으로 UUID가 생성되어 도구 호출 ID로 사용됨
    4. 실제 도구 실행과는 독립적으로 UI 피드백만 제공

    사용 시나리오:
    - AI 모델을 거치지 않고 직접 도구를 호출할 때
    - 조건부 로직으로 특정 도구를 선택적으로 실행할 때
    - 내부적으로 여러 도구를 조합하여 사용하는 경우
    - 도구 호출 과정을 사용자에게 투명하게 보여주고 싶을 때

    Parameters
    ----------
    config : RunnableConfig
        LangGraph 실행 설정 객체
    name : str
        도구 이름 (클라이언트 UI에 표시됨)
    args : Dict[str, Any]
        도구 호출 인자들 (JSON 직렬화 가능해야 함)

    Returns
    -------
    bool
        항상 True를 반환 (비동기)

    Examples
    --------
    >>> from copilotkit.langgraph import copilotkit_emit_tool_call
    >>> from copilotkit.langgraph import CopilotKitState
    >>> from langchain_core.runnables import RunnableConfig
    >>>
    >>> # 커스텀 도구 호출 표시
    >>> async def custom_search_node(state: CopilotKitState, config: RunnableConfig):
    ...     # UI에 도구 호출 표시
    ...     await copilotkit_emit_tool_call(
    ...         config,
    ...         name="SearchTool",
    ...         args={"query": "Python tutorial", "max_results": 10}
    ...     )
    ...
    ...     # 실제 검색 실행
    ...     results = await custom_search_function("Python tutorial", max_results=10)
    ...
    ...     return {"messages": [AIMessage(content=f"Found {len(results)} results")]}
    >>>
    >>> # 조건부 도구 선택
    >>> async def smart_tool_node(state: CopilotKitState, config: RunnableConfig):
    ...     if state.get("needs_calculation"):
    ...         await copilotkit_emit_tool_call(
    ...             config,
    ...             name="Calculator",
    ...             args={"expression": "2 + 2"}
    ...         )
    ...         result = calculate("2 + 2")
    ...     else:
    ...         await copilotkit_emit_tool_call(
    ...             config,
    ...             name="WebSearch",
    ...             args={"query": state["query"]}
    ...         )
    ...         result = search(state["query"])
    ...
    ...     return {"messages": [AIMessage(content=str(result))]}

    Notes
    -----
    - 이 함수는 UI 피드백만 제공하며 실제 도구를 실행하지 않습니다
    - 실제 도구 실행은 별도로 구현해야 합니다
    - 자동으로 UUID가 생성되어 tool call ID로 사용됩니다
    - 0.02초의 짧은 대기로 이벤트 전파를 보장합니다
    - args는 반드시 JSON 직렬화 가능해야 합니다 (dict, list, str, int, bool, None 등)
    """

    await adispatch_custom_event(
        "copilotkit_manually_emit_tool_call",
        {
            "name": name,
            "args": args,
            "id": str(uuid.uuid4())
        },
        config=config,
    )
    await asyncio.sleep(0.02)

    return True

def copilotkit_interrupt(
        message: Optional[str] = None,
        action: Optional[str] = None,
        args: Optional[Dict[str, Any]] = None
):
    """
    에이전트 실행을 일시 중지하고 사용자 입력 대기

    LangGraph 실행을 중단하고 사용자의 응답을 기다립니다.
    사용자가 응답하면 에이전트는 해당 응답을 받아 실행을 재개합니다.

    두 가지 인터럽트 모드:
    1. 메시지 모드 (message 파라미터 사용):
       - 사용자에게 텍스트 질문을 표시
       - 사용자가 텍스트로 응답
       - 예: "이 파일을 삭제하시겠습니까?"

    2. 액션 모드 (action, args 파라미터 사용):
       - 사용자에게 액션 승인 요청
       - 도구 호출 형태로 인터럽트 (tool_calls 포함)
       - 예: DeleteFile 액션에 대한 승인 요청

    동작 흐름:
    1. LangGraph의 interrupt() 함수 호출로 실행 중단
    2. 클라이언트에 인터럽트 메시지/액션 전송
    3. 사용자가 입력 제공 (텍스트 또는 승인)
    4. 클라이언트가 meta_events로 응답과 함께 재개 요청
    5. 에이전트가 사용자 응답을 받아 실행 재개

    Parameters
    ----------
    message : Optional[str], optional
        사용자에게 표시할 질문 메시지 (메시지 모드)
        action과 함께 사용할 수 없음
    action : Optional[str], optional
        승인이 필요한 액션 이름 (액션 모드)
        message와 함께 사용할 수 없음
    args : Optional[Dict[str, Any]], optional
        액션의 인자들 (액션 모드에서 사용)
        action이 제공된 경우에만 유효

    Returns
    -------
    tuple[str, List[BaseMessage]]
        - answer (str): 사용자 응답의 content (마지막 메시지의 content)
        - response (List[BaseMessage]): 전체 응답 메시지 리스트

    Raises
    ------
    ValueError
        message와 action 모두 None인 경우

    Examples
    --------
    >>> from copilotkit.langgraph import copilotkit_interrupt
    >>> from copilotkit.langgraph import CopilotKitState
    >>> from langchain_core.runnables import RunnableConfig
    >>>
    >>> # 메시지 모드: 텍스트 질문
    >>> async def approval_node(state: CopilotKitState, config: RunnableConfig):
    ...     answer, messages = copilotkit_interrupt(
    ...         message="정말로 이 작업을 진행하시겠습니까?"
    ...     )
    ...
    ...     if "yes" in answer.lower() or "예" in answer:
    ...         # 작업 진행
    ...         return {"messages": [AIMessage(content="작업을 진행합니다.")]}
    ...     else:
    ...         # 작업 취소
    ...         return {"messages": [AIMessage(content="작업이 취소되었습니다.")]}
    >>>
    >>> # 액션 모드: 도구 호출 승인
    >>> async def delete_approval_node(state: CopilotKitState, config: RunnableConfig):
    ...     answer, messages = copilotkit_interrupt(
    ...         action="DeleteFile",
    ...         args={"filename": "important.txt", "reason": "outdated"}
    ...     )
    ...
    ...     # 사용자가 승인하면 파일 삭제
    ...     await delete_file("important.txt")
    ...     return {"messages": [AIMessage(content="파일이 삭제되었습니다.")]}
    >>>
    >>> # 다단계 승인 프로세스
    >>> async def multi_approval_node(state: CopilotKitState, config: RunnableConfig):
    ...     # 1단계: 데이터 수집 승인
    ...     answer1, _ = copilotkit_interrupt(
    ...         message="데이터를 수집하시겠습니까?"
    ...     )
    ...
    ...     if "no" in answer1.lower():
    ...         return {"messages": [AIMessage(content="작업 취소")]}
    ...
    ...     data = await collect_data()
    ...
    ...     # 2단계: 분석 승인
    ...     answer2, _ = copilotkit_interrupt(
    ...         message=f"{len(data)}개 항목을 분석하시겠습니까?"
    ...     )
    ...
    ...     if "yes" in answer2.lower():
    ...         result = await analyze(data)
    ...         return {"messages": [AIMessage(content=f"분석 완료: {result}")]}

    Notes
    -----
    - message와 action 중 정확히 하나만 제공해야 합니다
    - 메시지 모드: AIMessage(content=message)로 전송
    - 액션 모드: AIMessage(tool_calls=[...])로 전송, tool_call_id 자동 생성
    - 인터럽트 값은 __copilotkit_interrupt_value__와 __copilotkit_messages__에 저장
    - 사용자 응답은 response[-1].content에서 추출됩니다
    - LangGraph의 interrupt() 함수를 내부적으로 사용합니다

    See Also
    --------
    copilotkit_exit : 에이전트 종료 시그널
    copilotkit_emit_message : 메시지 방출
    """
    if message is None and action is None:
        raise ValueError('Either message or action (and optional arguments) must be provided')

    interrupt_message = None
    interrupt_values = None
    answer = None

    if message is not None:
        interrupt_values = message
        interrupt_message = AIMessage(content=message, id=str(uuid.uuid4()))
    else:
        tool_id = str(uuid.uuid4())
        interrupt_message = AIMessage(
                content="",
                tool_calls=[{
                    "id": tool_id,
                    "name": action,
                    "args": args or {}
                }]
            )
        interrupt_values = {
            "action": action,
            "args": args or {}
        }

    response = interrupt({
        "__copilotkit_interrupt_value__": interrupt_values,
        "__copilotkit_messages__": [interrupt_message]
    })
    answer = response[-1].content

    return answer, response
