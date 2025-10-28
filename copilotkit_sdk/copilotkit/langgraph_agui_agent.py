"""
LangGraph AGUI Agent for CopilotKit

이 모듈은 AG-UI (Agent UI) 통합을 위한 LangGraphAgent의 확장 클래스를 제공합니다.
AG-UI는 에이전트의 UI 이벤트를 구조화하여 더 풍부한 사용자 인터페이스를 구축할 수 있게 합니다.

LangGraphAGUIAgent는 기본 LangGraphAgent를 상속하며, 다음 기능을 추가합니다:
- 커스텀 이벤트 디스패칭 (메시지, 도구 호출, 상태)
- 메타데이터 기반 이벤트 필터링
- CopilotKit 전용 이벤트 변환

주요 차이점:
1. 기본 LangGraphAgent: 원시 LangGraph 이벤트 스트리밍
2. LangGraphAGUIAgent: 구조화된 UI 이벤트로 변환하여 스트리밍

Event Processing Flow:
```mermaid
graph TD
    subgraph "LangGraph Events"
    A[on_chat_model_stream]
    B[on_tool_calls]
    C[on_custom_event]
    end

    subgraph "LangGraphAGUIAgent"
    D[_handle_single_event]
    E[_dispatch_event]
    end

    subgraph "Custom Event Handling"
    F{Event Type?}
    G[ManuallyEmitMessage]
    H[ManuallyEmitToolCall]
    I[ManuallyEmitState]
    J[copilotkit_exit]
    end

    subgraph "AG-UI Events"
    K[TextMessageStartEvent]
    L[TextMessageContentEvent]
    M[TextMessageEndEvent]
    N[ToolCallStartEvent]
    O[ToolCallArgsEvent]
    P[ToolCallEndEvent]
    Q[StateSnapshotEvent]
    R[CustomEvent Exit]
    end

    A --> D
    B --> D
    C --> D
    D --> E
    E --> F

    F -->|ManuallyEmitMessage| G
    F -->|ManuallyEmitToolCall| H
    F -->|ManuallyEmitState| I
    F -->|copilotkit_exit| J

    G --> K
    G --> L
    G --> M

    H --> N
    H --> O
    H --> P

    I --> Q
    J --> R

    style E fill:#ffe1e1
    style F fill:#fff4e1
```

Custom Event Dispatch Flow:
```mermaid
sequenceDiagram
    participant G as LangGraph
    participant A as LangGraphAGUIAgent
    participant C as Client

    Note over G,A: 수동 메시지 방출
    G->>A: CustomEvent(ManuallyEmitMessage)
    A->>A: _dispatch_event()
    A->>C: TextMessageStartEvent
    A->>C: TextMessageContentEvent
    A->>C: TextMessageEndEvent

    Note over G,A: 수동 도구 호출 방출
    G->>A: CustomEvent(ManuallyEmitToolCall)
    A->>A: _dispatch_event()
    A->>C: ToolCallStartEvent
    A->>C: ToolCallArgsEvent
    A->>C: ToolCallEndEvent

    Note over G,A: 수동 상태 방출
    G->>A: CustomEvent(ManuallyEmitState)
    A->>A: _dispatch_event()
    A->>A: get_state_snapshot()
    A->>C: StateSnapshotEvent

    Note over G,A: 종료 이벤트
    G->>A: CustomEvent(copilotkit_exit)
    A->>A: _dispatch_event()
    A->>C: CustomEvent(Exit)
```

Event Filtering:
```mermaid
graph LR
    A[Raw Event] --> B{Has Metadata?}
    B -->|Yes| C{Check Filters}
    B -->|No| D[Dispatch Event]

    C --> E{emit-messages?}
    C --> F{emit-tool-calls?}

    E -->|false & is_message_event| G[Skip Event]
    E -->|true| D

    F -->|false & is_tool_event| G
    F -->|true| D

    D --> H[Client]
    G --> I[Discard]

    style G fill:#ffcccc
    style D fill:#ccffcc
```
"""

import json
from typing import Dict, Any, List, Optional, Union, AsyncGenerator
from enum import Enum
from ag_ui_langgraph import LangGraphAgent
from ag_ui.core import (
    EventType,
    CustomEvent,
    TextMessageStartEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    ToolCallStartEvent,
    ToolCallArgsEvent,
    ToolCallEndEvent,
    StateSnapshotEvent,
)
from langgraph.graph.state import CompiledStateGraph
from langchain_core.runnables import RunnableConfig

try:
    from langchain.schema import BaseMessage
