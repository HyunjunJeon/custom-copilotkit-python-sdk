"""
CopilotKit SDK - 핵심 진입점 및 요청 라우팅

이 모듈은 CopilotKit SDK의 핵심 진입점인 CopilotKitRemoteEndpoint 클래스를 제공합니다.
액션(Action)과 에이전트(Agent)를 등록하고, 클라이언트 요청을 적절한 핸들러로 라우팅하는
역할을 수행합니다.

주요 기능:
- 정적/동적 액션 및 에이전트 등록
- 컨텍스트 기반 액션/에이전트 필터링
- 액션 실행 및 에이전트 실행 관리
- 상태 조회 및 정보 제공

CopilotKitRemoteEndpoint는 다음과 같은 패턴을 지원합니다:
1. 정적 등록: 미리 정의된 액션/에이전트 리스트 제공
2. 동적 빌더: 요청 시 컨텍스트를 기반으로 액션/에이전트 생성
3. 조건부 필터링: 사용자 권한에 따라 다른 액션/에이전트 제공

SDK Architecture:
```mermaid
graph TB
    subgraph "Client Layer"
    C[CopilotKit Client]
    end

    subgraph "Integration Layer"
    F[FastAPI Endpoint]
    end

    subgraph "SDK Core - CopilotKitRemoteEndpoint"
    S[SDK Instance]
    AB[Actions Builder]
    GB[Agents Builder]
    end

    subgraph "Execution Layer"
    AH[Action Handlers]
    LG[LangGraph Agents]
    end

    subgraph "Context"
    CTX[CopilotKitContext]
    P[Properties]
    H[Headers]
    U[Frontend URL]
    end

    C -->|HTTP Request| F
    F -->|info| S
    F -->|execute_action| S
    F -->|execute_agent| S
    F -->|get_agent_state| S

    S -->|context| CTX
    CTX --> P
    CTX --> H
    CTX --> U

    S -->|build| AB
    S -->|build| GB

    AB -->|filter| AH
    GB -->|filter| LG

    S -->|invoke| AH
    S -->|stream| LG

    style S fill:#e1f5ff
    style CTX fill:#fff4e1
    style F fill:#f0f0f0
```

Dynamic Builder Pattern Flow:
```mermaid
sequenceDiagram
    participant C as Client
    participant F as FastAPI
    participant SDK as CopilotKitRemoteEndpoint
    participant B as Actions/Agents Builder
    participant H as Handler/Agent

    C->>F: POST /copilotkit/info
    F->>SDK: info(context)

    SDK->>SDK: Extract context (properties, headers, url)

    alt Actions is callable
        SDK->>B: actions(context)
        B->>B: Filter by permissions
        B->>B: Parameterize handlers
        B-->>SDK: List[Action]
    else Actions is list
        SDK->>SDK: Use static actions
    end

    alt Agents is callable
        SDK->>B: agents(context)
        B->>B: Filter by permissions
        B->>B: Configure LangGraph
        B-->>SDK: List[Agent]
    else Agents is list
        SDK->>SDK: Use static agents
    end

    SDK-->>F: InfoDict (actions, agents, version)
    F-->>C: JSON Response

    Note over C,H: Later: Execute Action or Agent

    C->>F: POST /copilotkit/execute_action
    F->>SDK: execute_action(name, args, context)
    SDK->>B: Build actions(context)
    SDK->>SDK: Find action by name
    SDK->>H: action.execute(args)
    H-->>SDK: ActionResultDict
    SDK-->>F: Result
    F-->>C: JSON Response
```

Key Classes:

1. **CopilotKitRemoteEndpoint**: 메인 SDK 클래스
   - 액션과 에이전트를 등록하고 관리
   - 요청에 따라 적절한 핸들러 호출
   - 컨텍스트 기반 동적 빌더 지원

2. **CopilotKitContext**: 요청 컨텍스트
   - properties: 프론트엔드에서 전달한 커스텀 데이터
   - frontend_url: 현재 프론트엔드 URL
   - headers: HTTP 헤더 정보

3. **InfoDict**: SDK 정보
   - actions: 사용 가능한 액션 목록
   - agents: 사용 가능한 에이전트 목록
   - sdkVersion: SDK 버전

Usage Examples:

    # 정적 액션 등록
    from copilotkit import CopilotKitRemoteEndpoint, Action

    sdk = CopilotKitRemoteEndpoint(
        actions=[
            Action(name="greet", handler=greet_handler, description="Say hello")
        ]
    )

    # 동적 액션 빌더
    def build_actions(context):
        user_role = context["properties"].get("role")
        actions = [basic_action]
        if user_role == "admin":
            actions.append(admin_action)
        return actions

    sdk = CopilotKitRemoteEndpoint(actions=build_actions)

    # 동적 에이전트 빌더
    def build_agents(context):
        token = context["properties"].get("token")
        return [
            LangGraphAGUIAgent(
                name="assistant",
                description="AI assistant",
                graph=graph,
                langgraph_config={"token": token}
            )
        ]

    sdk = CopilotKitRemoteEndpoint(agents=build_agents)

See Also
--------
- copilotkit.integrations.fastapi: FastAPI 통합
- copilotkit.action: Action 클래스
- copilotkit.langgraph_agui_agent: LangGraphAGUIAgent 클래스
"""

