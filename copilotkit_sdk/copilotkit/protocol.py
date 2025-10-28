"""
CopilotKit Runtime Protocol - 이벤트 타입 정의 및 직렬화

이 모듈은 CopilotKit Runtime Protocol의 핵심 이벤트 타입을 정의합니다.
클라이언트와 서버 간의 실시간 통신에 사용되는 모든 이벤트 타입과
직렬화 유틸리티를 제공합니다.

주요 개념
--------

**Runtime Protocol**:
  - 클라이언트 ↔ 서버 간 실시간 이벤트 스트리밍 프로토콜
  - Server-Sent Events (SSE) 기반
  - JSON 형식으로 직렬화
  - 타입 안정성을 위한 TypedDict 사용

**Event Categories**:
  1. **Protocol Events** (RuntimeProtocolEvent): 비즈니스 로직 이벤트
     - Text Messages: 텍스트 메시지 (start, content, end)
     - Action Executions: 액션 실행 (start, args, end, result)
     - Agent State: 에이전트 상태
     - Meta Events: 메타 이벤트 (인터럽트, 종료 등)

  2. **Lifecycle Events** (RuntimeLifecycleEvent): 실행 라이프사이클 이벤트
     - Run Events: 실행 시작/종료/에러
     - Node Events: LangGraph 노드 시작/종료

**Event Lifecycle**:
  모든 이벤트는 start → (content/args) → end 패턴을 따릅니다.

Event Protocol Flow
-------------------

```mermaid
stateDiagram-v2
    [*] --> Idle

    Idle --> TextMessageStart: AI 응답 시작
    TextMessageStart --> TextMessageContent: 텍스트 청크
    TextMessageContent --> TextMessageContent: 추가 청크 (반복)
    TextMessageContent --> TextMessageEnd: 메시지 완료
    TextMessageEnd --> Idle

    Idle --> ActionExecutionStart: 액션 호출 시작
    ActionExecutionStart --> ActionExecutionArgs: 액션 인자
    ActionExecutionArgs --> ActionExecutionEnd: 액션 인자 완료
    ActionExecutionEnd --> Idle

    Idle --> ActionExecutionResult: 액션 결과 전달
    ActionExecutionResult --> Idle

    Idle --> AgentStateMessage: 에이전트 상태 업데이트
    AgentStateMessage --> Idle

    Idle --> MetaEvent: 메타 이벤트 (인터럽트, 종료 등)
    MetaEvent --> Idle

    note right of TextMessageStart
        텍스트 메시지 라이프사이클:
        1. START (메시지 ID 생성)
        2. CONTENT (스트리밍 청크들)
        3. END (메시지 완료)
    end note

    note right of ActionExecutionStart
        액션 실행 라이프사이클:
        1. START (액션 실행 ID 생성)
        2. ARGS (인자 전달)
        3. END (호출 완료)
        4. RESULT (실행 결과)
    end note
```

Event Types Overview
---------------------

### Text Message Events
텍스트 메시지를 스트리밍으로 전송하는 이벤트 시퀀스:

1. **TextMessageStart**: 새 메시지 시작 (messageId 생성)
2. **TextMessageContent**: 메시지 내용 청크 (여러 번 반복 가능)
3. **TextMessageEnd**: 메시지 완료

```python
# 예시: "Hello, world!" 메시지 스트리밍
yield text_message_start(message_id="msg_1")
yield text_message_content(message_id="msg_1", content="Hello, ")
yield text_message_content(message_id="msg_1", content="world!")
yield text_message_end(message_id="msg_1")
```

### Action Execution Events
액션 실행을 나타내는 이벤트 시퀀스:

1. **ActionExecutionStart**: 액션 실행 시작 (actionExecutionId 생성)
2. **ActionExecutionArgs**: 액션 인자 전달 (JSON 문자열)
3. **ActionExecutionEnd**: 액션 호출 완료
4. **ActionExecutionResult**: 액션 실행 결과 (별도 이벤트)

```python
# 예시: send_email 액션 실행
yield action_execution_start(
    action_execution_id="action_1",
    action_name="send_email"
)
yield action_execution_args(
    action_execution_id="action_1",
    args='{"to": "user@example.com"}'
)
yield action_execution_end(action_execution_id="action_1")

# 나중에 결과 전달
yield action_execution_result(
    action_execution_id="action_1",
    action_name="send_email",
    result='{"status": "sent"}'
)
```

### Agent State Event
에이전트의 현재 상태를 클라이언트에 전달:

```python
yield agent_state_message(
    thread_id="thread_123",
    agent_name="assistant",
    node_name="agent_node",
    run_id="run_456",
    active=True,
    role="assistant",
    state='{"key": "value"}',
    running=True
)
```

### Meta Events
특수 이벤트 (인터럽트, 상태 예측, 종료 등):

```python
# 인터럽트 이벤트
yield meta_event(
    name=RuntimeMetaEventName.LANG_GRAPH_INTERRUPT_EVENT,
    value={"message": "Waiting for user input"}
)

# 종료 이벤트
yield meta_event(
    name=RuntimeMetaEventName.EXIT,
    value={}
)
```

### Lifecycle Events
LangGraph 실행 라이프사이클 (내부용):

- **RunStarted/Finished/Error**: 전체 실행 시작/완료/에러
- **NodeStarted/Finished**: 개별 노드 시작/완료

Serialization
-------------

이벤트는 JSON Lines 형식으로 직렬화됩니다:

```python
# 단일 이벤트
event_json = emit_runtime_event(
    text_message_content(message_id="msg_1", content="Hello")
)
# 출력: '{"type": "TextMessageContent", "messageId": "msg_1", "content": "Hello"}\n'

# 여러 이벤트
events_json = emit_runtime_events(
    text_message_start(message_id="msg_1"),
    text_message_content(message_id="msg_1", content="Hello"),
    text_message_end(message_id="msg_1")
)
# 출력: 3줄의 JSON (각각 \n으로 구분)
```

Best Practices
--------------

1. **이벤트 순서 준수**:
   - 반드시 START → CONTENT/ARGS → END 순서 지키기
   - END 없이 START만 보내면 클라이언트가 대기 상태로 남음

2. **ID 일관성**:
   - 같은 메시지/액션의 모든 이벤트는 동일한 ID 사용
   - messageId, actionExecutionId를 정확하게 매칭

3. **JSON 직렬화**:
   - args, result, state는 JSON 문자열로 직렬화
   - 유효한 JSON 형식 확인

4. **에러 처리**:
   - 액션 실행 중 에러 발생 시 ActionExecutionResult로 에러 정보 전달
   - result 필드에 에러 JSON 포함

5. **스트리밍 효율**:
   - TextMessageContent는 적절한 청크 크기로 분할
   - 너무 작으면 오버헤드, 너무 크면 지연

Common Pitfalls
---------------

- ❌ **START 없이 CONTENT 전송**:
  ```python
  yield text_message_content(message_id="msg_1", content="Hello")  # START 없음!
  ```

- ❌ **END 누락**:
  ```python
  yield text_message_start(message_id="msg_1")
  yield text_message_content(message_id="msg_1", content="Hello")
  # END 없음! 클라이언트가 무한 대기
  ```

- ❌ **ID 불일치**:
  ```python
  yield text_message_start(message_id="msg_1")
  yield text_message_content(message_id="msg_2", content="Hello")  # 다른 ID!
  yield text_message_end(message_id="msg_1")
  ```

- ❌ **JSON 직렬화 오류**:
  ```python
  yield action_execution_args(
      action_execution_id="action_1",
      args="not a json"  # 유효한 JSON 아님!
  )
  ```

- ✅ **올바른 사용**:
  ```python
  msg_id = "msg_1"
  yield text_message_start(message_id=msg_id)
  yield text_message_content(message_id=msg_id, content="Hello")
  yield text_message_end(message_id=msg_id)
  ```

Usage Example
-------------

### 완전한 메시지 스트리밍 예제

```python
from copilotkit.protocol import (
    text_message_start, text_message_content, text_message_end,
    emit_runtime_events
)

def stream_ai_response(message_id: str, full_text: str):
    '''AI 응답을 청크 단위로 스트리밍합니다'''
    events = []

    # 1. 메시지 시작
    events.append(text_message_start(message_id=message_id))

    # 2. 텍스트를 청크로 분할하여 전송
    chunk_size = 10
    for i in range(0, len(full_text), chunk_size):
        chunk = full_text[i:i+chunk_size]
        events.append(text_message_content(
            message_id=message_id,
            content=chunk
        ))

    # 3. 메시지 종료
    events.append(text_message_end(message_id=message_id))

    # 4. 직렬화하여 반환
    return emit_runtime_events(*events)

# 사용
sse_data = stream_ai_response("msg_123", "Hello, how can I help you today?")
# SSE로 클라이언트에 전송
```

### 액션 실행 및 결과 처리 예제

```python
from copilotkit.protocol import (
    action_execution_start, action_execution_args,
    action_execution_end, action_execution_result,
    emit_runtime_event
)
import json

def execute_action_with_events(action_name: str, arguments: dict):
    '''액션을 실행하고 이벤트를 생성합니다'''
    action_id = f"action_{uuid.uuid4()}"

    # 1. 액션 시작
    yield emit_runtime_event(action_execution_start(
        action_execution_id=action_id,
        action_name=action_name
    ))

    # 2. 인자 전달
    yield emit_runtime_event(action_execution_args(
        action_execution_id=action_id,
        args=json.dumps(arguments)
    ))

    # 3. 액션 호출 완료
    yield emit_runtime_event(action_execution_end(
        action_execution_id=action_id
    ))

    # 4. 액션 실제 실행
    try:
        result = perform_action(action_name, arguments)
        yield emit_runtime_event(action_execution_result(
            action_execution_id=action_id,
            action_name=action_name,
            result=json.dumps(result)
        ))
    except Exception as e:
        yield emit_runtime_event(action_execution_result(
            action_execution_id=action_id,
            action_name=action_name,
            result=json.dumps({"error": str(e)})
        ))
```

See Also
--------

- copilotkit.runloop: 이벤트 처리 및 전송을 담당하는 런타임 루프
- copilotkit.integrations.fastapi: SSE 엔드포인트 구현
- copilotkit.types: CopilotKit 메시지 타입 정의
"""

