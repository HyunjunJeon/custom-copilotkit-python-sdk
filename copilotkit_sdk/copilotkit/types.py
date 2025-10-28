"""
CopilotKit 타입 정의 - 메시지 및 설정 구조

이 모듈은 CopilotKit SDK 전반에서 사용되는 핵심 타입 정의를 제공합니다.
주로 메시지 형식, 상태 설정, 메타 이벤트 등의 TypedDict와 Enum을 포함합니다.

주요 타입 카테고리:
1. 메시지 타입: TextMessage, ActionExecutionMessage, ResultMessage
2. 설정 타입: IntermediateStateConfig
3. 이벤트 타입: MetaEvent
4. Enum: MessageRole

Message Type Hierarchy:
```mermaid
graph TD
    subgraph "Base Type"
    M[Message]
    end

    subgraph "Message Types"
    TM[TextMessage]
    AE[ActionExecutionMessage]
    RM[ResultMessage]
    end

    subgraph "Message Role"
    R[MessageRole Enum]
    U[USER]
    A[ASSISTANT]
    S[SYSTEM]
    end

    subgraph "Conversion Flow"
    CK[CopilotKit Format]
    LC[LangChain Format]
    end

    M -->|extends| TM
    M -->|extends| AE
    M -->|extends| RM

    R --> U
    R --> A
    R --> S

    TM -->|has| R

    TM -->|id, createdAt, role, content| CK
    AE -->|id, name, arguments| CK
    RM -->|id, result, actionName| CK

    CK <-->|copilotkit_messages_to_langchain| LC
    LC <-->|langchain_messages_to_copilotkit| CK

    style M fill:#e1f5ff
    style TM fill:#fff4e1
    style AE fill:#ffe1e1
    style RM fill:#e1ffe1
```

Message Types 상세:

1. **TextMessage**: 일반 텍스트 메시지
   - 사용자 입력, AI 응답, 시스템 메시지
   - role: user, assistant, system
   - LangChain의 HumanMessage, AIMessage, SystemMessage로 변환

2. **ActionExecutionMessage**: 도구/액션 호출 메시지
   - AI가 도구를 호출할 때 사용
   - name: 도구 이름, arguments: 도구 인자
   - LangChain의 AIMessage(tool_calls=[...])로 변환

3. **ResultMessage**: 도구 실행 결과 메시지
   - 도구 실행 완료 후 결과 전달
   - actionExecutionId: 어떤 액션의 결과인지
   - LangChain의 ToolMessage로 변환

Message Flow Example:

    # 1. 사용자 메시지
    TextMessage(
        id="msg_1",
        role="user",
        content="Send email to john@example.com",
        createdAt="2024-01-01T00:00:00Z"
    )

    # 2. AI가 도구 호출
    ActionExecutionMessage(
        id="action_1",
        parentMessageId="msg_2",  # AI 메시지 ID
        name="SendEmail",
        arguments={"to": "john@example.com", "subject": "Hello"},
        createdAt="2024-01-01T00:00:01Z"
    )

    # 3. 도구 실행 결과
    ResultMessage(
        id="result_1",
        actionExecutionId="action_1",
        actionName="SendEmail",
        result='{"status": "sent", "message_id": "123"}',
        createdAt="2024-01-01T00:00:02Z"
    )

Usage in LangGraph Conversion:

    from copilotkit.langgraph import (
        copilotkit_messages_to_langchain,
        langchain_messages_to_copilotkit
    )

    # CopilotKit → LangChain
    converter = copilotkit_messages_to_langchain()
    langchain_msgs = converter([text_msg, action_msg, result_msg])

    # LangChain → CopilotKit
    copilotkit_msgs = langchain_messages_to_copilotkit(langchain_msgs)

See Also
--------
- copilotkit.langgraph: 메시지 변환 유틸리티
- copilotkit.sdk: SDK 메인 클래스
"""

from typing import TypedDict
from enum import Enum
from typing_extensions import NotRequired