import warnings
from importlib import metadata

from pprint import pformat
from typing import List, Callable, Union, Optional, Any, Coroutine
from typing_extensions import TypedDict, Tuple, cast, Mapping
from .agent import Agent, AgentDict
from .action import Action, ActionDict, ActionResultDict
from .types import Message, MetaEvent
from .exc import (
    ActionNotFoundException,
    AgentNotFoundException,
    ActionExecutionException,
    AgentExecutionException
)
from .logging import get_logger, bold


try:
    __version__ = metadata.version(cast(str, __package__))
except metadata.PackageNotFoundError:
    # Case where package metadata is not available.
    __version__ = ""
del metadata  # optional, avoids polluting the results of dir(__package__)

COPILOTKIT_SDK_VERSION = __version__

logger = get_logger(__name__)

class InfoDict(TypedDict):
    """
    SDK 정보 딕셔너리

    /info 엔드포인트의 응답 형식입니다.
    클라이언트가 사용 가능한 액션과 에이전트 목록을 확인할 때 사용합니다.

    Attributes
    ----------
    sdkVersion : str
        CopilotKit Python SDK 버전 (예: "0.1.70")
    actions : List[ActionDict]
        사용 가능한 액션 목록 (각 액션의 메타데이터 포함)
    agents : List[AgentDict]
        사용 가능한 에이전트 목록 (각 에이전트의 메타데이터 포함)
    """
    sdkVersion: str
    actions: List[ActionDict]
    agents: List[AgentDict]

class CopilotKitContext(TypedDict):
    """
    CopilotKit 요청 컨텍스트

    모든 SDK 메서드에 전달되는 컨텍스트 정보입니다.
    프론트엔드로부터 전달받은 데이터와 HTTP 요청 정보를 포함합니다.

    이 컨텍스트는 동적 빌더 함수에 전달되어 사용자별 액션/에이전트를 생성하거나,
    핸들러에서 사용자 정보를 활용하는 데 사용됩니다.

    Attributes
    ----------
    properties : Any
        프론트엔드에서 전달한 커스텀 속성
        프론트엔드에서 <CopilotKit properties={{...}} />로 전달한 데이터
        예: 사용자 ID, 권한 토큰, 설정 값 등
    frontend_url : Optional[str]
        현재 프론트엔드의 URL (예: "https://app.example.com/dashboard")
        클라이언트가 어느 페이지에서 요청했는지 확인할 때 사용
    headers : Mapping[str, str]
        HTTP 요청 헤더 정보
        인증, CORS, 커스텀 헤더 등을 확인할 때 사용

    Examples
    --------
    >>> # 동적 빌더에서 컨텍스트 활용
    >>> def build_actions(context: CopilotKitContext):
    ...     user_id = context["properties"].get("userId")
    ...     is_admin = context["properties"].get("isAdmin", False)
    ...
    ...     actions = [basic_action]
    ...     if is_admin:
    ...         actions.append(admin_action)
    ...     return actions
    """
    properties: Any
    frontend_url: Optional[str]
    headers: Mapping[str, str]

# Alias for backwards compatibility
CopilotKitSDKContext = CopilotKitContext


