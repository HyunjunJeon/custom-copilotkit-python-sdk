"""
CopilotKit Run Loop - 비동기 이벤트 처리 런타임

이 모듈은 CopilotKit의 핵심 실행 엔진입니다.
비동기 이벤트 큐를 기반으로 에이전트 실행을 관리하고,
실시간 상태 예측 및 SSE 스트리밍을 처리합니다.

Run Loop Architecture
---------------------

```mermaid
flowchart TB
    subgraph "Main Process"
        Start([copilotkit_run 시작])
        CreateQueue[로컬 큐 생성]
        SetContext[컨텍스트 설정]
        CreateTask[에이전트 태스크 생성]
        EventLoop{이벤트 대기}
        HandleEvent[handle_runtime_event]
        YieldJSON[JSON Lines 반환]
        CheckFinish{완료?}
        Cleanup[컨텍스트 정리]
        End([종료])
    end

    subgraph "Event Handlers"
        ProtocolEvent[Protocol Event<br/>텍스트/액션 메시지]
        MetaEvent[Meta Event<br/>PREDICT_STATE/EXIT]
        LifecycleEvent[Lifecycle Event<br/>RUN/NODE 이벤트]
        StatePredict[predict_state<br/>실시간 상태 예측]
        StateUpdate[AgentStateMessage<br/>상태 업데이트]
    end

    subgraph "Context Management"
        QueueCtx[Queue Context<br/>asyncio.Queue]
        ExecCtx[Execution Context<br/>CopilotKitRunExecution]
    end

    Start --> CreateQueue
    CreateQueue --> SetContext
    SetContext --> QueueCtx
    SetContext --> ExecCtx
    SetContext --> CreateTask
    CreateTask --> EventLoop
    EventLoop -->|큐에서 꺼냄| HandleEvent

    HandleEvent --> ProtocolEvent
    HandleEvent --> MetaEvent
    HandleEvent --> LifecycleEvent

    ProtocolEvent --> StatePredict
    StatePredict -->|예측 상태| StateUpdate
    StateUpdate --> YieldJSON

    MetaEvent -->|설정 업데이트| EventLoop
    LifecycleEvent --> StateUpdate

    ProtocolEvent --> YieldJSON
    YieldJSON --> CheckFinish
    CheckFinish -->|아니오| EventLoop
    CheckFinish -->|예| Cleanup
    Cleanup --> End
```

Context Management Flow
-----------------------

```mermaid
sequenceDiagram
    participant Caller as 호출자
    participant RunLoop as copilotkit_run
    participant Queue as asyncio.Queue
    participant Ctx as Context Variables
    participant Agent as 에이전트 태스크

    Caller->>RunLoop: fn() 실행 요청
    RunLoop->>Queue: 로컬 큐 생성
    RunLoop->>Ctx: set_context_queue(queue)
    RunLoop->>Ctx: set_context_execution(execution)
    RunLoop->>Agent: create_task(fn())

    loop 이벤트 처리
        Agent->>Queue: queue_put(event)
        Queue->>RunLoop: event 전달
        RunLoop->>RunLoop: handle_runtime_event
        RunLoop-->>Caller: yield JSON Lines
    end

    RunLoop->>Ctx: reset_context_queue
    RunLoop->>Ctx: reset_context_execution
    RunLoop-->>Caller: 완료
```

Event Processing Pipeline
--------------------------

```mermaid
stateDiagram-v2
    [*] --> QueueWait: 이벤트 대기

    QueueWait --> EventReceived: event 수신

    EventReceived --> ProtocolEvent: Protocol Event
    EventReceived --> MetaEvent: Meta Event
    EventReceived --> LifecycleEvent: Lifecycle Event

    ProtocolEvent --> PredictCheck: ACTION_EXECUTION?
    PredictCheck --> PredictState: Yes
    PredictCheck --> EmitEvent: No
    PredictState --> EmitBoth: 예측 상태 포함
    EmitBoth --> QueueWait
    EmitEvent --> QueueWait

    MetaEvent --> UpdateConfig: PREDICT_STATE
    MetaEvent --> SetExit: EXIT
    UpdateConfig --> QueueWait
    SetExit --> QueueWait

    LifecycleEvent --> NodeStart: NODE_STARTED
    LifecycleEvent --> NodeFinish: NODE_FINISHED
    LifecycleEvent --> RunStart: RUN_STARTED
    LifecycleEvent --> RunFinish: RUN_FINISHED
    LifecycleEvent --> RunError: RUN_ERROR

    NodeStart --> EmitState: AgentStateMessage
    NodeFinish --> ResetPredict: 예측 상태 초기화
    ResetPredict --> EmitState
    EmitState --> QueueWait

    RunStart --> UpdateState: execution 상태 업데이트
    UpdateState --> QueueWait

    RunFinish --> MarkFinished: is_finished = True
    RunError --> PrintError: 에러 출력
    PrintError --> MarkFinished
    MarkFinished --> [*]
```

Core Concepts
-------------

1. **Context Variables (컨텍스트 변수)**
   - 비동기 태스크 간 안전한 상태 공유
   - Queue Context: 이벤트 큐 참조
   - Execution Context: 실행 상태 추적

2. **Event Queue (이벤트 큐)**
   - asyncio.Queue 기반 비동기 이벤트 처리
   - Priority 지원: 우선순위 이벤트 처리
   - yield_control(): 이벤트 루프 제어권 양보

3. **State Prediction (상태 예측)**
   - 실시간 액션 인자 파싱
   - Partial JSON parsing으로 스트리밍 중 상태 업데이트
   - copilotkit_customize_config로 예측 대상 설정

4. **Event Handling (이벤트 처리)**
   - Protocol Events: 클라이언트로 직접 전송
   - Meta Events: 런타임 설정 변경
   - Lifecycle Events: 에이전트 상태 추적

5. **JSON Lines Streaming (JSON Lines 스트리밍)**
   - SSE를 통한 실시간 이벤트 전송
   - 각 이벤트는 별도의 JSON 라인으로 전송
   - 클라이언트는 줄 단위로 파싱

Usage Examples
--------------

Basic Run Loop:

>>> async def my_agent():
...     await queue_put(text_message_start(message_id="msg_1"))
...     await queue_put(text_message_content(message_id="msg_1", content="Hello"))
...     await queue_put(text_message_end(message_id="msg_1"))
...
>>> execution = CopilotKitRunExecution(
...     thread_id="thread_1",
...     agent_name="assistant",
...     run_id="run_1",
...     should_exit=False,
...     node_name="",
...     is_finished=False,
...     predict_state_configuration={},
...     predicted_state={},
...     argument_buffer="",
...     current_tool_call=None,
...     state={}
... )
>>> async for json_line in copilotkit_run(my_agent, execution=execution):
...     print(json_line)

State Prediction:

>>> from copilotkit import copilotkit_customize_config
>>>
>>> @copilotkit_action(name="update_user")
... @copilotkit_customize_config(
...     predict_state={
...         "user_name": {
...             "tool_name": "update_user",
...             "tool_argument": "name"
...         }
...     }
... )
... async def update_user(name: str):
...     # user_name이 실시간으로 예측되어 클라이언트로 스트리밍됩니다
...     return {"status": "updated"}

Priority Events:

>>> async def send_urgent_message():
...     # 우선순위 이벤트는 즉시 처리됩니다
...     await queue_put(
...         meta_event(name=RuntimeMetaEventName.EXIT, value=True),
...         priority=True
...     )

Best Practices
--------------

1. **Context 사용**
   - queue_put()으로 이벤트 전송 (직접 큐 접근 금지)
   - get_context_execution()으로 실행 상태 접근

2. **이벤트 순서**
   - START → CONTENT/ARGS → END 패턴 준수
   - 동일한 ID로 이벤트 그룹화

3. **에러 처리**
   - RUN_ERROR 이벤트로 에러 전달
   - 예외 발생 시 traceback 출력

4. **상태 예측 설정**
   - @copilotkit_customize_config로 예측 대상 지정
   - tool_name, tool_argument 정확히 설정
   - 파싱 가능한 JSON 구조 사용

5. **성능 최적화**
   - yield_control()로 이벤트 루프 제어권 양보
   - Priority 이벤트 최소화 (긴급 상황만)
   - 불필요한 상태 전송 방지

Common Pitfalls
---------------

1. **컨텍스트 미설정**: queue_put() 호출 전 copilotkit_run() 실행 필요
2. **이벤트 순서 불일치**: END 없이 새 START 전송 금지
3. **상태 예측 설정 오류**: tool_name이 실제 액션명과 불일치
4. **무한 루프**: is_finished 또는 should_exit 미설정
5. **Partial JSON 파싱 실패**: 잘못된 JSON 형식의 인자

See Also
--------
protocol : 이벤트 타입 정의 및 직렬화
agent : 에이전트 실행 래퍼
action : 액션 정의 및 실행
"""