import json
from enum import Enum
from typing import Union, Optional
from typing_extensions import TypedDict, Literal, Any, Dict

class RuntimeEventTypes(Enum):
    """
    Runtime 이벤트 타입 열거형

    CopilotKit Runtime Protocol에서 사용되는 모든 이벤트 타입을 정의합니다.
    각 이벤트는 특정 상황에서 클라이언트로 전송되며, 타입에 따라 페이로드가 다릅니다.

    Attributes
    ----------
    TEXT_MESSAGE_START : str
        텍스트 메시지 시작 (값: "TextMessageStart")
        새로운 AI 응답 메시지가 시작될 때
    TEXT_MESSAGE_CONTENT : str
        텍스트 메시지 내용 (값: "TextMessageContent")
        AI 응답의 일부 (청크)가 생성될 때
    TEXT_MESSAGE_END : str
        텍스트 메시지 종료 (값: "TextMessageEnd")
        AI 응답이 완전히 완료되었을 때
    ACTION_EXECUTION_START : str
        액션 실행 시작 (값: "ActionExecutionStart")
        AI가 액션/도구 호출을 시작할 때
    ACTION_EXECUTION_ARGS : str
        액션 실행 인자 (값: "ActionExecutionArgs")
        액션 호출의 인자가 전달될 때
    ACTION_EXECUTION_END : str
        액션 실행 종료 (값: "ActionExecutionEnd")
        액션 호출이 완료되었을 때
    ACTION_EXECUTION_RESULT : str
        액션 실행 결과 (값: "ActionExecutionResult")
        액션 실행 결과가 반환될 때
    AGENT_STATE_MESSAGE : str
        에이전트 상태 메시지 (값: "AgentStateMessage")
        에이전트의 상태가 업데이트될 때
    META_EVENT : str
        메타 이벤트 (값: "MetaEvent")
        특수 이벤트 (인터럽트, 종료 등)
    RUN_STARTED : str
        실행 시작 (값: "RunStarted")
        LangGraph 실행이 시작될 때
    RUN_FINISHED : str
        실행 완료 (값: "RunFinished")
        LangGraph 실행이 완료될 때
    RUN_ERROR : str
        실행 에러 (값: "RunError")
        LangGraph 실행 중 에러 발생 시
    NODE_STARTED : str
        노드 시작 (값: "NodeStarted")
        LangGraph 노드 실행 시작 시
    NODE_FINISHED : str
        노드 완료 (값: "NodeFinished")
        LangGraph 노드 실행 완료 시

    Examples
    --------
    >>> event_type = RuntimeEventTypes.TEXT_MESSAGE_START
    >>> print(event_type.value)
    'TextMessageStart'

    >>> # 이벤트 딕셔너리에 사용
    >>> event = {
    ...     "type": RuntimeEventTypes.TEXT_MESSAGE_CONTENT,
    ...     "messageId": "msg_1",
    ...     "content": "Hello"
    ... }
    """
    TEXT_MESSAGE_START = "TextMessageStart"
    TEXT_MESSAGE_CONTENT = "TextMessageContent"
    TEXT_MESSAGE_END = "TextMessageEnd"
    ACTION_EXECUTION_START = "ActionExecutionStart"
    ACTION_EXECUTION_ARGS = "ActionExecutionArgs"
    ACTION_EXECUTION_END = "ActionExecutionEnd"
    ACTION_EXECUTION_RESULT = "ActionExecutionResult"
    AGENT_STATE_MESSAGE = "AgentStateMessage"
    META_EVENT = "MetaEvent"
    RUN_STARTED = "RunStarted"
    RUN_FINISHED = "RunFinished"
    RUN_ERROR = "RunError"
    NODE_STARTED = "NodeStarted"
    NODE_FINISHED = "NodeFinished"