except ImportError:
    # Langchain >= 1.0.0
    from langchain_core.messages import BaseMessage


class CustomEventNames(Enum):
    """
    CopilotKit 커스텀 이벤트 이름 정의

    이 이벤트들은 LangGraph 그래프 내에서 명시적으로 발생시켜
    클라이언트에게 특정 정보를 전달할 때 사용됩니다.
    """
    ManuallyEmitMessage = "copilotkit_manually_emit_message"
    """
    수동으로 메시지를 방출합니다.
    그래프 로직에서 직접 메시지를 생성하여 클라이언트에 전송할 때 사용합니다.
    """

    ManuallyEmitToolCall = "copilotkit_manually_emit_tool_call"
    """
    수동으로 도구 호출 정보를 방출합니다.
    AI 모델 외부에서 도구를 호출한 결과를 클라이언트에 표시할 때 사용합니다.
    """

    ManuallyEmitState = "copilotkit_manually_emit_intermediate_state"
    """
    중간 상태를 수동으로 방출합니다.
    그래프 실행 중 특정 시점의 상태를 클라이언트와 동기화할 때 사용합니다.
    """


class LangGraphEventTypes(Enum):
    """
    LangGraph 이벤트 타입

    LangGraph에서 발생하는 이벤트의 타입을 정의합니다.
    """
    OnChatModelStream = "on_chat_model_stream"
    """AI 모델의 응답 스트리밍 이벤트"""

    OnCustomEvent = "on_custom_event"
    """사용자 정의 커스텀 이벤트"""


class PredictStateTool:
    """
    예측 상태 도구 설정

    AI 모델이 도구를 호출할 때, 해당 도구의 인자로부터
    상태 값을 예측하여 실시간으로 UI에 반영하기 위한 설정입니다.

    Attributes
    ----------
    tool : str
        모니터링할 도구 이름
    state_key : str
        상태에서 업데이트할 키
    tool_argument : str
        도구 인자 중 상태 값을 추출할 필드 이름
    """
    def __init__(self, tool: str, state_key: str, tool_argument: str):
        self.tool = tool
        self.state_key = state_key
        self.tool_argument = tool_argument


# 타입 별칭 정의
State = Dict[str, Any]
"""에이전트 상태 타입"""

SchemaKeys = Dict[str, List[str]]
"""스키마 키 목록 타입"""

TextMessageEvents = Union[TextMessageStartEvent, TextMessageContentEvent, TextMessageEndEvent]
"""텍스트 메시지 관련 이벤트 타입"""

ToolCallEvents = Union[ToolCallStartEvent, ToolCallArgsEvent, ToolCallEndEvent]
"""도구 호출 관련 이벤트 타입"""