import asyncio
import contextvars
import json
import traceback
from typing import Callable
from pydantic import BaseModel
from typing_extensions import Any, Dict, Optional, List, TypedDict, cast
from partialjson.json_parser import JSONParser as PartialJSONParser

from .protocol import (
    RuntimeEvent,
    RuntimeEventTypes,
    RuntimeMetaEventName,
    emit_runtime_event,
    emit_runtime_events,
    agent_state_message,
    AgentStateMessage,
    PredictStateConfig,
    RuntimeProtocolEvent
)

async def yield_control():
    """
    이벤트 루프에 제어권을 양보하는 헬퍼 함수

    현재 코루틴의 실행을 일시 중단하고 이벤트 루프에 제어권을 넘깁니다.
    다른 코루틴이나 이벤트를 처리할 기회를 제공합니다.

    Notes
    -----
    - asyncio.sleep(0)과 유사하지만 더 명시적
    - 우선순위 이벤트 처리를 위해 사용
    - 이벤트 큐 처리 후 제어권 양보에 사용

    동작 원리:
    1. 현재 실행 중인 이벤트 루프 가져오기
    2. 즉시 완료될 Future 생성
    3. call_soon으로 Future를 다음 이벤트 루프 틱에 완료
    4. Future가 완료될 때까지 대기 (다른 태스크 실행 기회 제공)

    Examples
    --------
    >>> async def process_events():
    ...     for i in range(100):
    ...         print(f"Processing {i}")
    ...         await yield_control()  # 다른 태스크에 기회 제공
    ...         await process_item(i)

    See Also
    --------
    queue_put : 이벤트 큐에 넣기 (내부적으로 yield_control 사용)
    """
    loop = asyncio.get_running_loop()
    future = loop.create_future()
    loop.call_soon(future.set_result, None)
    await future