class RuntimeMetaEventName(Enum):
    """
    Runtime 메타 이벤트 이름 열거형

    특수한 상황에서 사용되는 메타 이벤트의 이름을 정의합니다.
    메타 이벤트는 일반적인 메시지/액션 플로우와 다른 특별한 이벤트입니다.

    Attributes
    ----------
    LANG_GRAPH_INTERRUPT_EVENT : str
        LangGraph 인터럽트 이벤트 (값: "LangGraphInterruptEvent")
        에이전트가 사용자 입력을 기다릴 때
    PREDICT_STATE : str
        상태 예측 (값: "PredictState")
        도구 호출 인자를 상태로 예측할 때
    EXIT : str
        종료 (값: "Exit")
        에이전트 실행을 명시적으로 종료할 때

    Examples
    --------
    >>> meta_name = RuntimeMetaEventName.LANG_GRAPH_INTERRUPT_EVENT
    >>> print(meta_name.value)
    'LangGraphInterruptEvent'

    >>> # MetaEvent에 사용
    >>> event = {
    ...     "type": RuntimeEventTypes.META_EVENT,
    ...     "name": RuntimeMetaEventName.EXIT,
    ...     "value": {}
    ... }
    """
    LANG_GRAPH_INTERRUPT_EVENT = "LangGraphInterruptEvent"
    PREDICT_STATE = "PredictState"
    EXIT = "Exit"


class TextMessageStart(TypedDict):
    """
    텍스트 메시지 시작 이벤트

    새로운 AI 응답 메시지가 시작될 때 클라이언트로 전송됩니다.
    이 이벤트 이후 TextMessageContent 이벤트들이 스트리밍되며,
    마지막에 TextMessageEnd로 종료됩니다.

    Attributes
    ----------
    type : Literal[RuntimeEventTypes.TEXT_MESSAGE_START]
        이벤트 타입 (항상 TEXT_MESSAGE_START)
    messageId : str
        메시지 고유 ID (UUID 권장)
        후속 Content/End 이벤트에서 동일한 ID 사용
    parentMessageId : Optional[str]
        부모 메시지 ID (대화 스레드 구성용)
        첫 메시지인 경우 None

    Examples
    --------
    >>> event = text_message_start(
    ...     message_id="msg_123",
    ...     parent_message_id="msg_122"
    ... )
    >>> print(event)
    {
        'type': RuntimeEventTypes.TEXT_MESSAGE_START,
        'messageId': 'msg_123',
        'parentMessageId': 'msg_122'
    }
    """
    type: Literal[RuntimeEventTypes.TEXT_MESSAGE_START]
    messageId: str
    parentMessageId: Optional[str]

class TextMessageContent(TypedDict):
    """
    텍스트 메시지 내용 이벤트

    AI 응답의 일부(청크)를 클라이언트로 스트리밍합니다.
    하나의 메시지에 대해 여러 번 전송될 수 있습니다.

    Attributes
    ----------
    type : Literal[RuntimeEventTypes.TEXT_MESSAGE_CONTENT]
        이벤트 타입 (항상 TEXT_MESSAGE_CONTENT)
    messageId : str
        메시지 ID (TextMessageStart의 messageId와 동일)
    content : str
        메시지 내용 청크 (부분 문자열)

    Examples
    --------
    >>> # 긴 응답을 청크로 나누어 전송
    >>> yield text_message_content(message_id="msg_123", content="Hello, ")
    >>> yield text_message_content(message_id="msg_123", content="how are ")
    >>> yield text_message_content(message_id="msg_123", content="you?")

    Notes
    -----
    - content는 빈 문자열("")도 가능하지만 권장하지 않음
    - 적절한 청크 크기로 분할 (너무 작으면 오버헤드, 너무 크면 지연)
    """
    type: Literal[RuntimeEventTypes.TEXT_MESSAGE_CONTENT]
    messageId: str
    content: str

class TextMessageEnd(TypedDict):
    """
    텍스트 메시지 종료 이벤트

    AI 응답 메시지가 완전히 완료되었음을 클라이언트에 알립니다.
    이 이벤트 이후 해당 messageId로는 더 이상 Content가 전송되지 않습니다.

    Attributes
    ----------
    type : Literal[RuntimeEventTypes.TEXT_MESSAGE_END]
        이벤트 타입 (항상 TEXT_MESSAGE_END)
    messageId : str
        메시지 ID (TextMessageStart의 messageId와 동일)

    Examples
    --------
    >>> event = text_message_end(message_id="msg_123")
    >>> print(event)
    {
        'type': RuntimeEventTypes.TEXT_MESSAGE_END,
        'messageId': 'msg_123'
    }

    Notes
    -----
    - 반드시 TextMessageStart와 쌍을 이루어야 함
    - END 없이 START만 보내면 클라이언트가 무한 대기 상태
    """
    type: Literal[RuntimeEventTypes.TEXT_MESSAGE_END]
    messageId: str