class MessageRole(Enum):
    """
    메시지 역할 열거형

    텍스트 메시지의 발신자 역할을 정의합니다.
    LangChain의 메시지 타입과 매핑되어 변환에 사용됩니다.

    Attributes
    ----------
    ASSISTANT : str
        AI 어시스턴트의 응답 메시지 (value: "assistant")
        LangChain의 AIMessage에 해당
    SYSTEM : str
        시스템 메시지, 일반적으로 지시사항이나 컨텍스트 (value: "system")
        LangChain의 SystemMessage에 해당
    USER : str
        사용자 입력 메시지 (value: "user")
        LangChain의 HumanMessage에 해당
    """
    ASSISTANT = "assistant"
    SYSTEM = "system"
    USER = "user"

class Message(TypedDict):
    """
    메시지 기본 타입

    모든 메시지 타입이 공통으로 가지는 필드를 정의합니다.
    TextMessage, ActionExecutionMessage, ResultMessage의 부모 타입입니다.

    Attributes
    ----------
    id : str
        메시지 고유 식별자 (UUID 형식 권장)
        메시지 추적 및 관계 설정에 사용
    createdAt : str
        메시지 생성 시간 (ISO 8601 형식 권장)
        예: "2024-01-01T12:00:00Z"
    """
    id: str
    createdAt: str

class TextMessage(Message):
    """
    텍스트 메시지

    사용자 입력, AI 응답, 시스템 메시지를 나타냅니다.
    대화의 주요 내용을 담는 메시지 타입입니다.

    Attributes
    ----------
    id : str
        메시지 고유 식별자 (Message로부터 상속)
    createdAt : str
        메시지 생성 시간 (Message로부터 상속)
    parentMessageId : str, optional
        부모 메시지 ID
        대화 스레드나 응답 체인을 구성할 때 사용
    role : MessageRole
        메시지 역할 (USER, ASSISTANT, SYSTEM)
    content : str
        메시지 텍스트 내용

    Examples
    --------
    >>> # 사용자 메시지
    >>> user_msg: TextMessage = {
    ...     "id": "msg_1",
    ...     "createdAt": "2024-01-01T12:00:00Z",
    ...     "role": MessageRole.USER,
    ...     "content": "Hello, how are you?"
    ... }
    >>>
    >>> # AI 응답
    >>> ai_msg: TextMessage = {
    ...     "id": "msg_2",
    ...     "createdAt": "2024-01-01T12:00:01Z",
    ...     "parentMessageId": "msg_1",
    ...     "role": MessageRole.ASSISTANT,
    ...     "content": "I'm doing great! How can I help you?"
    ... }
    """
    parentMessageId: NotRequired[str]
    role: MessageRole
    content: str

class ActionExecutionMessage(Message):
    """
    액션 실행 메시지

    AI가 도구/액션을 호출할 때 생성되는 메시지입니다.
    함수 호출 파라미터와 메타데이터를 포함합니다.

    Attributes
    ----------
    id : str
        액션 실행 고유 식별자 (Message로부터 상속)
        ResultMessage의 actionExecutionId와 매칭됨
    createdAt : str
        액션 호출 시간 (Message로부터 상속)
    parentMessageId : str, optional
        부모 AI 메시지 ID
        하나의 AI 응답에서 여러 도구를 호출할 경우 동일한 parentMessageId를 가짐
    name : str
        액션/도구 이름 (예: "SendEmail", "SearchWeb")
    arguments : dict
        액션에 전달할 인자들 (JSON 직렬화 가능해야 함)

    Examples
    --------
    >>> # 이메일 전송 액션
    >>> action_msg: ActionExecutionMessage = {
    ...     "id": "action_1",
    ...     "createdAt": "2024-01-01T12:00:02Z",
    ...     "parentMessageId": "msg_2",
    ...     "name": "SendEmail",
    ...     "arguments": {
    ...         "to": "user@example.com",
    ...         "subject": "Hello",
    ...         "body": "Test email"
    ...     }
    ... }

    Notes
    -----
    - LangChain의 AIMessage(tool_calls=[...])로 변환됩니다
    - 같은 parentMessageId를 가진 여러 액션은 하나의 AIMessage로 통합됩니다
    """
    parentMessageId: NotRequired[str]
    name: str
    arguments: dict