class CopilotKitRunExecution(TypedDict):
    """
    CopilotKit 런 실행 상태를 추적하는 TypedDict

    에이전트 실행의 전체 상태를 관리합니다.
    이벤트 처리, 상태 예측, 실행 제어에 필요한 모든 정보를 포함합니다.

    Attributes
    ----------
    thread_id : str
        대화 스레드 고유 ID
        동일한 스레드의 메시지들을 그룹화
    agent_name : str
        에이전트 이름
        AgentStateMessage에서 사용
    run_id : str
        실행 고유 ID (LangGraph run ID)
        단일 실행 세션 추적용
    should_exit : bool
        에이전트 종료 플래그
        META_EVENT.EXIT로 설정
    node_name : str
        현재 실행 중인 노드 이름 (LangGraph 노드)
        NODE_STARTED 이벤트에서 업데이트
    is_finished : bool
        실행 완료 플래그
        RUN_FINISHED 또는 RUN_ERROR 시 True
    predict_state_configuration : Dict[str, PredictStateConfig]
        상태 예측 설정 딕셔너리
        키: 상태 키 (예: "user_name")
        값: PredictStateConfig (tool_name, tool_argument)
        @copilotkit_customize_config로 설정
    predicted_state : Dict[str, Any]
        예측된 상태 딕셔너리
        실시간 액션 인자 파싱으로 채워짐
        NODE_FINISHED 시 초기화
    argument_buffer : str
        액션 인자 누적 버퍼
        ACTION_EXECUTION_ARGS 이벤트 청크를 누적
        Partial JSON 파싱에 사용
    current_tool_call : Optional[str]
        현재 실행 중인 툴/액션 이름
        ACTION_EXECUTION_START 시 설정
        NODE_FINISHED 시 None으로 초기화
    state : Dict[str, Any]
        에이전트 전체 상태
        RUN_STARTED, NODE_STARTED, NODE_FINISHED에서 업데이트
        AgentStateMessage로 클라이언트에 전송

    Examples
    --------
    기본 실행 상태 생성:

    >>> execution = CopilotKitRunExecution(
    ...     thread_id="thread_abc123",
    ...     agent_name="research_assistant",
    ...     run_id="run_xyz789",
    ...     should_exit=False,
    ...     node_name="",
    ...     is_finished=False,
    ...     predict_state_configuration={},
    ...     predicted_state={},
    ...     argument_buffer="",
    ...     current_tool_call=None,
    ...     state={}
    ... )

    상태 예측 설정 포함:

    >>> execution = CopilotKitRunExecution(
    ...     thread_id="thread_1",
    ...     agent_name="assistant",
    ...     run_id="run_1",
    ...     should_exit=False,
    ...     node_name="agent_node",
    ...     is_finished=False,
    ...     predict_state_configuration={
    ...         "user_name": {
    ...             "tool_name": "update_user",
    ...             "tool_argument": "name"
    ...         },
    ...         "user_email": {
    ...             "tool_name": "update_user",
    ...             "tool_argument": "email"
    ...         }
    ...     },
    ...     predicted_state={},
    ...     argument_buffer="",
    ...     current_tool_call=None,
    ...     state={"current_user": "john"}
    ... )

    Notes
    -----
    - 이 객체는 copilotkit_run() 함수에서 관리됩니다
    - 직접 수정하지 말고 이벤트를 통해 업데이트하세요
    - 컨텍스트 변수로 저장되어 비동기 태스크 간 공유됩니다

    State Lifecycle:
    1. RUN_STARTED: 초기 상태 설정
    2. NODE_STARTED: 노드 진입 시 상태 업데이트
    3. ACTION_EXECUTION_*: 예측 상태 실시간 업데이트
    4. NODE_FINISHED: 예측 관련 필드 초기화
    5. RUN_FINISHED: is_finished = True

    See Also
    --------
    copilotkit_run : 메인 런 루프 (execution 관리)
    get_context_execution : 현재 execution 가져오기
    set_context_execution : execution 설정
    PredictStateConfig : 상태 예측 설정 타입
    """
    thread_id: str
    agent_name: str
    run_id: str
    should_exit: bool
    node_name: str
    is_finished: bool
    predict_state_configuration: Dict[str, PredictStateConfig]
    predicted_state: Dict[str, Any]
    argument_buffer: str
    current_tool_call: Optional[str]
    state: Dict[str, Any]

_CONTEXT_QUEUE = contextvars.ContextVar('queue', default=None)
_CONTEXT_EXECUTION = contextvars.ContextVar('execution', default=None)

def get_context_queue() -> asyncio.Queue:
    """
    현재 태스크의 컨텍스트에서 이벤트 큐를 가져오는 함수

    비동기 태스크 간 안전하게 공유되는 이벤트 큐를 반환합니다.
    queue_put()에서 내부적으로 사용됩니다.

    Returns
    -------
    asyncio.Queue
        현재 컨텍스트의 이벤트 큐

    Raises
    ------
    RuntimeError
        컨텍스트 큐가 설정되지 않은 경우
        copilotkit_run() 외부에서 호출 시 발생

    Examples
    --------
    >>> async def my_handler():
    ...     # copilotkit_run() 내부에서만 사용 가능
    ...     queue = get_context_queue()
    ...     await queue.put(some_event)

    Notes
    -----
    - 일반적으로 직접 호출하지 않고 queue_put() 사용
    - copilotkit_run()이 자동으로 큐를 설정합니다
    - 비동기 컨텍스트 변수로 스레드 안전 보장

    See Also
    --------
    set_context_queue : 컨텍스트 큐 설정
    queue_put : 이벤트를 큐에 넣는 권장 방법
    """
    q = _CONTEXT_QUEUE.get()
    if q is None:
        raise RuntimeError("No context queue is set!")
    return q