class ActionExecutionStart(TypedDict):
    """
    액션 실행 시작 이벤트

    AI가 액션/도구를 호출하기 시작할 때 클라이언트로 전송됩니다.
    이 이벤트 이후 ActionExecutionArgs와 ActionExecutionEnd가 순서대로 전송됩니다.

    Attributes
    ----------
    type : Literal[RuntimeEventTypes.ACTION_EXECUTION_START]
        이벤트 타입 (항상 ACTION_EXECUTION_START)
    actionExecutionId : str
        액션 실행 고유 ID (UUID 권장)
        후속 Args/End/Result 이벤트에서 동일한 ID 사용
    actionName : str
        호출할 액션 이름
    parentMessageId : Optional[str]
        부모 AI 메시지 ID
        하나의 AI 응답에서 여러 액션을 호출할 수 있음

    Examples
    --------
    >>> event = action_execution_start(
    ...     action_execution_id="action_1",
    ...     action_name="send_email",
    ...     parent_message_id="msg_123"
    ... )
    >>> print(event)
    {
        'type': RuntimeEventTypes.ACTION_EXECUTION_START,
        'actionExecutionId': 'action_1',
        'actionName': 'send_email',
        'parentMessageId': 'msg_123'
    }
    """
    type: Literal[RuntimeEventTypes.ACTION_EXECUTION_START]
    actionExecutionId: str
    actionName: str
    parentMessageId: Optional[str]

class ActionExecutionArgs(TypedDict):
    """
    액션 실행 인자 이벤트

    액션 호출에 사용할 인자를 JSON 문자열로 전달합니다.
    ActionExecutionStart 이후, ActionExecutionEnd 이전에 전송됩니다.

    Attributes
    ----------
    type : Literal[RuntimeEventTypes.ACTION_EXECUTION_ARGS]
        이벤트 타입 (항상 ACTION_EXECUTION_ARGS)
    actionExecutionId : str
        액션 실행 ID (ActionExecutionStart의 actionExecutionId와 동일)
    args : str
        액션 인자 (JSON 문자열 형식)
        예: '{"to": "user@example.com", "subject": "Hello"}'

    Examples
    --------
    >>> import json
    >>> args_dict = {"to": "user@example.com", "subject": "Hello"}
    >>> event = action_execution_args(
    ...     action_execution_id="action_1",
    ...     args=json.dumps(args_dict)
    ... )
    >>> print(event)
    {
        'type': RuntimeEventTypes.ACTION_EXECUTION_ARGS,
        'actionExecutionId': 'action_1',
        'args': '{"to": "user@example.com", "subject": "Hello"}'
    }

    Notes
    -----
    - args는 반드시 유효한 JSON 문자열이어야 함
    - JSON 직렬화 가능한 타입만 포함 (dict, list, str, int, float, bool, None)
    """
    type: Literal[RuntimeEventTypes.ACTION_EXECUTION_ARGS]
    actionExecutionId: str
    args: str

class ActionExecutionEnd(TypedDict):
    """
    액션 실행 종료 이벤트

    액션 호출(인자 전달)이 완료되었음을 클라이언트에 알립니다.
    이 이벤트 이후 서버에서 실제 액션이 실행되며,
    나중에 ActionExecutionResult로 결과가 전달됩니다.

    Attributes
    ----------
    type : Literal[RuntimeEventTypes.ACTION_EXECUTION_END]
        이벤트 타입 (항상 ACTION_EXECUTION_END)
    actionExecutionId : str
        액션 실행 ID (ActionExecutionStart의 actionExecutionId와 동일)

    Examples
    --------
    >>> event = action_execution_end(action_execution_id="action_1")
    >>> print(event)
    {
        'type': RuntimeEventTypes.ACTION_EXECUTION_END,
        'actionExecutionId': 'action_1'
    }

    Notes
    -----
    - START → ARGS → END 순서를 반드시 지켜야 함
    - END 이후 실제 액션 실행 시작
    """
    type: Literal[RuntimeEventTypes.ACTION_EXECUTION_END]
    actionExecutionId: str

class ActionExecutionResult(TypedDict):
    """
    액션 실행 결과 이벤트

    액션 실행이 완료되고 결과를 클라이언트로 전달합니다.
    ActionExecutionEnd 이후 언제든지 전송될 수 있습니다.

    Attributes
    ----------
    type : Literal[RuntimeEventTypes.ACTION_EXECUTION_RESULT]
        이벤트 타입 (항상 ACTION_EXECUTION_RESULT)
    actionName : str
        실행된 액션 이름
    actionExecutionId : str
        액션 실행 ID (ActionExecutionStart의 actionExecutionId와 동일)
    result : str
        액션 실행 결과 (JSON 문자열 형식)
        성공 시: '{"status": "success", "data": ...}'
        실패 시: '{"error": "error message"}'

    Examples
    --------
    >>> import json
    >>> # 성공 결과
    >>> result_dict = {"status": "sent", "message_id": "email_123"}
    >>> event = action_execution_result(
    ...     action_execution_id="action_1",
    ...     action_name="send_email",
    ...     result=json.dumps(result_dict)
    ... )

    >>> # 에러 결과
    >>> error_dict = {"error": "Invalid email address"}
    >>> event = action_execution_result(
    ...     action_execution_id="action_1",
    ...     action_name="send_email",
    ...     result=json.dumps(error_dict)
    ... )

    Notes
    -----
    - result는 반드시 유효한 JSON 문자열이어야 함
    - 에러 발생 시에도 이 이벤트로 에러 정보 전달
    - END와 RESULT 사이에 시간차가 있을 수 있음 (액션 실행 시간)
    """
    type: Literal[RuntimeEventTypes.ACTION_EXECUTION_RESULT]
    actionName: str
    actionExecutionId: str
    result: str

class AgentStateMessage(TypedDict):
    """
    에이전트 상태 메시지 이벤트

    에이전트의 현재 상태를 클라이언트로 전달합니다.
    LangGraph 에이전트가 실행될 때 노드 전환, 상태 변경 등을 알립니다.

    Attributes
    ----------
    type : Literal[RuntimeEventTypes.AGENT_STATE_MESSAGE]
        이벤트 타입 (항상 AGENT_STATE_MESSAGE)
    threadId : str
        스레드 ID (대화 세션)
    agentName : str
        에이전트 이름
    nodeName : str
        현재 실행 중인 LangGraph 노드 이름
    runId : str
        LangGraph 실행 ID
    active : bool
        에이전트 활성화 여부
    role : str
        에이전트 역할 (예: "assistant")
    state : str
        에이전트 상태 (JSON 문자열)
    running : bool
        현재 실행 중인지 여부

    Examples
    --------
    >>> import json
    >>> state_dict = {"messages": [...], "key": "value"}
    >>> event = agent_state_message(
    ...     thread_id="thread_123",
    ...     agent_name="assistant",
    ...     node_name="agent_node",
    ...     run_id="run_456",
    ...     active=True,
    ...     role="assistant",
    ...     state=json.dumps(state_dict),
    ...     running=True
    ... )

    Notes
    -----
    - state는 JSON 문자열로 직렬화되어야 함
    - LangGraph 에이전트에서 주로 사용됨
    """
    type: Literal[RuntimeEventTypes.AGENT_STATE_MESSAGE]
    threadId: str
    agentName: str
    nodeName: str
    runId: str
    active: bool
    role: str
    state: str
    running: bool

