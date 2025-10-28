"""
CopilotKit Agent - 에이전트 추상 베이스 클래스

이 모듈은 CopilotKit에서 사용되는 모든 에이전트의 추상 베이스 클래스를 정의합니다.
에이전트는 상태 기반 대화를 관리하고, 복잡한 멀티턴 상호작용을 처리할 수 있는
AI 시스템입니다. LangGraph, CrewAI 등 다양한 프레임워크와 통합할 수 있습니다.

주요 개념
--------

**Agent (에이전트)**:
  - 상태 기반 대화를 관리하는 AI 시스템
  - 여러 턴에 걸친 복잡한 상호작용 처리
  - Thread ID로 대화 세션 관리
  - Action보다 복잡한 작업에 적합

**Thread (스레드)**:
  - 독립적인 대화 세션
  - 각 스레드는 고유한 ID를 가짐
  - 스레드별로 상태와 메시지 히스토리가 유지됨

**State (상태)**:
  - 에이전트의 현재 상태 (메시지, 데이터 등)
  - Thread별로 관리됨
  - LangGraph의 체크포인트 시스템과 통합

**Abstract Methods**:
  - execute(): 에이전트 실행 (필수 구현)
  - get_state(): 에이전트 상태 조회 (필수 구현)

Agent Hierarchy
----------------

```mermaid
graph TD
    subgraph "Abstract Base Class"
    ABC[Agent ABC]
    end

    subgraph "CopilotKit Implementations"
    LG[LangGraphAgent]
    LGAGUI[LangGraphAGUIAgent]
    end

    subgraph "External Integrations (Disabled)"
    CREW[CrewAIAgent]
    end

    subgraph "User Implementations"
    CUSTOM[Custom Agent]
    end

    ABC --> LG
    ABC --> LGAGUI
    ABC -.disabled.-> CREW
    ABC --> CUSTOM

    subgraph "Required Implementations"
    EXEC[execute method]
    GETSTATE[get_state method]
    end

    ABC -.requires.-> EXEC
    ABC -.requires.-> GETSTATE

    LG --> EXEC
    LG --> GETSTATE
    LGAGUI --> EXEC
    LGAGUI --> GETSTATE
    CUSTOM --> EXEC
    CUSTOM --> GETSTATE

    style ABC fill:#e1f5ff,stroke:#0066cc,stroke-width:3px
    style LG fill:#fff4e1,stroke:#ff9900,stroke-width:2px
    style LGAGUI fill:#ffe1e1,stroke:#cc0000,stroke-width:2px
    style CUSTOM fill:#e1ffe1,stroke:#00cc00,stroke-width:2px
    style CREW fill:#f0f0f0,stroke:#999999,stroke-width:1px,stroke-dasharray: 5 5
```

Implementation Guide
--------------------

### 1. 커스텀 에이전트 구현 예시

```python
from copilotkit import Agent
from typing import List, Optional
from copilotkit.types import Message, MetaEvent
from copilotkit.action import ActionDict

class MyCustomAgent(Agent):
    '''사용자 정의 에이전트'''

    def __init__(self, name: str, model, **kwargs):
        super().__init__(name=name, **kwargs)
        self.model = model

    def execute(
        self,
        *,
        state: dict,
        config: Optional[dict] = None,
        messages: List[Message],
        thread_id: str,
        actions: Optional[List[ActionDict]] = None,
        meta_events: Optional[List[MetaEvent]] = None,
        **kwargs
    ):
        '''에이전트를 실행하고 응답을 스트리밍합니다'''
        # 1. 상태 초기화
        current_state = state or {}

        # 2. 메시지 처리
        for msg in messages:
            # 메시지 처리 로직
            pass

        # 3. 에이전트 실행
        response = self.model.generate(messages)

        # 4. 응답 스트리밍 (Generator)
        yield {
            "type": "text",
            "content": response,
            "thread_id": thread_id
        }

    async def get_state(self, *, thread_id: str):
        '''에이전트 상태를 조회합니다'''
        # 데이터베이스나 체크포인트에서 상태 로드
        saved_state = self.load_state_from_db(thread_id)

        return {
            "threadId": thread_id,
            "threadExists": saved_state is not None,
            "state": saved_state or {},
            "messages": []
        }
```

### 2. LangGraph 에이전트 사용 (권장)

```python
from copilotkit import LangGraphAGUIAgent
from langgraph.graph import StateGraph, MessagesState
from langchain_core.messages import AIMessage

# LangGraph 그래프 정의
def agent_node(state: MessagesState):
    return {"messages": [AIMessage(content="Hello!")]}

graph = StateGraph(MessagesState)
graph.add_node("agent", agent_node)
graph.set_entry_point("agent")
graph.set_finish_point("agent")

# 에이전트 생성
agent = LangGraphAGUIAgent(
    name="my_agent",
    description="도움을 주는 AI 어시스턴트",
    graph=graph.compile()
)
```

### 3. SDK에 에이전트 등록

```python
from copilotkit import CopilotKitRemoteEndpoint

# 단일 에이전트
sdk = CopilotKitRemoteEndpoint(agents=[agent])

# 여러 에이전트
sdk = CopilotKitRemoteEndpoint(
    agents=[agent1, agent2, agent3]
)

# 동적 빌더
def build_agents(context):
    '''사용자 권한에 따라 에이전트 제공'''
    if context.user.is_premium:
        return [premium_agent]
    else:
        return [basic_agent]

sdk = CopilotKitRemoteEndpoint(agents=build_agents)
```

Agent vs Action
----------------

**언제 Agent를 사용할까?**

- 여러 턴에 걸친 대화가 필요한 경우
- 복잡한 상태 관리가 필요한 경우
- LangGraph/LangChain 워크플로우 사용
- 멀티스텝 추론이 필요한 경우

**언제 Action을 사용할까?**

- 단일 함수 호출로 끝나는 작업
- 상태 관리가 필요 없는 경우
- 빠른 응답이 필요한 경우
- 간단한 API 호출, 데이터 조회 등

| 특징 | Agent | Action |
|------|-------|--------|
| 상태 관리 | ✅ 있음 (Thread별) | ❌ 없음 (stateless) |
| 멀티턴 대화 | ✅ 지원 | ❌ 단일 호출 |
| 복잡도 | 높음 | 낮음 |
| 응답 시간 | 상대적으로 느림 | 빠름 |
| 사용 예시 | 대화형 AI, 복잡한 워크플로우 | 이메일 전송, 데이터 조회 |

Thread Management
-----------------

Thread는 독립적인 대화 세션을 나타냅니다:

```python
# 새 스레드 시작 (thread_id: "thread_123")
response = await sdk.execute_agent(
    agent_name="my_agent",
    messages=[{"role": "user", "content": "Hello"}],
    thread_id="thread_123"
)

# 같은 스레드 계속 (상태 유지됨)
response = await sdk.execute_agent(
    agent_name="my_agent",
    messages=[{"role": "user", "content": "What did I say?"}],
    thread_id="thread_123"  # 이전 대화 기억
)

# 다른 스레드 (독립적)
response = await sdk.execute_agent(
    agent_name="my_agent",
    messages=[{"role": "user", "content": "Hello"}],
    thread_id="thread_456"  # 완전히 새로운 세션
)

# 스레드 상태 조회
state = await sdk.get_agent_state(
    agent_name="my_agent",
    thread_id="thread_123"
)
print(state["messages"])  # 대화 히스토리
```

Best Practices
--------------

1. **에이전트 이름 규칙**:
   - Action과 동일: 영문자, 숫자, _, - 만 사용
   - 명확하고 설명적인 이름 사용

2. **상태 관리**:
   - Thread별로 상태를 독립적으로 관리
   - 영구 저장소(DB, Redis 등) 사용 권장
   - LangGraph의 체크포인트 활용

3. **execute() 구현**:
   - Generator 패턴으로 응답 스트리밍
   - 에러 처리를 명확하게
   - 타임아웃 설정

4. **get_state() 구현**:
   - threadExists 플래그를 정확하게 설정
   - 존재하지 않는 스레드도 처리
   - 메시지 히스토리 포함

5. **에러 핸들링**:
   - 에이전트 실행 중 에러는 AgentExecutionException으로 래핑됨
   - 명확한 에러 메시지 제공
   - 복구 가능한 에러는 재시도 로직 구현

Common Pitfalls
---------------

- ❌ **잘못된 에이전트 이름**: 공백, 특수문자 사용
  ```python
  Agent(name="my agent")  # ValueError 발생!
  ```

- ❌ **execute()를 일반 함수로 구현**:
  ```python
  def execute(self, ...):  # Generator여야 함!
      return result
  ```

- ❌ **thread_id 무시**:
  ```python
  def execute(self, ...):
      # thread_id를 무시하고 전역 상태 사용 (잘못됨!)
      global_state = {}
  ```

- ✅ **올바른 구현**:
  ```python
  Agent(name="my_agent")  # 언더스코어 사용

  def execute(self, *, thread_id, ...):  # Generator
      state = self.load_state(thread_id)  # Thread별 상태
      yield response
  ```

See Also
--------

- copilotkit.langgraph_agent.LangGraphAgent : LangGraph 통합 에이전트
- copilotkit.langgraph_agui_agent.LangGraphAGUIAgent : AG-UI 이벤트 지원 에이전트
- copilotkit.sdk.CopilotKitRemoteEndpoint : SDK 메인 클래스
- copilotkit.action.Action : 단순 함수 호출용 Action 클래스
- copilotkit.exc.AgentNotFoundException : 에이전트를 찾을 수 없는 경우
- copilotkit.exc.AgentExecutionException : 에이전트 실행 중 에러
"""