def set_context_queue(q: asyncio.Queue) -> contextvars.Token:
    """
    현재 태스크의 컨텍스트에 이벤트 큐를 설정하는 함수

    Parameters
    ----------
    q : asyncio.Queue
        설정할 이벤트 큐

    Returns
    -------
    contextvars.Token
        컨텍스트 리셋용 토큰
        reset_context_queue()에 전달

    Notes
    -----
    - copilotkit_run()에서 자동으로 호출됩니다
    - 일반적으로 직접 호출 불필요
    - finally 블록에서 reset_context_queue() 호출 필요

    See Also
    --------
    reset_context_queue : 컨텍스트 큐 리셋
    copilotkit_run : 큐 설정 및 관리
    """
    token = _CONTEXT_QUEUE.set(cast(Any, q))
    return token

def reset_context_queue(token: contextvars.Token):
    """
    컨텍스트 큐를 이전 상태로 리셋하는 함수

    Parameters
    ----------
    token : contextvars.Token
        set_context_queue()에서 반환된 토큰

    Notes
    -----
    - 항상 finally 블록에서 호출해야 합니다
    - 컨텍스트 오염 방지
    - copilotkit_run()에서 자동 처리

    See Also
    --------
    set_context_queue : 컨텍스트 큐 설정
    copilotkit_run : 큐 생명주기 관리
    """
    _CONTEXT_QUEUE.reset(token)

def get_context_execution() -> CopilotKitRunExecution:
    """
    현재 태스크의 컨텍스트에서 실행 상태를 가져오는 함수

    에이전트 핸들러 내에서 현재 실행 상태에 접근할 때 사용합니다.
    thread_id, run_id, state 등의 정보를 조회할 수 있습니다.

    Returns
    -------
    CopilotKitRunExecution
        현재 실행 상태 객체

    Examples
    --------
    >>> async def my_action_handler():
    ...     execution = get_context_execution()
    ...     print(f"Thread ID: {execution['thread_id']}")
    ...     print(f"Current state: {execution['state']}")
    ...     return {"result": "success"}

    Notes
    -----
    - copilotkit_run() 내부에서만 사용 가능
    - 실행 상태를 직접 수정하지 마세요 (읽기 전용으로 사용)
    - 상태 변경은 이벤트를 통해 수행

    See Also
    --------
    set_context_execution : 실행 상태 설정
    CopilotKitRunExecution : 실행 상태 TypedDict
    """
    return cast(CopilotKitRunExecution, _CONTEXT_EXECUTION.get())

def set_context_execution(execution: CopilotKitRunExecution) -> contextvars.Token:
    """
    현재 태스크의 컨텍스트에 실행 상태를 설정하는 함수

    Parameters
    ----------
    execution : CopilotKitRunExecution
        설정할 실행 상태 객체

    Returns
    -------
    contextvars.Token
        컨텍스트 리셋용 토큰
        reset_context_execution()에 전달

    Notes
    -----
    - copilotkit_run()에서 자동으로 호출됩니다
    - 일반적으로 직접 호출 불필요
    - finally 블록에서 reset_context_execution() 호출 필요

    See Also
    --------
    reset_context_execution : 실행 상태 리셋
    copilotkit_run : 실행 상태 설정 및 관리
    """
    token = _CONTEXT_EXECUTION.set(cast(Any, execution))
    return token

def reset_context_execution(token: contextvars.Token):
    """
    컨텍스트 실행 상태를 이전 상태로 리셋하는 함수

    Parameters
    ----------
    token : contextvars.Token
        set_context_execution()에서 반환된 토큰

    Notes
    -----
    - 항상 finally 블록에서 호출해야 합니다
    - 컨텍스트 오염 방지
    - copilotkit_run()에서 자동 처리

    See Also
    --------
    set_context_execution : 실행 상태 설정
    copilotkit_run : 실행 상태 생명주기 관리
    """
    _CONTEXT_EXECUTION.reset(token)


async def queue_put(*events: RuntimeEvent, priority: bool = False):
    """
    이벤트를 큐에 넣는 헬퍼 함수

    에이전트 핸들러에서 Runtime 이벤트를 전송할 때 사용합니다.
    우선순위 옵션을 지원하여 긴급 이벤트를 먼저 처리할 수 있습니다.

    Parameters
    ----------
    *events : RuntimeEvent
        큐에 넣을 이벤트들 (가변 인자)
    priority : bool, default=False
        우선순위 플래그
        True: 즉시 큐에 넣음 (긴급 이벤트용)
        False: yield_control() 후 넣음 (일반 이벤트용)

    Examples
    --------
    일반 이벤트 전송:

    >>> async def send_message():
    ...     await queue_put(
    ...         text_message_start(message_id="msg_1"),
    ...         text_message_content(message_id="msg_1", content="Hello"),
    ...         text_message_end(message_id="msg_1")
    ...     )

    우선순위 이벤트 (긴급):

    >>> async def emergency_exit():
    ...     await queue_put(
    ...         meta_event(name=RuntimeMetaEventName.EXIT, value=True),
    ...         priority=True
    ...     )

    Notes
    -----
    - copilotkit_run() 컨텍스트 내에서만 사용 가능
    - 우선순위 이벤트는 즉시 처리되지만 남용 금지
    - yield_control()을 통해 이벤트 루프 제어권 양보

    동작 원리:
    1. priority=False: yield_control() 호출 (우선순위 이벤트 먼저 처리 기회 제공)
    2. get_context_queue()로 큐 가져오기
    3. 모든 이벤트를 순서대로 큐에 넣기
    4. yield_control() 호출 (reader가 이벤트 처리할 기회 제공)

    Raises
    ------
    RuntimeError
        컨텍스트 큐가 설정되지 않은 경우

    See Also
    --------
    yield_control : 이벤트 루프 제어권 양보
    get_context_queue : 컨텍스트 큐 가져오기
    copilotkit_run : 메인 런 루프
    """
    if not priority:
        # yield control so that priority events can be processed first
        await yield_control()

    q = get_context_queue()
    for event in events:
        await q.put(event)

    # yield control so that the reader can process the event
    await yield_control()