class LangGraphAGUIAgent(LangGraphAgent):
    """
    AG-UI 통합 LangGraph 에이전트

    AG-UI 프레임워크와 통합된 LangGraphAgent의 확장 버전입니다.
    기본 LangGraphAgent의 모든 기능을 포함하며, 추가로 AG-UI의
    구조화된 이벤트 시스템을 지원합니다.

    주요 기능:
    - 커스텀 CopilotKit 이벤트를 AG-UI 이벤트로 변환
    - 메타데이터 기반 이벤트 필터링
    - 수동 메시지/도구 호출/상태 방출 지원
    - 중간 상태 예측 (PredictState)

    Parameters
    ----------
    name : str
        에이전트 이름
    graph : CompiledStateGraph
        실행할 LangGraph 그래프
    description : Optional[str], optional
        에이전트 설명 (동적 라우팅에 사용)
    config : Union[Optional[RunnableConfig], dict], optional
        LangGraph 설정

    Examples
    --------
    >>> from copilotkit import LangGraphAGUIAgent
    >>> agent = LangGraphAGUIAgent(
    ...     name="my_agent",
    ...     graph=my_compiled_graph,
    ...     description="A helpful assistant"
    ... )
    """
    def __init__(
        self,
        *,
        name: str,
        graph: CompiledStateGraph,
        description: Optional[str] = None,
        config: Union[Optional[RunnableConfig], dict] = None
    ):
        super().__init__(name=name, graph=graph, description=description, config=config)
        # "copilotkit"을 상수 스키마 키에 추가
        # 이를 통해 copilotkit 필드가 항상 상태에 포함되도록 보장
        self.constant_schema_keys = self.constant_schema_keys + ["copilotkit"]

    def _dispatch_event(self, event) -> str:
        """
        이벤트를 디스패치하고 필터링합니다.

        이 메서드는 AG-UI의 기본 이벤트 디스패칭을 오버라이드하여
        CopilotKit 전용 커스텀 이벤트를 처리하고, 메타데이터 기반으로
        이벤트를 필터링합니다.

        Event Processing:
        1. CustomEvent 타입 체크
        2. CopilotKit 커스텀 이벤트 처리
        3. 메타데이터 기반 필터링 적용
        4. 부모 클래스의 디스패치 메서드 호출

        Parameters
        ----------
        event : Event
            디스패치할 이벤트 객체

        Returns
        -------
        str
            직렬화된 이벤트 문자열 (클라이언트로 전송됨)
            필터링된 경우 빈 문자열 반환

        Notes
        -----
        지원하는 커스텀 이벤트:
        - ManuallyEmitMessage: 텍스트 메시지 3개 이벤트로 변환
        - ManuallyEmitToolCall: 도구 호출 3개 이벤트로 변환
        - ManuallyEmitState: 상태 스냅샷 이벤트로 변환
        - copilotkit_exit: Exit 커스텀 이벤트로 변환

        메타데이터 필터:
        - copilotkit:emit-tool-calls: false면 도구 호출 이벤트 스킵
        - copilotkit:emit-messages: false면 메시지 이벤트 스킵
        """
        # CustomEvent 타입인 경우 CopilotKit 전용 처리
        if event.type == EventType.CUSTOM:
            custom_event = event

            # 수동 메시지 방출: 시작-내용-종료 3개 이벤트로 분리
            if custom_event.name == CustomEventNames.ManuallyEmitMessage.value:
                # 메시지 시작 이벤트
                super()._dispatch_event(
                    TextMessageStartEvent(
                        type=EventType.TEXT_MESSAGE_START,
                        role="assistant",
                        message_id=custom_event.value["message_id"],
                        raw_event=event,
                    )
                )
                # 메시지 내용 이벤트
                super()._dispatch_event(
                    TextMessageContentEvent(
                        type=EventType.TEXT_MESSAGE_CONTENT,
                        message_id=custom_event.value["message_id"],
                        delta=custom_event.value["message"],
                        raw_event=event,
                    )
                )
                # 메시지 종료 이벤트
                super()._dispatch_event(
                    TextMessageEndEvent(
                        type=EventType.TEXT_MESSAGE_END,
                        message_id=custom_event.value["message_id"],
                        raw_event=event,
                    )
                )
                return super()._dispatch_event(event)

            # 수동 도구 호출 방출: 시작-인자-종료 3개 이벤트로 분리
            if custom_event.name == CustomEventNames.ManuallyEmitToolCall.value:
                # 도구 호출 시작 이벤트
                super()._dispatch_event(
                    ToolCallStartEvent(
                        type=EventType.TOOL_CALL_START,
                        tool_call_id=custom_event.value["id"],
                        tool_call_name=custom_event.value["name"],
                        parent_message_id=custom_event.value["id"],
                        raw_event=event,
                    )
                )
                # 도구 호출 인자 이벤트
                super()._dispatch_event(
                    ToolCallArgsEvent(
                        type=EventType.TOOL_CALL_ARGS,
                        tool_call_id=custom_event.value["id"],
                        delta=custom_event.value["args"] if isinstance(custom_event.value["args"], str) else json.dumps(
                            custom_event.value["args"]),
                        raw_event=event,
                    )
                )
                # 도구 호출 종료 이벤트
                super()._dispatch_event(
                    ToolCallEndEvent(
                        type=EventType.TOOL_CALL_END,
                        tool_call_id=custom_event.value["id"],
                        raw_event=event,
                    )
                )
                return super()._dispatch_event(event)

            # 수동 상태 방출: 상태 스냅샷 이벤트로 변환
            if custom_event.name == CustomEventNames.ManuallyEmitState.value:
                # 현재 실행 중인 run의 수동 방출 상태 저장
                self.active_run["manually_emitted_state"] = custom_event.value
                return super()._dispatch_event(
                    StateSnapshotEvent(
                        type=EventType.STATE_SNAPSHOT,
                        snapshot=self.get_state_snapshot(self.active_run["manually_emitted_state"]),
                        raw_event=event,
                    )
                )

            # 종료 이벤트: Exit 커스텀 이벤트로 변환
            if custom_event.name == "copilotkit_exit":
                return super()._dispatch_event(
                    CustomEvent(
                        type=EventType.CUSTOM,
                        name="Exit",
                        value=True,
                        raw_event=event,
                    )
                )

        # 메타데이터 기반 이벤트 필터링
        # 원시 이벤트에서 메타데이터 추출
        raw_event = getattr(event, 'raw_event', None)
        if raw_event:
            # 메시지 이벤트 타입 체크
            is_message_event = event.type in [
                EventType.TEXT_MESSAGE_START,
                EventType.TEXT_MESSAGE_CONTENT,
                EventType.TEXT_MESSAGE_END
            ]
            # 도구 호출 이벤트 타입 체크
            is_tool_event = event.type in [
                EventType.TOOL_CALL_START,
                EventType.TOOL_CALL_ARGS,
                EventType.TOOL_CALL_END
            ]

            metadata = getattr(raw_event, 'metadata', {}) or {}

            # 도구 호출 방출 필터
            if "copilotkit:emit-tool-calls" in metadata:
                if metadata["copilotkit:emit-tool-calls"] is False and is_tool_event:
                    return ""  # 이벤트 스킵

            # 메시지 방출 필터
            if "copilotkit:emit-messages" in metadata:
                if metadata["copilotkit:emit-messages"] is False and is_message_event:
                    return ""  # 이벤트 스킵

        # 필터링되지 않은 이벤트는 부모 클래스의 디스패처로 전달
        return super()._dispatch_event(event)

    async def _handle_single_event(self, event: Any, state: State) -> AsyncGenerator[str, None]:
        """
        단일 이벤트를 처리하고 PredictState 메타데이터를 추가합니다.

        이 메서드는 AG-UI의 기본 이벤트 처리를 오버라이드하여
        on_chat_model_stream 이벤트에 PredictState 관련 메타데이터를 추가합니다.
        PredictState는 AI 모델이 도구를 호출할 때, 도구의 인자로부터
        상태 값을 실시간으로 예측하여 UI에 반영하는 기능입니다.

        Parameters
        ----------
        event : Any
            처리할 LangGraph 이벤트
        state : State
            현재 에이전트 상태

        Yields
        ------
        str
            직렬화된 이벤트 문자열

        Notes
        -----
        PredictState 동작:
        1. 메타데이터에서 emit-intermediate-state 설정 확인
        2. AI가 특정 도구를 호출하기 시작하면
        3. 도구 인자를 파싱하여 상태 필드 업데이트
        4. 실시간으로 상태 동기화 이벤트 방출
        """
        # on_chat_model_stream 이벤트에 PredictState 메타데이터 추가
        if event.get("event") == LangGraphEventTypes.OnChatModelStream.value:
            # 메타데이터에서 중간 상태 방출 설정 가져오기
            predict_state_metadata = event.get("metadata", {}).get("copilotkit:emit-intermediate-state", [])
            # predict_state 필드로 메타데이터 복사
            event["metadata"]['predict_state'] = predict_state_metadata

        # 부모 클래스의 이벤트 처리 메서드 호출 (제너레이터)
        async for event_str in super()._handle_single_event(event, state):
            yield event_str

    def langgraph_default_merge_state(self, state: State, messages: List[BaseMessage], input: Any) -> State:
        """
        기본 상태 병합 로직을 오버라이드하여 CopilotKit 액션을 추가합니다.

        AG-UI의 기본 merge_state를 확장하여, AG-UI의 tools와 context를
        CopilotKit의 actions 형식으로 변환하여 상태에 포함시킵니다.

        이를 통해 AG-UI 그래프에서 정의된 도구들이 CopilotKit 클라이언트에서
        사용 가능한 액션으로 자동 변환됩니다.

        Parameters
        ----------
        state : State
            현재 에이전트 상태
        messages : List[BaseMessage]
            병합할 메시지 목록
        input : Any
            입력 데이터

        Returns
        -------
        State
            병합된 상태 (copilotkit 필드 포함)

        Notes
        -----
        병합 로직:
        1. 부모 클래스의 merge_state 호출
        2. ag-ui 필드에서 tools와 context 추출
        3. copilotkit 필드에 actions로 변환하여 저장
        4. 원본 상태와 병합하여 반환
        """
        # 부모 클래스의 기본 병합 로직 실행
        merged_state = super().langgraph_default_merge_state(state, messages, input)

        # AG-UI 속성 추출 (ag-ui 필드가 있으면 사용, 없으면 전체 상태 사용)
        agui_properties = merged_state.get('ag-ui', {}) or merged_state

        # CopilotKit 형식으로 변환
        return {
            **merged_state,
            'copilotkit': {
                'actions': agui_properties.get('tools', []),      # AG-UI tools → CopilotKit actions
                'context': agui_properties.get('context', [])     # AG-UI context 유지
            },
        }