class ResultMessage(Message):
    """
    액션 실행 결과 메시지

    도구/액션 실행이 완료된 후 그 결과를 담는 메시지입니다.
    ActionExecutionMessage와 쌍을 이루어 도구 호출 사이클을 완성합니다.

    Attributes
    ----------
    id : str
        결과 메시지 고유 식별자 (Message로부터 상속)
    createdAt : str
        결과 생성 시간 (Message로부터 상속)
    actionExecutionId : str
        어떤 ActionExecutionMessage의 결과인지 식별
        ActionExecutionMessage의 id와 매칭됨
    actionName : str
        실행된 액션 이름 (ActionExecutionMessage의 name과 동일)
    result : str
        액션 실행 결과 (문자열 형태, JSON 직렬화된 객체도 가능)

    Examples
    --------
    >>> # 이메일 전송 결과
    >>> result_msg: ResultMessage = {
    ...     "id": "result_1",
    ...     "createdAt": "2024-01-01T12:00:03Z",
    ...     "actionExecutionId": "action_1",
    ...     "actionName": "SendEmail",
    ...     "result": '{"status": "sent", "message_id": "abc123"}'
    ... }

    Notes
    -----
    - LangChain의 ToolMessage로 변환됩니다
    - result는 문자열이므로 복잡한 객체는 JSON으로 직렬화해야 합니다
    - actionExecutionId로 ActionExecutionMessage와 연결됩니다
    """
    actionExecutionId: str
    actionName: str
    result: str

class IntermediateStateConfig(TypedDict):
    """
    중간 상태 스트리밍 설정

    도구 호출의 인자를 LangGraph 상태로 실시간 스트리밍하기 위한 설정입니다.
    copilotkit_customize_config의 emit_intermediate_state 파라미터에서 사용됩니다.

    Attributes
    ----------
    state_key : str
        상태에 저장할 키 이름
        예: "search_results", "analysis_steps"
    tool : str
        모니터링할 도구 이름
        이 도구의 호출이 감지되면 인자를 상태로 방출
    tool_argument : str, optional
        특정 인자만 추출할 경우 인자 이름
        생략하면 모든 인자가 state_key에 저장됨

    Examples
    --------
    >>> # SearchTool의 "steps" 인자를 state["search_steps"]로 스트리밍
    >>> config1: IntermediateStateConfig = {
    ...     "state_key": "search_steps",
    ...     "tool": "SearchTool",
    ...     "tool_argument": "steps"
    ... }
    >>>
    >>> # AnalyzeTool의 모든 인자를 state["analysis"]로 스트리밍
    >>> config2: IntermediateStateConfig = {
    ...     "state_key": "analysis",
    ...     "tool": "AnalyzeTool"
    ... }

    See Also
    --------
    copilotkit.langgraph.copilotkit_customize_config : 이 설정을 사용하는 함수
    """
    state_key: str
    tool: str
    tool_argument: NotRequired[str]

class MetaEvent(TypedDict):
    """
    메타 이벤트

    LangGraph 인터럽트 재개 시 클라이언트로부터 전달받는 이벤트입니다.
    사용자가 인터럽트에 응답한 내용을 담아 에이전트에 전달합니다.

    Attributes
    ----------
    name : str
        이벤트 이름 (일반적으로 "interrupt_response" 등)
    response : str, optional
        사용자 응답 내용
        인터럽트 메시지에 대한 사용자의 답변

    Examples
    --------
    >>> # 사용자가 "yes"로 응답한 경우
    >>> meta_event: MetaEvent = {
    ...     "name": "interrupt_response",
    ...     "response": "yes"
    ... }

    See Also
    --------
    copilotkit.langgraph.copilotkit_interrupt : 인터럽트를 생성하는 함수
    copilotkit.sdk.CopilotKitRemoteEndpoint.execute_agent : meta_events를 받는 메서드
    """
    name: str
    response: NotRequired[str]