def _to_dict_if_pydantic(obj):
    """
    Pydantic 모델을 딕셔너리로 변환하는 내부 유틸리티 함수

    Parameters
    ----------
    obj : Any
        변환할 객체

    Returns
    -------
    Any
        Pydantic BaseModel인 경우 model_dump() 결과
        그 외의 경우 원본 객체

    Notes
    -----
    - _filter_state()에서 내부적으로 사용
    - Pydantic v2 model_dump() 사용
    """
    if isinstance(obj, BaseModel):
        return obj.model_dump()
    return obj

def _filter_state(
        *,
        state: Dict[str, Any],
        exclude_keys: Optional[List[str]] = None
    ) -> Dict[str, Any]:
    """
    에이전트 상태에서 특정 키를 제외하는 내부 유틸리티 함수

    AgentStateMessage로 전송하기 전에 불필요한 필드를 제거합니다.
    기본적으로 "messages"와 "id" 필드를 제외합니다.

    Parameters
    ----------
    state : Dict[str, Any]
        필터링할 상태 딕셔너리
    exclude_keys : Optional[List[str]], default=["messages", "id"]
        제외할 키 리스트

    Returns
    -------
    Dict[str, Any]
        필터링된 상태 딕셔너리

    Examples
    --------
    >>> state = {
    ...     "messages": [...],
    ...     "id": "thread_123",
    ...     "user_name": "Alice",
    ...     "user_email": "alice@example.com"
    ... }
    >>> filtered = _filter_state(state=state)
    >>> print(filtered)
    {'user_name': 'Alice', 'user_email': 'alice@example.com'}

    커스텀 제외 키:

    >>> filtered = _filter_state(
    ...     state=state,
    ...     exclude_keys=["messages", "id", "user_email"]
    ... )
    >>> print(filtered)
    {'user_name': 'Alice'}

    Notes
    -----
    - "messages"와 "id"는 클라이언트로 전송 불필요
    - Pydantic 모델은 자동으로 딕셔너리로 변환
    - handle_runtime_event()에서 내부적으로 사용

    See Also
    --------
    _to_dict_if_pydantic : Pydantic 모델 변환
    """
    state = _to_dict_if_pydantic(state)
    exclude_keys = exclude_keys or ["messages", "id"]
    return {k: v for k, v in state.items() if k not in exclude_keys}


async def copilotkit_run(
        fn: Callable,
        *,
        execution: CopilotKitRunExecution
):
    """
    CopilotKit 메인 런 루프 - 에이전트 실행 및 이벤트 스트리밍

    에이전트 함수를 실행하고 이벤트를 JSON Lines 형식으로 스트리밍하는
    비동기 제너레이터입니다. SSE(Server-Sent Events)를 통한 실시간 통신을 지원합니다.

    Parameters
    ----------
    fn : Callable
        실행할 에이전트 함수 (비동기 함수)
        내부에서 queue_put()으로 이벤트 전송
    execution : CopilotKitRunExecution
        실행 상태 객체
        thread_id, agent_name, run_id 등 초기화 필요

    Yields
    ------
    str
        JSON Lines 형식의 이벤트 문자열
        각 yield는 하나 이상의 JSON 라인 포함

    Examples
    --------
    기본 사용법:

    >>> async def my_agent():
    ...     await queue_put(text_message_start(message_id="msg_1"))
    ...     await queue_put(text_message_content(message_id="msg_1", content="Hello"))
    ...     await queue_put(text_message_end(message_id="msg_1"))
    ...
    >>> execution = CopilotKitRunExecution(
    ...     thread_id="thread_1",
    ...     agent_name="assistant",
    ...     run_id="run_1",
    ...     should_exit=False,
    ...     node_name="",
    ...     is_finished=False,
    ...     predict_state_configuration={},
    ...     predicted_state={},
    ...     argument_buffer="",
    ...     current_tool_call=None,
    ...     state={}
    ... )
    >>> async for json_line in copilotkit_run(my_agent, execution=execution):
    ...     print(f"Event: {json_line}")

    FastAPI SSE 통합:

    >>> from fastapi import FastAPI
    >>> from fastapi.responses import StreamingResponse
    >>>
    >>> app = FastAPI()
    >>>
    >>> @app.get("/stream")
    >>> async def stream_agent():
    ...     async def event_generator():
    ...         async for json_line in copilotkit_run(my_agent, execution=execution):
    ...             yield f"data: {json_line}\n\n"
    ...     return StreamingResponse(event_generator(), media_type="text/event-stream")

    Notes
    -----
    런 루프 동작 순서:
    1. 로컬 이벤트 큐 생성
    2. 컨텍스트 설정 (queue, execution)
    3. 에이전트 태스크 생성 및 시작
    4. 이벤트 루프:
       - 큐에서 이벤트 가져오기
       - handle_runtime_event()로 처리
       - JSON Lines 반환 (yield)
       - is_finished 체크
    5. 태스크 완료 대기
    6. 컨텍스트 정리 (finally)

    이벤트 처리:
    - Protocol Events: 클라이언트로 직접 전송
    - Meta Events: 실행 설정 변경 (전송 안 함)
    - Lifecycle Events: AgentStateMessage로 변환 후 전송

    컨텍스트 관리:
    - 모든 비동기 태스크에서 queue_put() 사용 가능
    - get_context_execution()로 상태 접근 가능
    - finally 블록에서 자동 정리

    Warnings
    --------
    - fn()은 반드시 비동기 함수여야 합니다
    - execution 객체를 직접 수정하지 마세요
    - is_finished 또는 should_exit를 설정하지 않으면 무한 루프 발생 가능

    See Also
    --------
    queue_put : 이벤트를 큐에 넣는 함수
    handle_runtime_event : 이벤트 처리 로직
    CopilotKitRunExecution : 실행 상태 TypedDict
    """
    local_queue = asyncio.Queue()
    token_queue = set_context_queue(local_queue)
    token_execution = set_context_execution(execution)

    task = asyncio.create_task(
        fn()
    )
    try:
        while True:
            event = await local_queue.get()
            local_queue.task_done()

            json_lines = handle_runtime_event(
                event=event,
                execution=execution
            )

            if json_lines is not None:
                yield json_lines

            if execution["is_finished"]:
                break

            # return control to the containing run loop to send events
            await yield_control()

        await task

    finally:
        reset_context_queue(token_queue)
        reset_context_execution(token_execution)