class CopilotKitRemoteEndpoint:
    """
    CopilotKitRemoteEndpoint lets you connect actions and agents written in Python to your 
    CopilotKit application.

    To install CopilotKit for Python, run:

    ```bash
    pip install copilotkit
    # CUSTOMIZATION: CrewAI support disabled
    # # or to include crewai
    # pip install copilotkit[crewai]
    ```

    ## Adding actions

    In this example, we provide a simple action to the Copilot:

    ```python
    from copilotkit import CopilotKitRemoteEndpoint, Action

    sdk = CopilotKitRemoteEndpoint(
        actions=[
            Action(
                name="greet_user",
                handler=greet_user_handler,
                description="Greet the user",
                parameters=[
                    {
                        "name": "name",
                        "type": "string",
                        "description": "The name of the user"
                    }
                ]
            )
        ]
    )
    ```

    You can also dynamically build actions by providing a callable that returns a list of actions.
    In this example, we use "name" from the `properties` object to parameterize the action handler.

    ```python
    from copilotkit import CopilotKitRemoteEndpoint, Action

    sdk = CopilotKitRemoteEndpoint(
        actions=lambda context: [
            Action(
                name="greet_user",
                handler=make_greet_user_handler(context["properties"]["name"]), 
                description="Greet the user"
            )
        ]
    )
    ```

    Using the same approach, you can restrict the actions available to the Copilot:

    ```python
    from copilotkit import CopilotKitRemoteEndpoint, Action

    sdk = CopilotKitRemoteEndpoint(
        actions=lambda context: (
            [action_a, action_b] if is_admin(context["properties"]["token"]) else [action_a]
        )
    )
    ```

    ## Adding agents

    Serving agents works in a similar way to serving actions:

    ```python
    from copilotkit import CopilotKitRemoteEndpoint, LangGraphAgent
    from my_agent.agent import graph

    sdk = CopilotKitRemoteEndpoint(
        agents=[
            LangGraphAgent(
                name="email_agent",
                description="This agent sends emails",
                graph=graph,
            )
        ]
    )
    ```

    To dynamically build agents, provide a callable that returns a list of agents:

    ```python
    from copilotkit import CopilotKitRemoteEndpoint, LangGraphAgent
    from my_agent.agent import graph

    sdk = CopilotKitRemoteEndpoint(
        agents=lambda context: [
            LangGraphAgent(
                name="email_agent",
                description="This agent sends emails",
                graph=graph,
                langgraph_config={
                    "token": context["properties"]["token"]
                }
            )
        ]
    )
    ```

    To restrict the agents available to the Copilot, simply return a different list of agents based on the `context`:

    ```python
    from copilotkit import CopilotKitRemoteEndpoint
    from my_agents import agent_a, agent_b, is_admin

    sdk = CopilotKitRemoteEndpoint(
        agents=lambda context: (
            [agent_a, agent_b] if is_admin(context["properties"]["token"]) else [agent_a]
        )
    )
    ```

    ## Serving the CopilotKit SDK

    To serve the CopilotKit SDK, you can use the `add_fastapi_endpoint` function from the `copilotkit.integrations.fastapi` module:

    ```python
    from copilotkit.integrations.fastapi import add_fastapi_endpoint
    from fastapi import FastAPI

    app = FastAPI()
    sdk = CopilotKitRemoteEndpoint(...)
    add_fastapi_endpoint(app, sdk, "/copilotkit")

    def main():
        uvicorn.run(
            "your_package:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
        )

    ```

    Parameters
    ----------
    actions : Optional[Union[List[Action], Callable[[CopilotKitContext], List[Action]]]]
        The actions to make available to the Copilot.
    agents : Optional[Union[List[Agent], Callable[[CopilotKitContext], List[Agent]]]]
        The agents to make available to the Copilot.
    """

    def __init__(
        self,
        *,
        actions: Optional[
            Union[
                List[Action],
                Callable[[CopilotKitContext], List[Action]]
            ]
        ] = None,
        agents: Optional[
            Union[
                List[Agent],
                Callable[[CopilotKitContext], List[Agent]]
            ]
        ] = None,
    ):
        self.agents = agents or []
        self.actions = actions or []

        if isinstance(agents, list):
            from .langgraph_agent import LangGraphAgent
            for agent in agents:
                if isinstance(agent, LangGraphAgent):
                    raise ValueError(
                        "LangGraphAgent should be instantiated using LangGraphAGUIAgent. Refer to https://docs.copilotkit.ai/langgraph for more information.")
        

    def info(
        self,
        *,
        context: CopilotKitContext
    ) -> InfoDict:
        """
        사용 가능한 액션 및 에이전트 정보 반환

        클라이언트가 SDK에 등록된 액션과 에이전트 목록을 조회할 때 호출됩니다.
        동적 빌더가 등록된 경우, 현재 컨텍스트를 기반으로 액션/에이전트를 빌드합니다.

        호출 시점:
        - 클라이언트 초기화 시 (CopilotKit 컴포넌트 마운트)
        - 페이지 전환 시 (컨텍스트 변경)
        - 명시적 갱신 요청 시

        동작 흐름:
        1. actions가 callable이면 context를 전달하여 호출, 아니면 정적 리스트 사용
        2. agents가 callable이면 context를 전달하여 호출, 아니면 정적 리스트 사용
        3. 각 액션/에이전트의 dict_repr()을 호출하여 메타데이터 추출
        4. SDK 버전과 함께 InfoDict로 반환
        5. 요청 정보를 로그에 기록

        Parameters
        ----------
        context : CopilotKitContext
            요청 컨텍스트 (properties, frontend_url, headers)

        Returns
        -------
        InfoDict
            SDK 정보 딕셔너리:
            - actions: 액션 메타데이터 리스트
            - agents: 에이전트 메타데이터 리스트
            - sdkVersion: SDK 버전 문자열

        Examples
        --------
        >>> # 정적 액션/에이전트
        >>> sdk = CopilotKitRemoteEndpoint(
        ...     actions=[action1, action2],
        ...     agents=[agent1]
        ... )
        >>> info = sdk.info(context={"properties": {}, "frontend_url": None, "headers": {}})
        >>> len(info["actions"])  # 2
        >>> len(info["agents"])  # 1
        >>>
        >>> # 동적 빌더
        >>> def build_actions(context):
        ...     if context["properties"].get("isAdmin"):
        ...         return [action1, action2, admin_action]
        ...     return [action1, action2]
        >>>
        >>> sdk = CopilotKitRemoteEndpoint(actions=build_actions)
        >>> admin_info = sdk.info(context={"properties": {"isAdmin": True}, ...})
        >>> len(admin_info["actions"])  # 3
        >>> user_info = sdk.info(context={"properties": {"isAdmin": False}, ...})
        >>> len(user_info["actions"])  # 2

        Notes
        -----
        - 동적 빌더는 매 요청마다 호출되므로 성능에 주의해야 합니다
        - dict_repr()은 각 액션/에이전트의 name, description, parameters 등을 포함합니다
        - 로그는 INFO 레벨로 출력되며 디버깅에 유용합니다
        """

        actions = self.actions(context) if callable(self.actions) else self.actions
        agents = self.agents(context) if callable(self.agents) else self.agents

        actions_list = [action.dict_repr() for action in actions]
        agents_list = [agent.dict_repr() for agent in agents]

        self._log_request_info(
            title="Handling info request:",
            data=[
                ("Context", context),
                ("Actions", actions_list),
                ("Agents", agents_list),
            ]
        )

        return {
            "actions": actions_list,
            "agents": agents_list,
            "sdkVersion": COPILOTKIT_SDK_VERSION
        }

    def _get_action(
        self,
        *,
        context: CopilotKitContext,
        name: str,
    ) -> Action:
        """
        이름으로 액션 조회 (내부 헬퍼 메서드)

        현재 컨텍스트에서 사용 가능한 액션 목록을 빌드하고,
        지정된 이름의 액션을 찾아 반환합니다.

        동작:
        1. actions가 callable이면 context로 빌드, 아니면 정적 리스트 사용
        2. name과 일치하는 액션 검색
        3. 찾으면 Action 객체 반환, 없으면 ActionNotFoundException 발생

        Parameters
        ----------
        context : CopilotKitContext
            요청 컨텍스트
        name : str
            찾을 액션의 이름

        Returns
        -------
        Action
            이름이 일치하는 Action 객체

        Raises
        ------
        ActionNotFoundException
            지정된 이름의 액션을 찾을 수 없는 경우

        Notes
        -----
        - 이 메서드는 내부 헬퍼로, execute_action에서 호출됩니다
        - 동적 빌더를 사용하는 경우 매 호출마다 액션 리스트를 재빌드합니다
        """
        actions = self.actions(context) if callable(self.actions) else self.actions
        action = next((action for action in actions if action.name == name), None)
        if action is None:
            raise ActionNotFoundException(name)
        return action

    def execute_action(
            self,
            *,
            context: CopilotKitContext,
            name: str,
            arguments: dict,
    ) -> Coroutine[Any, Any, ActionResultDict]:
        """
        액션 실행

        클라이언트가 특정 액션을 호출할 때 사용됩니다.
        액션을 찾아서 제공된 인자로 핸들러를 실행하고 결과를 반환합니다.

        실행 흐름:
        1. _get_action()으로 현재 컨텍스트에서 액션 조회
        2. 요청 정보를 로그에 기록 (액션 메타데이터, 인자)
        3. action.execute(arguments) 호출
        4. 성공 시 ActionResultDict 반환
        5. 실패 시 ActionExecutionException 발생

        Parameters
        ----------
        context : CopilotKitContext
            요청 컨텍스트 (properties, frontend_url, headers)
        name : str
            실행할 액션의 이름
        arguments : dict
            액션 핸들러에 전달할 인자들
            액션의 parameters 정의와 일치해야 함

        Returns
        -------
        Coroutine[Any, Any, ActionResultDict]
            액션 실행 결과를 담은 코루틴
            ActionResultDict는 result 필드에 반환값을 포함

        Raises
        ------
        ActionNotFoundException
            지정된 이름의 액션을 찾을 수 없는 경우
        ActionExecutionException
            액션 실행 중 에러가 발생한 경우 (원본 예외를 포함)

        Examples
        --------
        >>> # 액션 정의
        >>> async def send_email(to: str, subject: str, body: str):
        ...     # 이메일 전송 로직
        ...     return {"status": "sent", "message_id": "123"}
        >>>
        >>> action = Action(
        ...     name="send_email",
        ...     handler=send_email,
        ...     description="Send an email"
        ... )
        >>>
        >>> sdk = CopilotKitRemoteEndpoint(actions=[action])
        >>>
        >>> # 액션 실행
        >>> context = {"properties": {"userId": "user123"}, ...}
        >>> result_coro = sdk.execute_action(
        ...     context=context,
        ...     name="send_email",
        ...     arguments={
        ...         "to": "user@example.com",
        ...         "subject": "Hello",
        ...         "body": "Test email"
        ...     }
        ... )
        >>> result = await result_coro
        >>> result["result"]  # {"status": "sent", "message_id": "123"}

        Notes
        -----
        - 이 메서드는 코루틴을 반환하므로 await으로 호출해야 합니다
        - 액션 핸들러는 동기/비동기 모두 가능합니다
        - 로그는 INFO 레벨로 출력되며 요청 추적에 유용합니다
        - 에러 발생 시 원본 예외는 ActionExecutionException.__cause__에 저장됩니다
        """

        action = self._get_action(context=context, name=name)

        self._log_request_info(
            title="Handling execute action request:",
            data=[
                ("Context", context),
                ("Action", action.dict_repr()),
                ("Arguments", arguments),
            ]
        )

        try:
            result = action.execute(arguments=arguments)
            return result
        except Exception as error:
            raise ActionExecutionException(name, error) from error

    def execute_agent( # pylint: disable=too-many-arguments
        self,
        *,
        context: CopilotKitContext,
        name: str,
        thread_id: str,
        state: dict,
        config: Optional[dict] = None,
        messages: List[Message],
        actions: List[ActionDict],
        node_name: str,
        meta_events: Optional[List[MetaEvent]] = None,
    ) -> Any:
        """
        에이전트 실행

        클라이언트가 LangGraph 에이전트를 실행하거나 재개할 때 호출됩니다.
        에이전트를 찾아서 제공된 상태와 메시지로 LangGraph를 실행하고 결과를 스트리밍합니다.

        실행 흐름:
        1. 현재 컨텍스트에서 에이전트 조회 (이름으로 검색)
        2. 요청 정보를 로그에 기록 (thread_id, state, messages 등)
        3. agent.execute() 호출 (LangGraph 실행)
        4. 스트리밍 이벤트 반환 (on_agent_action, on_agent_message 등)
        5. 에러 발생 시 AgentExecutionException 발생

        Parameters
        ----------
        context : CopilotKitContext
            요청 컨텍스트 (properties, frontend_url, headers)
        name : str
            실행할 에이전트의 이름
        thread_id : str
            대화 스레드 ID (상태 저장/복원에 사용)
        state : dict
            에이전트 상태 (기존 상태 또는 초기 상태)
        config : Optional[dict], optional
            LangGraph 실행 설정 (커스텀 설정 추가 가능)
        messages : List[Message]
            대화 메시지 목록 (CopilotKit 형식)
        actions : List[ActionDict]
            사용 가능한 액션 메타데이터 리스트
        node_name : str
            실행할 노드 이름 (빈 문자열이면 처음부터 시작)
        meta_events : Optional[List[MetaEvent]], optional
            메타 이벤트 (interrupt 재개 시 사용자 응답 등)

        Returns
        -------
        Any
            에이전트 실행 결과 (일반적으로 AsyncGenerator for SSE streaming)

        Raises
        ------
        AgentNotFoundException
            지정된 이름의 에이전트를 찾을 수 없는 경우
        AgentExecutionException
            에이전트 실행 중 에러가 발생한 경우 (원본 예외를 포함)

        Examples
        --------
        >>> # 에이전트 정의
        >>> from copilotkit import LangGraphAGUIAgent
        >>> from langgraph.graph import StateGraph
        >>>
        >>> graph = StateGraph(...)  # LangGraph 정의
        >>> agent = LangGraphAGUIAgent(
        ...     name="email_agent",
        ...     description="Email management agent",
        ...     graph=graph
        ... )
        >>>
        >>> sdk = CopilotKitRemoteEndpoint(agents=[agent])
        >>>
        >>> # 에이전트 실행 (새 대화)
        >>> result = sdk.execute_agent(
        ...     context=context,
        ...     name="email_agent",
        ...     thread_id="thread_123",
        ...     state={},
        ...     messages=[{"role": "user", "content": "Send email to John"}],
        ...     actions=[],
        ...     node_name=""
        ... )
        >>>
        >>> # 에이전트 재개 (interrupt 이후)
        >>> result = sdk.execute_agent(
        ...     context=context,
        ...     name="email_agent",
        ...     thread_id="thread_123",
        ...     state=existing_state,
        ...     messages=existing_messages,
        ...     actions=[],
        ...     node_name="approval_node",
        ...     meta_events=[{"type": "interrupt_response", "data": "yes"}]
        ... )

        Notes
        -----
        - thread_id는 대화 연속성을 위해 중요합니다 (상태 체크포인트 키)
        - node_name이 빈 문자열이면 그래프의 시작 노드부터 실행
        - meta_events는 interrupt 재개 시 사용자 응답을 전달합니다
        - 반환값은 일반적으로 SSE (Server-Sent Events) 스트리밍 생성기입니다
        - 로그는 모든 파라미터를 포함하여 출력되므로 디버깅에 유용합니다
        """
        agents = self.agents(context) if callable(self.agents) else self.agents
        agent = next((agent for agent in agents if agent.name == name), None)
        if agent is None:
            raise AgentNotFoundException(name)

        self._log_request_info(
            title="Handling execute agent request:",
            data=[
                ("Context", context),
                ("Agent", agent.dict_repr()),
                ("Thread ID", thread_id),
                ("Node Name", node_name),
                ("State", state),
                ("Config", config),
                ("Messages", messages),
                ("Actions", actions),
                ("MetaEvents", meta_events),
            ]
        )

        try:
            return agent.execute(
                thread_id=thread_id,
                node_name=node_name,
                state=state,
                config=config,
                messages=messages,
                actions=actions,
                meta_events=meta_events
            )
        except Exception as error:
            raise AgentExecutionException(name, error) from error

    async def get_agent_state(
        self,
        *,
        context: CopilotKitContext,
        thread_id: str,
        name: str,
    ):
        """
        에이전트 상태 조회

        특정 스레드의 에이전트 상태를 조회합니다.
        LangGraph의 체크포인트에 저장된 상태를 반환하며, 대화 이력 복원이나
        상태 확인에 사용됩니다.

        실행 흐름:
        1. 현재 컨텍스트에서 에이전트 조회 (이름으로 검색)
        2. 요청 정보를 로그에 기록 (thread_id)
        3. agent.get_state(thread_id) 호출
        4. 체크포인트에서 상태 조회 및 반환
        5. 에러 발생 시 AgentExecutionException 발생

        사용 시나리오:
        - 대화 재개 시 이전 상태 확인
        - 현재 에이전트가 어느 노드에 있는지 확인
        - 인터럽트 상태 확인 (대기 중인 사용자 입력)
        - 디버깅 및 모니터링

        Parameters
        ----------
        context : CopilotKitContext
            요청 컨텍스트 (properties, frontend_url, headers)
        thread_id : str
            조회할 스레드 ID (대화 식별자)
        name : str
            에이전트 이름

        Returns
        -------
        StateSnapshot
            LangGraph 상태 스냅샷:
            - values: 현재 상태 값 (messages, copilotkit 등)
            - next: 다음 실행할 노드 이름들
            - config: 실행 설정
            - metadata: 메타데이터
            - tasks: 대기 중인 태스크 (인터럽트 포함)

        Raises
        ------
        AgentNotFoundException
            지정된 이름의 에이전트를 찾을 수 없는 경우
        AgentExecutionException
            상태 조회 중 에러가 발생한 경우 (원본 예외를 포함)

        Examples
        --------
        >>> # 에이전트 상태 조회
        >>> sdk = CopilotKitRemoteEndpoint(agents=[agent])
        >>>
        >>> state = await sdk.get_agent_state(
        ...     context=context,
        ...     name="email_agent",
        ...     thread_id="thread_123"
        ... )
        >>>
        >>> # 상태 정보 확인
        >>> state["values"]["messages"]  # 대화 메시지 목록
        >>> state["next"]  # 다음 실행할 노드 (["send_node"] 등)
        >>>
        >>> # 인터럽트 상태 확인
        >>> if state.get("tasks"):
        ...     # 인터럽트 대기 중
        ...     interrupt_value = state["tasks"][0]["interrupts"][0]["value"]
        ...     print(f"User input required: {interrupt_value}")

        Notes
        -----
        - 이 메서드는 async이므로 await으로 호출해야 합니다
        - thread_id가 존재하지 않으면 빈 상태를 반환할 수 있습니다
        - 상태는 LangGraph의 checkpointer에 저장되므로 설정에 따라 달라집니다
        - 인터럽트 대기 중인 경우 tasks 필드에 인터럽트 정보가 포함됩니다
        """
        agents = self.agents(context) if callable(self.agents) else self.agents
        agent = next((agent for agent in agents if agent.name == name), None)
        if agent is None:
            raise AgentNotFoundException(name)

        self._log_request_info(
            title="Handling get agent state request:",
            data=[
                ("Context", context),
                ("Agent", agent.dict_repr()),
                ("Thread ID", thread_id),
            ]
        )
        try:
            return await agent.get_state(thread_id=thread_id)
        except Exception as error:
            raise AgentExecutionException(name, error) from error

    def _log_request_info(self, title: str, data: List[Tuple[str, Any]]):
        """
        Log request info
        """
        logger.info(bold(title))
        logger.info("--------------------------")
        for key, value in data:
            logger.info(bold(key+":"))
            logger.info(pformat(value))
        logger.info("--------------------------")

# Alias for backwards compatibility
class CopilotKitSDK(CopilotKitRemoteEndpoint):
    """Deprecated: Use CopilotKitRemoteEndpoint instead. This class will be removed in a future version."""

    def __init__(self, *args, **kwargs):
        warnings.warn(
            "CopilotKitSDK is deprecated since version 0.1.31. "
            "Use CopilotKitRemoteEndpoint instead.",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*args, **kwargs)