class MetaEvent(TypedDict):
    """
    메타 이벤트

    일반적인 메시지/액션 플로우와 다른 특수 이벤트입니다.
    인터럽트, 상태 예측, 종료 등의 특별한 상황에서 사용됩니다.

    Attributes
    ----------
    type : Literal[RuntimeEventTypes.META_EVENT]
        이벤트 타입 (항상 META_EVENT)
    name : RuntimeMetaEventName
        메타 이벤트 이름
        - LANG_GRAPH_INTERRUPT_EVENT: 인터럽트 발생
        - PREDICT_STATE: 상태 예측
        - EXIT: 명시적 종료
    value : Any
        메타 이벤트 값 (이벤트 타입에 따라 다름)

    Examples
    --------
    >>> # 인터럽트 이벤트
    >>> event = meta_event(
    ...     name=RuntimeMetaEventName.LANG_GRAPH_INTERRUPT_EVENT,
    ...     value={"message": "Waiting for user confirmation"}
    ... )

    >>> # 종료 이벤트
    >>> event = meta_event(
    ...     name=RuntimeMetaEventName.EXIT,
    ...     value={}
    ... )

    >>> # 상태 예측 이벤트
    >>> event = meta_event(
    ...     name=RuntimeMetaEventName.PREDICT_STATE,
    ...     value={"state_key": "search_results", "tool": "SearchTool"}
    ... )

    Notes
    -----
    - value의 타입과 구조는 name에 따라 다름
    - 인터럽트 이벤트는 LangGraph의 copilotkit_interrupt()와 연동
    """
    type: Literal[RuntimeEventTypes.META_EVENT]
    name: RuntimeMetaEventName
    value: Any

class RunStarted(TypedDict):
    """
    실행 시작 이벤트 (Lifecycle)

    LangGraph 에이전트의 전체 실행이 시작될 때 발생합니다.
    내부용 이벤트로, 주로 디버깅 및 모니터링에 사용됩니다.

    Attributes
    ----------
    type : Literal[RuntimeEventTypes.RUN_STARTED]
        이벤트 타입 (항상 RUN_STARTED)
    state : Dict[str, Any]
        실행 시작 시점의 초기 상태

    Notes
    -----
    - RuntimeLifecycleEvent에 속하는 내부 이벤트
    - RuntimeProtocolEvent와 달리 클라이언트에 직접 노출되지 않을 수 있음
    """
    type: Literal[RuntimeEventTypes.RUN_STARTED]
    state: Dict[str, Any]

class RunFinished(TypedDict):
    """
    실행 완료 이벤트 (Lifecycle)

    LangGraph 에이전트의 전체 실행이 완료될 때 발생합니다.
    내부용 이벤트로, 주로 디버깅 및 모니터링에 사용됩니다.

    Attributes
    ----------
    type : Literal[RuntimeEventTypes.RUN_FINISHED]
        이벤트 타입 (항상 RUN_FINISHED)
    state : Dict[str, Any]
        실행 완료 시점의 최종 상태

    Notes
    -----
    - RuntimeLifecycleEvent에 속하는 내부 이벤트
    - 정상 완료 시 발생 (에러는 RunError)
    """
    type: Literal[RuntimeEventTypes.RUN_FINISHED]
    state: Dict[str, Any]

class RunError(TypedDict):
    """
    실행 에러 이벤트 (Lifecycle)

    LangGraph 에이전트 실행 중 에러가 발생할 때 발생합니다.
    내부용 이벤트로, 주로 디버깅 및 에러 추적에 사용됩니다.

    Attributes
    ----------
    type : Literal[RuntimeEventTypes.RUN_ERROR]
        이벤트 타입 (항상 RUN_ERROR)
    error : Any
        에러 정보 (Exception 객체 또는 에러 메시지)

    Notes
    -----
    - RuntimeLifecycleEvent에 속하는 내부 이벤트
    - 에러 발생 시 RunFinished 대신 이 이벤트 발생
    """
    type: Literal[RuntimeEventTypes.RUN_ERROR]
    error: Any

class NodeStarted(TypedDict):
    """
    노드 시작 이벤트 (Lifecycle)

    LangGraph 에이전트의 특정 노드 실행이 시작될 때 발생합니다.
    내부용 이벤트로, 주로 디버깅 및 실행 추적에 사용됩니다.

    Attributes
    ----------
    type : Literal[RuntimeEventTypes.NODE_STARTED]
        이벤트 타입 (항상 NODE_STARTED)
    node_name : str
        시작된 노드 이름
    state : Dict[str, Any]
        노드 시작 시점의 상태

    Notes
    -----
    - RuntimeLifecycleEvent에 속하는 내부 이벤트
    - LangGraph 그래프의 각 노드마다 발생
    """
    type: Literal[RuntimeEventTypes.NODE_STARTED]
    node_name: str
    state: Dict[str, Any]

class NodeFinished(TypedDict):
    """
    노드 완료 이벤트 (Lifecycle)

    LangGraph 에이전트의 특정 노드 실행이 완료될 때 발생합니다.
    내부용 이벤트로, 주로 디버깅 및 실행 추적에 사용됩니다.

    Attributes
    ----------
    type : Literal[RuntimeEventTypes.NODE_FINISHED]
        이벤트 타입 (항상 NODE_FINISHED)
    node_name : str
        완료된 노드 이름
    state : Dict[str, Any]
        노드 완료 시점의 상태

    Notes
    -----
    - RuntimeLifecycleEvent에 속하는 내부 이벤트
    - LangGraph 그래프의 각 노드마다 발생
    - NodeStarted와 쌍을 이룸
    """
    type: Literal[RuntimeEventTypes.NODE_FINISHED]
    node_name: str
    state: Dict[str, Any]

RuntimeProtocolEvent = Union[
    TextMessageStart,
    TextMessageContent,
    TextMessageEnd,
    ActionExecutionStart,
    ActionExecutionArgs,
    ActionExecutionEnd,
    ActionExecutionResult,
    AgentStateMessage,
    MetaEvent
]
"""
Runtime Protocol 이벤트 Union 타입

클라이언트와 서버 간 비즈니스 로직 통신에 사용되는 모든 이벤트 타입.
텍스트 메시지, 액션 실행, 에이전트 상태, 메타 이벤트를 포함합니다.

Examples
--------
>>> def handle_protocol_event(event: RuntimeProtocolEvent):
...     if event["type"] == RuntimeEventTypes.TEXT_MESSAGE_CONTENT:
...         print(event["content"])
...     elif event["type"] == RuntimeEventTypes.ACTION_EXECUTION_START:
...         print(f"Action: {event['actionName']}")
"""