def handle_runtime_event(
        *,
        event: RuntimeEvent,
        execution: CopilotKitRunExecution
) -> Optional[str]:
    """
    Runtime 이벤트를 처리하고 JSON Lines로 직렬화하는 핵심 함수

    이벤트 타입에 따라 적절한 처리를 수행합니다:
    - Protocol Events: 클라이언트로 직접 전송
    - Meta Events: 실행 설정 업데이트
    - Lifecycle Events: 상태 업데이트 및 AgentStateMessage 생성

    Parameters
    ----------
    event : RuntimeEvent
        처리할 런타임 이벤트
    execution : CopilotKitRunExecution
        현재 실행 상태 (업데이트됨)

    Returns
    -------
    Optional[str]
        JSON Lines 문자열 (클라이언트로 전송용)
        설정 업데이트 이벤트의 경우 None

    Event Handling Logic
    --------------------

    **Protocol Events** (직접 전송):
    - TEXT_MESSAGE_START/CONTENT/END
    - ACTION_EXECUTION_START/ARGS/END/RESULT
    - AGENT_STATE_MESSAGE

    ACTION_EXECUTION_START/ARGS의 경우 추가로:
    - predict_state() 호출하여 상태 예측
    - 예측 상태가 있으면 AgentStateMessage 추가 전송

    **Meta Events** (설정 업데이트, 전송 안 함):
    - PREDICT_STATE: execution["predict_state_configuration"] 업데이트
    - EXIT: execution["should_exit"] 업데이트

    **Lifecycle Events** (상태 추적):
    - RUN_STARTED: execution["state"] 초기화
    - NODE_STARTED: node_name, state 업데이트 → AgentStateMessage 전송 (active=True)
    - NODE_FINISHED: 예측 상태 초기화, state 업데이트 → AgentStateMessage 전송 (active=False)
    - RUN_FINISHED: execution["is_finished"] = True (런 루프 종료)
    - RUN_ERROR: 에러 출력, is_finished = True

    Examples
    --------
    Protocol Event 처리:

    >>> event = text_message_content(message_id="msg_1", content="Hello")
    >>> json_lines = handle_runtime_event(event=event, execution=execution)
    >>> print(json_lines)
    {"type": "TextMessageContent", "messageId": "msg_1", "content": "Hello"}
    <BLANKLINE>

    Meta Event 처리 (반환값 None):

    >>> event = meta_event(
    ...     name=RuntimeMetaEventName.PREDICT_STATE,
    ...     value={"user_name": {"tool_name": "update_user", "tool_argument": "name"}}
    ... )
    >>> result = handle_runtime_event(event=event, execution=execution)
    >>> print(result)
    None
    >>> print(execution["predict_state_configuration"])
    {'user_name': {'tool_name': 'update_user', 'tool_argument': 'name'}}

    Lifecycle Event 처리:

    >>> event = {
    ...     "type": RuntimeEventTypes.NODE_STARTED,
    ...     "node_name": "agent_node",
    ...     "state": {"user": "Alice"}
    ... }
    >>> json_lines = handle_runtime_event(event=event, execution=execution)
    >>> # AgentStateMessage가 반환됨
    >>> print(execution["node_name"])
    'agent_node'

    Notes
    -----
    상태 예측 플로우:
    1. ACTION_EXECUTION_START: current_tool_call 설정, buffer 초기화
    2. ACTION_EXECUTION_ARGS: buffer에 인자 누적, predict_state() 호출
    3. predict_state(): Partial JSON 파싱 → predicted_state 업데이트
    4. NODE_FINISHED: 모든 예측 관련 필드 초기화

    에러 처리:
    - RUN_ERROR 이벤트 수신 시 traceback 출력
    - Exception 객체: format_exception()으로 전체 스택 출력
    - 문자열: 그대로 출력
    - 항상 is_finished = True 설정 (런 루프 종료)

    See Also
    --------
    predict_state : 실시간 상태 예측 로직
    copilotkit_run : 메인 런 루프 (이 함수 호출)
    emit_runtime_events : JSON Lines 직렬화
    _filter_state : 상태 필터링 (messages, id 제외)
    """

    if event["type"] in [
        RuntimeEventTypes.TEXT_MESSAGE_START,
        RuntimeEventTypes.TEXT_MESSAGE_CONTENT,
        RuntimeEventTypes.TEXT_MESSAGE_END,
        RuntimeEventTypes.ACTION_EXECUTION_START,
        RuntimeEventTypes.ACTION_EXECUTION_ARGS,
        RuntimeEventTypes.ACTION_EXECUTION_END,
        RuntimeEventTypes.ACTION_EXECUTION_RESULT,
        RuntimeEventTypes.AGENT_STATE_MESSAGE
    ]:
        events: List[RuntimeProtocolEvent] = [cast(RuntimeProtocolEvent, event)]
        if event["type"] in [
            RuntimeEventTypes.ACTION_EXECUTION_START,
            RuntimeEventTypes.ACTION_EXECUTION_ARGS
        ]:
            message = predict_state(
                thread_id=execution["thread_id"],
                agent_name=execution["agent_name"],
                run_id=execution["run_id"],
                event=event,
                execution=execution,
            )
            if message is not None:
                events.append(message)
        return emit_runtime_events(*events)

    if event["type"] == RuntimeEventTypes.META_EVENT:
        if event["name"] == RuntimeMetaEventName.PREDICT_STATE:
            execution["predict_state_configuration"] = event["value"]
            return None
        if event["name"] == RuntimeMetaEventName.EXIT:
            execution["should_exit"] = event["value"]
            return None
        return None

    if event["type"] == RuntimeEventTypes.RUN_STARTED:
        execution["state"] = event["state"]
        return None

    if event["type"] == RuntimeEventTypes.NODE_STARTED:
        execution["node_name"] = event["node_name"]
        execution["state"] = event["state"]

        return emit_runtime_event(
            agent_state_message(
                thread_id=execution["thread_id"],
                agent_name=execution["agent_name"],
                node_name=execution["node_name"],
                run_id=execution["run_id"],
                active=True,
                role="assistant",
                state=json.dumps(_filter_state(state=execution["state"])),
                running=True
            )
        )

    if event["type"] == RuntimeEventTypes.NODE_FINISHED:

        # reset the predict state configuration at the end of the method execution
        execution["predict_state_configuration"] = {}
        execution["current_tool_call"] = None
        execution["argument_buffer"] = ""
        execution["predicted_state"] = {}
        execution["state"] = event["state"]

        return emit_runtime_event(
            agent_state_message(
                thread_id=execution["thread_id"],
                agent_name=execution["agent_name"],
                node_name=execution["node_name"],
                run_id=execution["run_id"],
                active=False,
                role="assistant",
                state=json.dumps(_filter_state(state=execution["state"])),
                running=True
            )
        )

    if event["type"] == RuntimeEventTypes.RUN_FINISHED:
        execution["is_finished"] = True
        return None

    if event["type"] == RuntimeEventTypes.RUN_ERROR:
        print("Flow execution error", flush=True)
        error_info = event["error"]

        if isinstance(error_info, Exception):
            # If it's an exception, print the traceback
            print("Exception occurred:", flush=True)
            print(
                ''.join(
                    traceback.format_exception(
                        None,
                        error_info,
                        error_info.__traceback__
                    )
                ),
                flush=True
            )
        else:
            # Otherwise, assume it's a string and print it
            print(error_info, flush=True)

        execution["is_finished"] = True
        return None