import re
from typing import Optional, List, TypedDict
from abc import ABC, abstractmethod
from .types import Message
from .action import ActionDict
from .types import MetaEvent

class AgentDict(TypedDict):
    """
    에이전트의 딕셔너리 표현

    Agent 인스턴스를 JSON 직렬화 가능한 딕셔너리로 변환한 형태입니다.
    주로 info() 엔드포인트에서 클라이언트에 사용 가능한 에이전트 목록을
    전달할 때 사용됩니다.

    Attributes
    ----------
    name : str
        에이전트 이름 (영문자, 숫자, _, - 만 허용)
    description : Optional[str]
        에이전트 설명 (AI가 이해할 수 있는 명확한 설명)

    Examples
    --------
    >>> agent = LangGraphAgent(name="assistant", graph=my_graph)
    >>> agent_dict = agent.dict_repr()
    >>> print(agent_dict)
    {
        "name": "assistant",
        "description": ""
    }
    """
    name: str
    description: Optional[str]

class Agent(ABC):
    """
    CopilotKit 에이전트 추상 베이스 클래스

    모든 CopilotKit 에이전트가 상속해야 하는 추상 베이스 클래스입니다.
    에이전트는 상태 기반 대화를 관리하고, 복잡한 멀티턴 상호작용을 처리합니다.

    Subclasses
    ----------
    - LangGraphAgent : LangGraph 그래프 통합 에이전트
    - LangGraphAGUIAgent : AG-UI 이벤트 지원 에이전트
    - 사용자 정의 에이전트 (Custom Agent)

    Attributes
    ----------
    name : str
        에이전트 이름 (영문자, 숫자, _, - 만 허용)
    description : Optional[str]
        에이전트 설명

    Abstract Methods
    ----------------
    execute : 에이전트를 실행하고 응답을 스트리밍 (Generator)
    get_state : 에이전트 상태를 조회 (async)

    Examples
    --------
    >>> from copilotkit import Agent
    >>> from typing import List
    >>> from copilotkit.types import Message
    >>>
    >>> class MyAgent(Agent):
    ...     def execute(self, *, state, messages, thread_id, **kwargs):
    ...         # 에이전트 로직 구현
    ...         yield {"type": "text", "content": "Hello!"}
    ...
    ...     async def get_state(self, *, thread_id):
    ...         return {
    ...             "threadId": thread_id,
    ...             "threadExists": True,
    ...             "state": {},
    ...             "messages": []
    ...         }

    See Also
    --------
    copilotkit.langgraph_agent.LangGraphAgent : LangGraph 통합
    copilotkit.langgraph_agui_agent.LangGraphAGUIAgent : AG-UI 이벤트 지원
    copilotkit.action.Action : 단순 함수 호출용 Action
    """
    def __init__(
            self,
            *,
            name: str,
            description: Optional[str] = None,
        ):
        """
        Agent 인스턴스를 생성합니다.

        Parameters
        ----------
        name : str
            에이전트 이름 (영문자, 숫자, _, - 만 허용)
            정규식 패턴: ^[a-zA-Z0-9_-]+$
        description : Optional[str], default=None
            에이전트 설명
            AI가 언제 이 에이전트를 사용해야 하는지 이해할 수 있도록 작성

        Raises
        ------
        ValueError
            name이 정규식 패턴에 맞지 않을 경우
            (공백, 특수문자 사용 불가)

        Examples
        --------
        >>> # 올바른 이름
        >>> agent = MyAgent(name="my_assistant", description="도움을 주는 AI")

        >>> # 잘못된 이름 (에러 발생)
        >>> try:
        ...     agent = MyAgent(name="my agent")  # 공백 포함!
        ... except ValueError as e:
        ...     print(e)
        Invalid agent name 'my agent': must consist of alphanumeric characters, underscores, and hyphens only
        """
        self.name = name
        self.description = description

        # 에이전트 이름 검증 (정규식 패턴)
        if not re.match(r"^[a-zA-Z0-9_-]+$", name):
            raise ValueError(
                f"Invalid agent name '{name}': " +
                "must consist of alphanumeric characters, underscores, and hyphens only"
            )

    @abstractmethod
    def execute( # pylint: disable=too-many-arguments
        self,
        *,
        state: dict,
        config: Optional[dict] = None,
        messages: List[Message],
        thread_id: str,
        actions: Optional[List[ActionDict]] = None,
        meta_events: Optional[List[MetaEvent]] = None,
        **kwargs,
    ):
        """
        에이전트를 실행하고 응답을 스트리밍합니다 (추상 메서드).

        이 메서드는 반드시 Generator로 구현되어야 하며,
        에이전트의 응답을 yield하여 클라이언트에 스트리밍합니다.

        Parameters
        ----------
        state : dict
            에이전트의 현재 상태
            Thread별로 유지되는 상태 정보
        config : Optional[dict], default=None
            에이전트 실행 설정
            LangGraph의 RunnableConfig 등
        messages : List[Message]
            대화 메시지 리스트
            사용자 입력 및 이전 AI 응답 포함
        thread_id : str
            스레드 ID (대화 세션 식별자)
            같은 thread_id는 상태를 공유함
        actions : Optional[List[ActionDict]], default=None
            사용 가능한 액션 목록
            에이전트가 호출할 수 있는 도구들
        meta_events : Optional[List[MetaEvent]], default=None
            메타 이벤트 목록
            인터럽트 응답 등
        **kwargs
            추가 인자

        Yields
        ------
        dict
            에이전트 응답 이벤트
            - type: 이벤트 타입 (text, tool_call, state 등)
            - content: 이벤트 내용
            - thread_id: 스레드 ID

        Raises
        ------
        AgentExecutionException
            에이전트 실행 중 발생한 에러는 SDK에서 래핑됨

        Examples
        --------
        >>> class MyAgent(Agent):
        ...     def execute(self, *, state, messages, thread_id, **kwargs):
        ...         # 1. 상태 로드
        ...         current_state = state or {}
        ...
        ...         # 2. 메시지 처리
        ...         last_message = messages[-1] if messages else None
        ...
        ...         # 3. 응답 생성 및 스트리밍
        ...         response = self.generate_response(last_message)
        ...         yield {
        ...             "type": "text",
        ...             "content": response,
        ...             "thread_id": thread_id
        ...         }
        ...
        ...         # 4. 상태 업데이트
        ...         current_state["last_response"] = response
        ...         yield {
        ...             "type": "state",
        ...             "state": current_state,
        ...             "thread_id": thread_id
        ...         }

        Notes
        -----
        - 반드시 Generator로 구현해야 합니다 (yield 사용)
        - thread_id를 사용하여 Thread별 상태를 관리하세요
        - 에러 발생 시 명확한 예외 메시지를 제공하세요
        """

    @abstractmethod
    async def get_state(
        self,
        *,
        thread_id: str,
    ):
        """
        에이전트 상태를 조회합니다 (추상 메서드).

        지정된 스레드의 현재 상태와 메시지 히스토리를 반환합니다.
        반드시 async 메서드로 구현되어야 합니다.

        Parameters
        ----------
        thread_id : str
            조회할 스레드 ID

        Returns
        -------
        dict
            에이전트 상태 딕셔너리
            - threadId (str): 스레드 ID
            - threadExists (bool): 스레드 존재 여부
            - state (dict): 에이전트 상태
            - messages (list): 메시지 히스토리

        Examples
        --------
        >>> class MyAgent(Agent):
        ...     async def get_state(self, *, thread_id):
        ...         # 데이터베이스에서 상태 로드
        ...         saved_state = await self.db.get_state(thread_id)
        ...         messages = await self.db.get_messages(thread_id)
        ...
        ...         return {
        ...             "threadId": thread_id,
        ...             "threadExists": saved_state is not None,
        ...             "state": saved_state or {},
        ...             "messages": messages or []
        ...         }

        >>> # 존재하지 않는 스레드 처리
        >>> class MyAgent(Agent):
        ...     async def get_state(self, *, thread_id):
        ...         return {
        ...             "threadId": thread_id,
        ...             "threadExists": False,  # 스레드 없음
        ...             "state": {},
        ...             "messages": []
        ...         }

        Notes
        -----
        - 반드시 async로 구현해야 합니다
        - threadExists를 정확하게 설정하세요
        - 존재하지 않는 스레드도 처리할 수 있어야 합니다
        - messages는 시간순으로 정렬되어야 합니다
        """
        return {
            "threadId": thread_id or "",
            "threadExists": False,
            "state": {},
            "messages": []
        }


    def dict_repr(self) -> AgentDict:
        """
        에이전트를 딕셔너리 형태로 직렬화합니다.

        에이전트의 스키마 정보(이름, 설명)를 JSON 직렬화 가능한
        딕셔너리로 변환합니다. 주로 info() 엔드포인트에서 클라이언트에게
        사용 가능한 에이전트 목록을 전달할 때 사용됩니다.

        Returns
        -------
        AgentDict
            에이전트 스키마를 담은 딕셔너리
            - name: 에이전트 이름
            - description: 에이전트 설명 (None이면 빈 문자열)

        Examples
        --------
        >>> agent = LangGraphAgent(
        ...     name="assistant",
        ...     description="도움을 주는 AI 어시스턴트",
        ...     graph=my_graph
        ... )
        >>> schema = agent.dict_repr()
        >>> print(schema)
        {
            "name": "assistant",
            "description": "도움을 주는 AI 어시스턴트"
        }

        >>> # description이 None인 경우
        >>> agent = LangGraphAgent(name="assistant", graph=my_graph)
        >>> schema = agent.dict_repr()
        >>> print(schema)
        {
            "name": "assistant",
            "description": ""
        }

        Notes
        -----
        - description이 None이면 빈 문자열로 변환됩니다
        - execute()와 get_state() 메서드는 포함되지 않습니다

        See Also
        --------
        AgentDict : 반환 타입 정의
        """
        return {
            'name': self.name,
            'description': self.description or ''  # None이면 빈 문자열
        }