RuntimeLifecycleEvent = Union[
    RunStarted,
    RunFinished,
    RunError,
    NodeStarted,
    NodeFinished,
]
"""
Runtime Lifecycle 이벤트 Union 타입

LangGraph 에이전트의 실행 라이프사이클을 추적하는 내부 이벤트 타입.
실행/노드 시작/완료/에러를 포함합니다.

Examples
--------
>>> def handle_lifecycle_event(event: RuntimeLifecycleEvent):
...     if event["type"] == RuntimeEventTypes.RUN_STARTED:
...         print("Run started with state:", event["state"])
...     elif event["type"] == RuntimeEventTypes.NODE_STARTED:
...         print(f"Node {event['node_name']} started")
"""

RuntimeEvent = Union[
    RuntimeProtocolEvent,
    RuntimeLifecycleEvent,
]
"""
모든 Runtime 이벤트의 Union 타입

RuntimeProtocolEvent와 RuntimeLifecycleEvent를 모두 포함하는 최상위 타입.

Examples
--------
>>> def handle_any_event(event: RuntimeEvent):
...     event_type = event["type"]
...     print(f"Received event: {event_type}")
"""


class PredictStateConfig(TypedDict):
    """
    상태 예측 설정

    도구 호출의 인자를 LangGraph 상태로 실시간 스트리밍하기 위한 설정입니다.
    특정 도구의 특정 인자를 추출하여 상태 키에 저장합니다.

    Attributes
    ----------
    tool_name : str
        모니터링할 도구 이름
        이 도구의 호출이 감지되면 인자를 상태로 방출
    tool_argument : Optional[str]
        특정 인자만 추출할 경우 인자 이름
        None이면 모든 인자를 포함

    Examples
    --------
    >>> # SearchTool의 "query" 인자를 상태로 스트리밍
    >>> config: PredictStateConfig = {
    ...     "tool_name": "SearchTool",
    ...     "tool_argument": "query"
    ... }

    >>> # AnalyzeTool의 모든 인자를 상태로 스트리밍
    >>> config: PredictStateConfig = {
    ...     "tool_name": "AnalyzeTool",
    ...     "tool_argument": None
    ... }

    Notes
    -----
    - copilotkit_customize_config의 predict_state 파라미터에서 사용
    - 도구 호출 시 실시간으로 클라이언트에 상태 업데이트 전송
    - PREDICT_STATE 메타 이벤트와 함께 동작

    See Also
    --------
    copilotkit.langgraph.copilotkit_customize_config : 이 설정을 사용하는 함수
    RuntimeMetaEventName.PREDICT_STATE : 관련 메타 이벤트
    """
    tool_name: str
    tool_argument: Optional[str]

def text_message_start(
        *,
        message_id: str,
        parent_message_id: Optional[str] = None
  ) -> TextMessageStart:
    """
    TextMessageStart 이벤트를 생성하는 헬퍼 함수

    새로운 AI 응답 메시지의 시작을 알리는 이벤트를 생성합니다.

    Parameters
    ----------
    message_id : str
        메시지 고유 ID
    parent_message_id : Optional[str], default=None
        부모 메시지 ID (대화 스레드용)

    Returns
    -------
    TextMessageStart
        텍스트 메시지 시작 이벤트

    Examples
    --------
    >>> event = text_message_start(message_id="msg_123")
    >>> print(event["type"])
    RuntimeEventTypes.TEXT_MESSAGE_START
    """
    return {
        "type": RuntimeEventTypes.TEXT_MESSAGE_START,
        "messageId": message_id,
        "parentMessageId": parent_message_id
    }

def text_message_content(*, message_id: str, content: str) -> TextMessageContent:
    """
    TextMessageContent 이벤트를 생성하는 헬퍼 함수

    AI 응답의 일부(청크)를 스트리밍하는 이벤트를 생성합니다.

    Parameters
    ----------
    message_id : str
        메시지 ID (TextMessageStart의 message_id와 동일)
    content : str
        메시지 내용 청크

    Returns
    -------
    TextMessageContent
        텍스트 메시지 내용 이벤트

    Examples
    --------
    >>> event = text_message_content(message_id="msg_123", content="Hello")
    >>> print(event["content"])
    'Hello'
    """
    return {
        "type": RuntimeEventTypes.TEXT_MESSAGE_CONTENT,
        "messageId": message_id,
        "content": content
    }

def text_message_end(*, message_id: str) -> TextMessageEnd:
    """
    TextMessageEnd 이벤트를 생성하는 헬퍼 함수

    AI 응답 메시지의 완료를 알리는 이벤트를 생성합니다.

    Parameters
    ----------
    message_id : str
        메시지 ID (TextMessageStart의 message_id와 동일)

    Returns
    -------
    TextMessageEnd
        텍스트 메시지 종료 이벤트

    Examples
    --------
    >>> event = text_message_end(message_id="msg_123")
    >>> print(event["type"])
    RuntimeEventTypes.TEXT_MESSAGE_END
    """
    return {
        "type": RuntimeEventTypes.TEXT_MESSAGE_END,
        "messageId": message_id
    }

def action_execution_start(
        *,
        action_execution_id: str,
        action_name: str,
        parent_message_id: Optional[str] = None
    ) -> ActionExecutionStart:
    """
    ActionExecutionStart 이벤트를 생성하는 헬퍼 함수

    액션 실행이 시작될 때 클라이언트에 알리기 위한 이벤트를 생성합니다.
    이 이벤트 이후 ActionExecutionArgs로 인자가 전달되고,
    ActionExecutionEnd로 인자 전달이 완료됩니다.

    Parameters
    ----------
    action_execution_id : str
        액션 실행 고유 ID (UUID 권장)
        후속 Args/End 이벤트에서 동일한 ID 사용
    action_name : str
        실행할 액션 이름
        @copilotkit_action 데코레이터로 등록된 액션명
    parent_message_id : Optional[str], default=None
        부모 메시지 ID (액션을 트리거한 메시지)

    Returns
    -------
    ActionExecutionStart
        액션 실행 시작 이벤트

    Examples
    --------
    >>> event = action_execution_start(
    ...     action_execution_id="exec_456",
    ...     action_name="search_database",
    ...     parent_message_id="msg_123"
    ... )
    >>> print(event["actionName"])
    'search_database'

    See Also
    --------
    action_execution_args : 액션 인자 전달
    action_execution_end : 액션 인자 전달 완료
    action_execution_result : 액션 실행 결과 반환
    """
    return {
        "type": RuntimeEventTypes.ACTION_EXECUTION_START,
        "actionExecutionId": action_execution_id,
        "actionName": action_name,
        "parentMessageId": parent_message_id
    }