def predict_state(
        *,
        thread_id: str,
        agent_name: str,
        run_id: str,
        event: Any,
        execution: CopilotKitRunExecution,
) -> Optional[AgentStateMessage]:
    """
    실시간 상태 예측 - 액션 인자를 스트리밍 중 파싱하여 상태 업데이트

    액션 실행 중 스트리밍되는 인자를 Partial JSON 파싱으로 실시간 파싱하여
    클라이언트 상태를 즉시 업데이트합니다. @copilotkit_customize_config로
    설정된 predict_state 설정을 기반으로 동작합니다.

    Parameters
    ----------
    thread_id : str
        대화 스레드 ID
    agent_name : str
        에이전트 이름
    run_id : str
        실행 ID
    event : Any
        처리할 이벤트 (ACTION_EXECUTION_START 또는 ACTION_EXECUTION_ARGS)
    execution : CopilotKitRunExecution
        현재 실행 상태 (업데이트됨)

    Returns
    -------
    Optional[AgentStateMessage]
        예측된 상태를 포함한 AgentStateMessage
        업데이트할 상태가 없거나 파싱 실패 시 None

    Algorithm
    ---------
    1. **ACTION_EXECUTION_START 처리**:
       - current_tool_call = actionName
       - argument_buffer = "" (초기화)

    2. **ACTION_EXECUTION_ARGS 처리**:
       - argument_buffer에 인자 청크 누적
       - 현재 tool_call이 predict_state_configuration에 있는지 확인
       - PartialJSONParser로 불완전한 JSON 파싱 시도
       - predict_state_configuration 순회:
         - tool_name 일치 확인
         - tool_argument 지정된 경우: 해당 인자 값만 추출
         - tool_argument 없는 경우: 전체 인자 객체 사용
         - predicted_state[state_key] = 추출된 값
       - 업데이트가 있으면 AgentStateMessage 생성 및 반환

    Examples
    --------
    Predict State 설정:

    >>> @copilotkit_action(name="update_user")
    ... @copilotkit_customize_config(
    ...     predict_state={
    ...         "user_name": {
    ...             "tool_name": "update_user",
    ...             "tool_argument": "name"
    ...         },
    ...         "user_email": {
    ...             "tool_name": "update_user",
    ...             "tool_argument": "email"
    ...         }
    ...     }
    ... )
    ... async def update_user(name: str, email: str):
    ...     return {"status": "updated"}

    실시간 상태 예측 플로우:

    >>> # 1. ACTION_EXECUTION_START
    >>> event_start = {
    ...     "type": RuntimeEventTypes.ACTION_EXECUTION_START,
    ...     "actionName": "update_user"
    ... }
    >>> result = predict_state(..., event=event_start, execution=execution)
    >>> # current_tool_call = "update_user", argument_buffer = ""

    >>> # 2. ACTION_EXECUTION_ARGS (첫 청크)
    >>> event_args1 = {
    ...     "type": RuntimeEventTypes.ACTION_EXECUTION_ARGS,
    ...     "args": '{"name": "Al'
    ... }
    >>> result = predict_state(..., event=event_args1, execution=execution)
    >>> # PartialJSONParser 파싱 실패 또는 부분 파싱 → None or partial update

    >>> # 3. ACTION_EXECUTION_ARGS (두 번째 청크)
    >>> event_args2 = {
    ...     "type": RuntimeEventTypes.ACTION_EXECUTION_ARGS,
    ...     "args": 'ice", "email": "alice@'
    ... }
    >>> result = predict_state(..., event=event_args2, execution=execution)
    >>> # 누적: '{"name": "Alice", "email": "alice@'
    >>> # Partial 파싱 성공 → {"name": "Alice"}
    >>> # predicted_state["user_name"] = "Alice"
    >>> # AgentStateMessage 반환

    >>> # 4. ACTION_EXECUTION_ARGS (마지막 청크)
    >>> event_args3 = {
    ...     "type": RuntimeEventTypes.ACTION_EXECUTION_ARGS,
    ...     "args": 'example.com"}'
    ... }
    >>> result = predict_state(..., event=event_args3, execution=execution)
    >>> # 누적: '{"name": "Alice", "email": "alice@example.com"}'
    >>> # 완전한 JSON 파싱 성공
    >>> # predicted_state["user_name"] = "Alice"
    >>> # predicted_state["user_email"] = "alice@example.com"
    >>> # AgentStateMessage 반환

    Notes
    -----
    Partial JSON Parsing:
    - 불완전한 JSON 문자열도 파싱 가능
    - 닫히지 않은 중괄호, 따옴표 처리
    - 파싱 실패 시 None 반환 (예외 무시)

    State Merging:
    - 기존 state와 predicted_state 병합
    - predicted_state가 우선 순위 (덮어쓰기)
    - _filter_state()로 불필요한 필드 제거

    Configuration Matching:
    - tool_name이 current_tool_call과 일치해야 함
    - tool_argument 지정: 특정 인자 값만 매핑
    - tool_argument 없음: 전체 인자 객체 매핑

    Performance:
    - 매 ARGS 청크마다 호출됨 (빈번)
    - 파싱 실패 시 빠르게 반환 (try-except)
    - 업데이트 없으면 None 반환 (불필요한 메시지 방지)

    See Also
    --------
    handle_runtime_event : predict_state() 호출
    copilotkit_customize_config : predict_state 설정 데코레이터
    PartialJSONParser : 부분 JSON 파싱 라이브러리
    """
    
    if event["type"] == RuntimeEventTypes.ACTION_EXECUTION_START:
        execution["current_tool_call"] = event["actionName"]
        execution["argument_buffer"] = ""
    elif event["type"] == RuntimeEventTypes.ACTION_EXECUTION_ARGS:
        execution["argument_buffer"] += event["args"]

        tool_names = [
            config.get("tool_name")
            for config in execution["predict_state_configuration"].values()
        ]

        if execution["current_tool_call"] not in tool_names:
            return None

        current_arguments = {}
        try:
            current_arguments = PartialJSONParser().parse(execution["argument_buffer"])
        except:  # pylint: disable=bare-except
            return None

        emit_update = False
        for k, v in execution["predict_state_configuration"].items():
            if v["tool_name"] == execution["current_tool_call"]:
                tool_argument = v.get("tool_argument")
                if tool_argument is not None:
                    argument_value = current_arguments.get(tool_argument)
                    if argument_value is not None:
                        execution["predicted_state"][k] = argument_value
                        emit_update = True
                else:
                    execution["predicted_state"][k] = current_arguments
                    emit_update = True

        if emit_update:
            return agent_state_message(
                thread_id=thread_id,
                agent_name=agent_name,
                node_name=execution["node_name"],
                run_id=run_id,
                active=True,
                role="assistant",
                state=json.dumps(
                    _filter_state(
                        state={
                            **(
                                execution["state"].model_dump()
                                if isinstance(execution["state"], BaseModel)
                                else execution["state"]
                            ),
                            **execution["predicted_state"]
                        }
                    )
                ),
                running=True
            )

        return None