def action_execution_args(*, action_execution_id: str, args: str) -> ActionExecutionArgs:
    """
    ActionExecutionArgs 이벤트를 생성하는 헬퍼 함수

    액션 실행에 필요한 인자를 전달하기 위한 이벤트를 생성합니다.
    인자는 JSON 직렬화된 문자열로 전달됩니다.

    Parameters
    ----------
    action_execution_id : str
        액션 실행 고유 ID
        ActionExecutionStart에서 사용한 것과 동일한 ID
    args : str
        JSON 직렬화된 액션 인자
        예: '{"query": "search term", "limit": 10}'

    Returns
    -------
    ActionExecutionArgs
        액션 인자 이벤트

    Examples
    --------
    >>> import json
    >>> args_dict = {"query": "Python", "max_results": 5}
    >>> event = action_execution_args(
    ...     action_execution_id="exec_456",
    ...     args=json.dumps(args_dict)
    ... )
    >>> print(event["args"])
    '{"query": "Python", "max_results": 5}'

    Notes
    -----
    - args는 반드시 유효한 JSON 문자열이어야 합니다
    - 복잡한 객체는 json.dumps()로 직렬화하세요
    - 액션 함수의 파라미터 타입과 일치해야 합니다

    See Also
    --------
    action_execution_start : 액션 실행 시작
    action_execution_end : 액션 인자 전달 완료
    """
    return {
        "type": RuntimeEventTypes.ACTION_EXECUTION_ARGS,
        "actionExecutionId": action_execution_id,
        "args": args
    }

def action_execution_end(*, action_execution_id: str) -> ActionExecutionEnd:
    """
    ActionExecutionEnd 이벤트를 생성하는 헬퍼 함수

    액션 인자 전달이 완료되었음을 알리는 이벤트를 생성합니다.
    이 이벤트 이후 서버는 액션을 실행하고 ActionExecutionResult를 반환합니다.

    Parameters
    ----------
    action_execution_id : str
        액션 실행 고유 ID
        ActionExecutionStart 및 ActionExecutionArgs에서 사용한 것과 동일한 ID

    Returns
    -------
    ActionExecutionEnd
        액션 인자 전달 완료 이벤트

    Examples
    --------
    >>> event = action_execution_end(action_execution_id="exec_456")
    >>> print(event["type"])
    <RuntimeEventTypes.ACTION_EXECUTION_END: 'ActionExecutionEnd'>

    Notes
    -----
    이 이벤트는 액션 실행의 완료가 아닌, 인자 전달의 완료를 나타냅니다.
    실제 액션 실행은 이 이벤트 이후 서버에서 수행되며,
    결과는 ActionExecutionResult로 전달됩니다.

    See Also
    --------
    action_execution_start : 액션 실행 시작
    action_execution_args : 액션 인자 전달
    action_execution_result : 액션 실행 결과 반환
    """
    return {
        "type": RuntimeEventTypes.ACTION_EXECUTION_END,
        "actionExecutionId": action_execution_id
    }

def action_execution_result(
        *,
        action_name: str,
        action_execution_id: str,
        result: str
    ) -> ActionExecutionResult:
    """
    ActionExecutionResult 이벤트를 생성하는 헬퍼 함수

    액션 실행 결과를 클라이언트로 전달하기 위한 이벤트를 생성합니다.
    결과는 JSON 직렬화된 문자열로 전달됩니다.

    Parameters
    ----------
    action_name : str
        실행된 액션 이름
    action_execution_id : str
        액션 실행 고유 ID
        ActionExecutionStart에서 사용한 것과 동일한 ID
    result : str
        JSON 직렬화된 액션 실행 결과
        성공 시 결과 데이터, 실패 시 에러 메시지

    Returns
    -------
    ActionExecutionResult
        액션 실행 결과 이벤트

    Examples
    --------
    성공 결과:

    >>> import json
    >>> result_data = {"found": 10, "items": ["item1", "item2"]}
    >>> event = action_execution_result(
    ...     action_name="search_database",
    ...     action_execution_id="exec_456",
    ...     result=json.dumps(result_data)
    ... )

    에러 결과:

    >>> error_data = {"error": "Database connection failed"}
    >>> event = action_execution_result(
    ...     action_name="search_database",
    ...     action_execution_id="exec_456",
    ...     result=json.dumps(error_data)
    ... )

    Notes
    -----
    - result는 반드시 유효한 JSON 문자열이어야 합니다
    - 액션 함수의 반환 타입과 일치해야 합니다
    - 에러 발생 시에도 JSON 형식으로 에러 정보를 전달하세요

    See Also
    --------
    action_execution_start : 액션 실행 시작
    action_execution_end : 액션 인자 전달 완료
    """
    return {
        "type": RuntimeEventTypes.ACTION_EXECUTION_RESULT,
        "actionName": action_name,
        "actionExecutionId": action_execution_id,
        "result": result
    }

def agent_state_message( # pylint: disable=too-many-arguments
        *,
        thread_id: str,
        agent_name: str,
        node_name: str,
        run_id: str,
        active: bool,
        role: str,
        state: str,
        running: bool
  ) -> AgentStateMessage:
    """
    AgentStateMessage 이벤트를 생성하는 헬퍼 함수

    LangGraph 에이전트의 현재 상태를 클라이언트로 전달하기 위한 이벤트를 생성합니다.
    에이전트 실행 흐름 추적 및 디버깅에 사용됩니다.

    Parameters
    ----------
    thread_id : str
        대화 스레드 ID
    agent_name : str
        에이전트 이름
    node_name : str
        현재 실행 중인 노드 이름 (LangGraph 노드)
    run_id : str
        실행 ID (LangGraph run ID)
    active : bool
        에이전트 활성화 상태
    role : str
        에이전트 역할 (예: "assistant", "user")
    state : str
        JSON 직렬화된 에이전트 상태
    running : bool
        에이전트 실행 중 여부

    Returns
    -------
    AgentStateMessage
        에이전트 상태 메시지 이벤트

    Examples
    --------
    >>> import json
    >>> state_data = {"current_step": "processing", "progress": 0.5}
    >>> event = agent_state_message(
    ...     thread_id="thread_789",
    ...     agent_name="research_agent",
    ...     node_name="search_node",
    ...     run_id="run_123",
    ...     active=True,
    ...     role="assistant",
    ...     state=json.dumps(state_data),
    ...     running=True
    ... )

    Notes
    -----
    - 이 이벤트는 LangGraph 기반 에이전트에서 주로 사용됩니다
    - state는 에이전트의 내부 상태를 JSON으로 직렬화한 것입니다
    - 에이전트 실행 흐름을 실시간으로 모니터링할 수 있습니다

    See Also
    --------
    NodeStarted : 노드 시작 이벤트
    NodeFinished : 노드 완료 이벤트
    """
    return {
        "type": RuntimeEventTypes.AGENT_STATE_MESSAGE,
        "threadId": thread_id,
        "agentName": agent_name,
        "nodeName": node_name,
        "runId": run_id,
        "active": active,
        "role": role,
        "state": state,
        "running": running
    }

def meta_event(*, name: RuntimeMetaEventName, value: Any) -> MetaEvent:
    """
    MetaEvent 이벤트를 생성하는 헬퍼 함수

    특수 제어 이벤트(인터럽트, 상태 예측, 종료)를 생성합니다.
    메타 이벤트는 에이전트 실행 흐름을 제어하거나 특수 동작을 트리거합니다.

    Parameters
    ----------
    name : RuntimeMetaEventName
        메타 이벤트 이름:
        - INTERRUPT: 에이전트 실행 일시 중단
        - PREDICT_STATE: 실시간 상태 예측 스트리밍
        - EXIT: 에이전트 실행 종료
    value : Any
        메타 이벤트 값 (이벤트 타입에 따라 다름)

    Returns
    -------
    MetaEvent
        메타 이벤트

    Examples
    --------
    Interrupt 이벤트:

    >>> event = meta_event(
    ...     name=RuntimeMetaEventName.INTERRUPT,
    ...     value="User requested pause"
    ... )

    Predict State 이벤트:

    >>> state_config = {
    ...     "state_key": "user_data",
    ...     "tool": "update_user",
    ...     "tool_argument": "profile"
    ... }
    >>> event = meta_event(
    ...     name=RuntimeMetaEventName.PREDICT_STATE,
    ...     value=state_config
    ... )

    Exit 이벤트:

    >>> event = meta_event(
    ...     name=RuntimeMetaEventName.EXIT,
    ...     value="Completed successfully"
    ... )

    Notes
    -----
    - INTERRUPT: 사용자 입력 대기나 중단점에서 사용
    - PREDICT_STATE: 실시간으로 툴 인자를 상태로 스트리밍
    - EXIT: 정상 종료 또는 에러 종료 시 사용

    See Also
    --------
    RuntimeMetaEventName : 메타 이벤트 이름 열거형
    MetaEvent : 메타 이벤트 TypedDict
    """
    return {
        "type": RuntimeEventTypes.META_EVENT,
        "name": name,
        "value": value
    }

def emit_runtime_events(*events: RuntimeProtocolEvent) -> str:
    """
    여러 Runtime Protocol 이벤트를 JSON Lines 형식으로 직렬화

    Server-Sent Events (SSE)를 통해 클라이언트로 전송하기 위해
    여러 이벤트를 JSON Lines 형식으로 직렬화합니다.
    각 이벤트는 별도의 줄에 JSON 객체로 출력됩니다.

    Parameters
    ----------
    *events : RuntimeProtocolEvent
        직렬화할 이벤트들 (가변 인자)

    Returns
    -------
    str
        JSON Lines 형식의 문자열
        각 줄은 하나의 JSON 이벤트 + 개행 문자

    Examples
    --------
    단일 이벤트:

    >>> msg_start = text_message_start(message_id="msg_1")
    >>> output = emit_runtime_events(msg_start)
    >>> print(output)
    {"type": "TextMessageStart", "messageId": "msg_1", "parentMessageId": null}
    <BLANKLINE>

    여러 이벤트:

    >>> msg_start = text_message_start(message_id="msg_1")
    >>> msg_content = text_message_content(message_id="msg_1", content="Hello")
    >>> msg_end = text_message_end(message_id="msg_1")
    >>> output = emit_runtime_events(msg_start, msg_content, msg_end)

    Notes
    -----
    - 각 이벤트는 별도의 줄에 출력됩니다 (JSON Lines 형식)
    - Enum 값은 자동으로 문자열로 변환됩니다
    - SSE 스트리밍에서 data: 접두사와 함께 사용됩니다
    - 마지막에 개행 문자가 추가됩니다

    직렬화 프로세스:
    1. 각 이벤트를 순회
    2. Enum 값을 .value로 변환
    3. JSON 문자열로 직렬화
    4. 개행 문자로 연결

    See Also
    --------
    emit_runtime_event : 단일 이벤트 직렬화
    """
    def serialize_event(event):
        # Convert enum values to their string representation
        if isinstance(event, dict):
            return {k: (v.value if isinstance(v, Enum) else v) for k, v in event.items()}
        return event

    return "\n".join(json.dumps(serialize_event(event)) for event in events) + "\n"

def emit_runtime_event(event: RuntimeProtocolEvent) -> str:
    """
    단일 Runtime Protocol 이벤트를 JSON Lines 형식으로 직렬화

    하나의 이벤트를 JSON Lines 형식으로 직렬화하는 헬퍼 함수입니다.
    내부적으로 emit_runtime_events()를 호출합니다.

    Parameters
    ----------
    event : RuntimeProtocolEvent
        직렬화할 단일 이벤트

    Returns
    -------
    str
        JSON Lines 형식의 문자열 (단일 줄 + 개행)

    Examples
    --------
    >>> msg_start = text_message_start(message_id="msg_1")
    >>> output = emit_runtime_event(msg_start)
    >>> print(output)
    {"type": "TextMessageStart", "messageId": "msg_1", "parentMessageId": null}
    <BLANKLINE>

    액션 실행 결과:

    >>> import json
    >>> result_data = {"status": "success", "data": [1, 2, 3]}
    >>> result_event = action_execution_result(
    ...     action_name="fetch_data",
    ...     action_execution_id="exec_1",
    ...     result=json.dumps(result_data)
    ... )
    >>> output = emit_runtime_event(result_event)

    Notes
    -----
    - emit_runtime_events()의 단순화된 버전
    - 단일 이벤트 전송 시 사용
    - 여러 이벤트는 emit_runtime_events() 사용 권장

    See Also
    --------
    emit_runtime_events : 여러 이벤트 직렬화
    """
    return emit_runtime_events(event)
