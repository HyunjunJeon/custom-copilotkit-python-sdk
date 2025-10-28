"""
FastAPI Integration for CopilotKit

이 모듈은 CopilotKit SDK를 FastAPI 애플리케이션과 통합하기 위한 엔드포인트를 제공합니다.
클라이언트로부터 받은 HTTP 요청을 CopilotKit SDK의 내부 로직으로 라우팅하고,
그 결과를 적절한 HTTP 응답으로 변환하여 반환합니다.

주요 기능:
- Action 실행: 클라이언트가 정의한 액션을 실행
- Agent 실행: LangGraph 기반 에이전트를 스트리밍 방식으로 실행
- Agent 상태 조회: 특정 스레드의 에이전트 상태를 가져옴
- 정보 조회: 사용 가능한 액션 및 에이전트 목록을 HTML 또는 JSON으로 반환

Request Flow Diagram:
```mermaid
graph TD
    A[Client Request] --> B[add_fastapi_endpoint]
    B --> C{Thread Pool?}
    C -->|Yes| D[ThreadPoolExecutor]
    C -->|No| E[Async Handler]
    D --> F[handler]
    E --> F
    F --> G{Parse Request}
    G --> H{Route by Path}
    H -->|/| I[handle_info]
    H -->|/agent/:name| J[handle_execute_agent]
    H -->|/agent/:name/state| K[handle_get_agent_state]
    H -->|/action/:name| L[handle_execute_action]
    H -->|Legacy| M[handler_v1]
    I --> N[Response]
    J --> N
    K --> N
    L --> N
    M --> N
    N --> O[Client]
```

Version Support:
- V2 (현재): REST 스타일 경로 (예: /agent/my_agent, /action/my_action)
- V1 (레거시): POST 기반 경로 (예: /agents/execute, /actions/execute)
"""

import logging
import asyncio
import re
import uuid
import warnings
from concurrent.futures import ThreadPoolExecutor
from typing import List, Any, cast, Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse, HTMLResponse
from fastapi.encoders import jsonable_encoder
from ..sdk import CopilotKitRemoteEndpoint, CopilotKitContext
from ..types import Message, MetaEvent
from ..exc import (
    ActionNotFoundException,
    ActionExecutionException,
    AgentNotFoundException,
    AgentExecutionException,
)
from ..action import ActionDict
from ..html import generate_info_html

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


def add_fastapi_endpoint(
        fastapi_app: FastAPI,
        sdk: CopilotKitRemoteEndpoint,
        prefix: str,
        *,
        use_thread_pool: bool = False,
        max_workers: int = 10,
    ):
    """
    FastAPI 애플리케이션에 CopilotKit 엔드포인트를 추가합니다.

    이 함수는 지정된 prefix 경로 아래에 CopilotKit SDK를 위한 모든 라우트를 등록합니다.
    모든 HTTP 메서드(GET, POST, PUT, DELETE, OPTIONS)를 지원하며,
    와일드카드 경로 매칭을 통해 다양한 하위 경로를 처리합니다.

    Parameters
    ----------
    fastapi_app : FastAPI
        CopilotKit 엔드포인트를 추가할 FastAPI 애플리케이션 인스턴스
    sdk : CopilotKitRemoteEndpoint
        요청을 처리할 CopilotKit SDK 인스턴스
    prefix : str
        엔드포인트의 기본 경로 (예: "/copilotkit")
        자동으로 앞뒤 슬래시가 정규화됩니다.
    use_thread_pool : bool, optional
        (DEPRECATED) ThreadPoolExecutor 사용 여부
        비동기 처리가 기본이므로 더 이상 권장되지 않습니다.
    max_workers : int, optional
        ThreadPoolExecutor의 최대 워커 수 (use_thread_pool=True일 때만 사용)

    Examples
    --------
    >>> from fastapi import FastAPI
    >>> from copilotkit import CopilotKitRemoteEndpoint
    >>> from copilotkit.integrations.fastapi import add_fastapi_endpoint
    >>>
    >>> app = FastAPI()
    >>> sdk = CopilotKitRemoteEndpoint(actions=[...], agents=[...])
    >>> add_fastapi_endpoint(app, sdk, "/copilotkit")

    Notes
    -----
    등록되는 경로 패턴:
    - GET/POST {prefix}/ : 정보 조회 (HTML 또는 JSON)
    - POST {prefix}/agent/:name : 에이전트 실행
    - POST {prefix}/agent/:name/state : 에이전트 상태 조회
    - POST {prefix}/action/:name : 액션 실행
    - 레거시 V1 경로도 하위 호환성을 위해 지원
    """
    if use_thread_pool:
        warnings.warn(
            "The 'use_thread_pool' parameter is deprecated " +
            "and will be removed in a future version.",
            DeprecationWarning
        )

    def run_handler_in_thread(request: Request, sdk: CopilotKitRemoteEndpoint):
        """
        스레드 풀에서 핸들러를 실행합니다. (DEPRECATED)

        새로운 이벤트 루프를 생성하여 비동기 handler 함수를 동기적으로 실행합니다.
        이 방식은 더 이상 권장되지 않으며, 직접 비동기 방식을 사용하는 것이 좋습니다.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(handler(request, sdk))

    async def make_handler(request: Request):
        """
        요청을 핸들러로 라우팅합니다.

        use_thread_pool 설정에 따라 ThreadPoolExecutor를 사용하거나
        직접 비동기 handler를 호출합니다.
        """
        if use_thread_pool:
            executor = ThreadPoolExecutor(max_workers=max_workers)
            loop = asyncio.get_event_loop()
            future = loop.run_in_executor(executor, run_handler_in_thread, request, sdk)
            return await future
        return await handler(request, sdk)

    # prefix 정규화: 시작에는 /를 추가하고, 끝의 /는 제거
    normalized_prefix = '/' + prefix.strip('/')

    # 모든 하위 경로를 처리하는 와일드카드 라우트 등록
    fastapi_app.add_api_route(
        f"{normalized_prefix}/{{path:path}}",
        make_handler,
        methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    )


def body_get_or_raise(body: Any, key: str):
    """
    요청 body에서 필수 필드를 가져옵니다.

    지정된 키가 body에 없거나 None인 경우 HTTP 400 에러를 발생시킵니다.

    Parameters
    ----------
    body : Any
        파싱된 JSON 요청 body
    key : str
        가져올 필드의 키

    Returns
    -------
    Any
        해당 키의 값

    Raises
    ------
    HTTPException
        키가 없거나 값이 None인 경우 400 에러
    """
    value = body.get(key)
    if value is None:
        raise HTTPException(status_code=400, detail=f"{key} is required")
    return value


async def handler(request: Request, sdk: CopilotKitRemoteEndpoint):
    """
    메인 요청 핸들러 - 모든 CopilotKit 요청을 처리합니다.

    이 함수는 FastAPI의 모든 요청을 받아서 경로와 메서드에 따라
    적절한 하위 핸들러로 라우팅합니다.

    Request Processing Flow:
    ```mermaid
    graph TD
        A[Request 수신] --> B[JSON Body 파싱]
        B --> C[CopilotKitContext 생성]
        C --> D{경로 분석}
        D -->|/ GET/POST| E[정보 조회]
        D -->|/agent/:name POST| F[에이전트 실행]
        D -->|/agent/:name/state POST| G[에이전트 상태]
        D -->|/action/:name POST| H[액션 실행]
        D -->|기타| I[V1 핸들러]
        E --> J[응답 반환]
        F --> J
        G --> J
        H --> J
        I --> J
        I -->|매칭 없음| K[404 에러]
    ```

    Parameters
    ----------
    request : Request
        FastAPI Request 객체
    sdk : CopilotKitRemoteEndpoint
        CopilotKit SDK 인스턴스

    Returns
    -------
    Response
        JSONResponse, StreamingResponse, HTMLResponse 중 하나

    Raises
    ------
    HTTPException
        매칭되는 경로가 없는 경우 404 에러

    Notes
    -----
    Context 구성:
    - properties: 클라이언트가 전달한 추가 속성
    - frontend_url: 프론트엔드 URL (CORS 등에 사용)
    - headers: HTTP 헤더 정보
    """
    # JSON body 파싱 (파싱 실패 시 None)
    try:
        body = await request.json()
    except: # pylint: disable=bare-except
        body = None

    path = request.path_params.get('path')
    method = request.method

    # CopilotKit 컨텍스트 생성
    # SDK 내부에서 사용되는 메타데이터를 포함
    context = cast(
        CopilotKitContext,
        {
            "properties": (body or {}).get("properties", {}),
            "frontend_url": (body or {}).get("frontendUrl", None),
            "headers": request.headers,
        }
    )

    # V2 API: 루트 경로 - 정보 조회 엔드포인트
    # Accept 헤더에 따라 HTML 또는 JSON 반환
    if method in ['GET', 'POST'] and path == '':
        accept_header = request.headers.get('accept', '')
        return await handle_info(
            sdk=sdk,
            context=context,
            as_html='text/html' in accept_header,
        )

    # V2 API: 에이전트 실행
    # POST /agent/{name} - 특정 에이전트를 스트리밍 방식으로 실행
    if method == 'POST' and (match := re.match(r'agent/([a-zA-Z0-9_-]+)', path)):
        name = match.group(1)
        body = body or {}

        thread_id = body.get("threadId", str(uuid.uuid4()))
        state = body.get("state", {})
        messages = body.get("messages", [])
        actions = body.get("actions", [])
        node_name = body.get("nodeName")  # LangGraph 전용: 재개할 노드 이름

        return handle_execute_agent(
            sdk=sdk,
            context=context,
            thread_id=thread_id,
            node_name=node_name,
            name=name,
            state=state,
            messages=messages,
            actions=actions,
        )

    # V2 API: 에이전트 상태 조회
    # POST /agent/{name}/state - 특정 스레드의 에이전트 상태 가져오기
    if method == 'POST' and (match := re.match(r'agent/([a-zA-Z0-9_-]+)/state', path)):
        name = match.group(1)
        thread_id = body_get_or_raise(body, "threadId")

        return await handle_get_agent_state(
            sdk=sdk,
            context=context,
            thread_id=thread_id,
            name=name,
        )

    # V2 API: 액션 실행
    # POST /action/{name} - 특정 액션을 실행
    if method == 'POST' and (match := re.match(r'action/([a-zA-Z0-9_-]+)', path)):
        name = match.group(1)
        arguments = body.get("arguments", {})

        return await handle_execute_action(
            sdk=sdk,
            context=context,
            name=name,
            arguments=arguments,
        )

    # 하위 호환성: V1 API 핸들러로 폴백
    result_v1 = await handler_v1(
        sdk=sdk,
        method=method,
        path=path,
        body=body,
        context=context,
    )

    if result_v1 is not None:
        return result_v1

    # 매칭되는 경로가 없는 경우
    raise HTTPException(status_code=404, detail="Not found")


async def handler_v1(
        sdk: CopilotKitRemoteEndpoint,
        method: str,
        path: str,
        body: Any,
        context: CopilotKitContext,
    ):
    """
    V1 API 핸들러 - 레거시 경로 지원

    이전 버전의 CopilotKit 클라이언트와의 하위 호환성을 위해 유지됩니다.
    V1 API는 POST 메서드와 동사 기반 경로를 사용합니다.

    V1 vs V2 API 비교:
    - V1: POST /agents/execute
    - V2: POST /agent/:name

    Parameters
    ----------
    sdk : CopilotKitRemoteEndpoint
        CopilotKit SDK 인스턴스
    method : str
        HTTP 메서드
    path : str
        요청 경로
    body : Any
        파싱된 JSON body
    context : CopilotKitContext
        CopilotKit 컨텍스트

    Returns
    -------
    Response or None
        매칭되는 경로가 있으면 응답, 없으면 None

    Notes
    -----
    지원하는 V1 경로:
    - POST /info: 정보 조회
    - POST /actions/execute: 액션 실행
    - POST /agents/execute: 에이전트 실행
    - POST /agents/state: 에이전트 상태 조회
    """
    if body is None:
        raise HTTPException(status_code=400, detail="Request body is required")

    # V1: 정보 조회
    if method == 'POST' and path == 'info':
        return await handle_info(sdk=sdk, context=context)

    # V1: 액션 실행
    if method == 'POST' and path == 'actions/execute':
        name = body_get_or_raise(body, "name")
        arguments = body.get("arguments", {})

        return await handle_execute_action(
            sdk=sdk,
            context=context,
            name=name,
            arguments=arguments,
        )

    # V1: 에이전트 실행
    if method == 'POST' and path == 'agents/execute':
        thread_id = body.get("threadId")
        node_name = body.get("nodeName")
        config = body.get("config")

        name = body_get_or_raise(body, "name")
        state = body_get_or_raise(body, "state")
        messages = body_get_or_raise(body, "messages")
        actions = cast(List[ActionDict], body.get("actions", []))
        meta_events = cast(List[MetaEvent], body.get("metaEvents", []))

        return handle_execute_agent(
            sdk=sdk,
            context=context,
            thread_id=thread_id,
            node_name=node_name,
            name=name,
            state=state,
            config=config,
            messages=messages,
            actions=actions,
            meta_events=meta_events,
        )

    # V1: 에이전트 상태 조회
    if method == 'POST' and path == 'agents/state':
        thread_id = body_get_or_raise(body, "threadId")
        name = body_get_or_raise(body, "name")

        return await handle_get_agent_state(
            sdk=sdk,
            context=context,
            thread_id=thread_id,
            name=name,
        )

    return None


async def handle_info(
        *,
        sdk: CopilotKitRemoteEndpoint,
        context: CopilotKitContext,
        as_html: bool = False,
    ):
    """
    SDK 정보를 반환합니다.

    등록된 모든 액션과 에이전트의 목록 및 설명을 제공합니다.
    개발자가 브라우저에서 직접 확인할 수 있도록 HTML 형식도 지원합니다.

    Parameters
    ----------
    sdk : CopilotKitRemoteEndpoint
        CopilotKit SDK 인스턴스
    context : CopilotKitContext
        요청 컨텍스트
    as_html : bool, optional
        True인 경우 HTML 페이지로, False인 경우 JSON으로 반환

    Returns
    -------
    HTMLResponse or JSONResponse
        SDK 정보를 담은 응답

    Examples
    --------
    JSON 응답 형식:
    {
        "actions": [
            {
                "name": "search",
                "description": "Search the web",
                "parameters": [...]
            }
        ],
        "agents": [
            {
                "name": "email_agent",
                "type": "langgraph",
                "description": "Send emails"
            }
        ]
    }
    """
    result = sdk.info(context=context)
    if as_html:
        return HTMLResponse(content=generate_info_html(result))
    return JSONResponse(content=jsonable_encoder(result))


async def handle_execute_action(
        *,
        sdk: CopilotKitRemoteEndpoint,
        context: CopilotKitContext,
        name: str,
        arguments: dict,
    ):
    """
    액션을 실행합니다.

    클라이언트가 요청한 액션을 SDK를 통해 실행하고 결과를 반환합니다.
    액션은 사용자 정의 Python 함수로, 데이터베이스 쿼리, API 호출 등
    다양한 작업을 수행할 수 있습니다.

    Execution Flow:
    ```mermaid
    graph TD
        A[요청 수신] --> B[액션 이름 확인]
        B --> C{액션 존재?}
        C -->|No| D[404 ActionNotFound]
        C -->|Yes| E[액션 실행]
        E --> F{실행 성공?}
        F -->|No| G[500 ExecutionError]
        F -->|Yes| H[결과 반환]
        H --> I[JSONResponse]
    ```

    Parameters
    ----------
    sdk : CopilotKitRemoteEndpoint
        CopilotKit SDK 인스턴스
    context : CopilotKitContext
        요청 컨텍스트
    name : str
        실행할 액션의 이름
    arguments : dict
        액션에 전달할 인자들

    Returns
    -------
    JSONResponse
        액션 실행 결과 또는 에러 메시지

    Examples
    --------
    성공 응답:
    {
        "result": "Action executed successfully",
        "data": {...}
    }

    에러 응답 (404):
    {
        "error": "Action 'unknown_action' not found"
    }
    """
    try:
        result = await sdk.execute_action(
            context=context,
            name=name,
            arguments=arguments
        )
        return JSONResponse(content=jsonable_encoder(result))
    except ActionNotFoundException as exc:
        logger.error("Action not found: %s", exc)
        return JSONResponse(content={"error": str(exc)}, status_code=404)
    except ActionExecutionException as exc:
        logger.error("Action execution error: %s", exc)
        return JSONResponse(content={"error": str(exc)}, status_code=500)
    except Exception as exc: # pylint: disable=broad-except
        logger.error("Action execution error: %s", exc)
        return JSONResponse(content={"error": str(exc)}, status_code=500)


def handle_execute_agent( # pylint: disable=too-many-arguments
        *,
        sdk: CopilotKitRemoteEndpoint,
        context: CopilotKitContext,
        thread_id: str,
        name: str,
        state: dict,
        config: Optional[dict] = None,
        messages: List[Message],
        actions: List[ActionDict],
        node_name: str,
        meta_events: Optional[List[MetaEvent]] = None,
    ):
    """
    에이전트를 실행하고 이벤트를 스트리밍합니다.

    LangGraph 기반 에이전트를 실행하며, 실행 중 발생하는 모든 이벤트를
    Server-Sent Events (SSE) 형식으로 스트리밍합니다.
    클라이언트는 실시간으로 에이전트의 상태, 메시지, 도구 호출 등을
    받아볼 수 있습니다.

    Agent Execution Flow:
    ```mermaid
    graph TD
        A[요청 수신] --> B[에이전트 검색]
        B --> C{에이전트 존재?}
        C -->|No| D[404 AgentNotFound]
        C -->|Yes| E[스레드 설정]
        E --> F{스레드 ID 존재?}
        F -->|No| G[새 스레드 생성]
        F -->|Yes| H[기존 스레드 재개]
        G --> I[에이전트 실행]
        H --> I
        I --> J[이벤트 생성기]
        J --> K[StreamingResponse]
        K --> L[클라이언트]

        subgraph "스트리밍 이벤트"
        M[상태 동기화]
        N[메시지]
        O[도구 호출]
        P[에러]
        end

        J -.->|emit| M
        J -.->|emit| N
        J -.->|emit| O
        J -.->|emit| P
    ```

    Parameters
    ----------
    sdk : CopilotKitRemoteEndpoint
        CopilotKit SDK 인스턴스
    context : CopilotKitContext
        요청 컨텍스트
    thread_id : str
        대화 스레드 ID (없으면 새로 생성)
    name : str
        실행할 에이전트 이름
    state : dict
        에이전트 초기 상태
    config : Optional[dict]
        LangGraph 설정 (선택사항)
    messages : List[Message]
        사용자 메시지 목록
    actions : List[ActionDict]
        사용 가능한 액션 목록
    node_name : str
        재개할 LangGraph 노드 이름 (선택사항)
    meta_events : Optional[List[MetaEvent]]
        메타 이벤트 (인터럽트 등)

    Returns
    -------
    StreamingResponse
        Server-Sent Events 스트림
        Content-Type: application/json

    Notes
    -----
    스트리밍 이벤트 타입:
    - on_copilotkit_state_sync: 상태 동기화
    - on_chat_model_stream: AI 응답 스트리밍
    - on_tool_calls: 도구 호출 정보
    - error: 에러 발생

    스레드 관리:
    - 각 대화는 고유한 thread_id로 식별
    - thread_id를 재사용하면 이전 대화 이어서 진행
    - node_name으로 특정 지점부터 재개 가능
    """
    try:
        events = sdk.execute_agent(
            context=context,
            thread_id=thread_id,
            name=name,
            node_name=node_name,
            state=state,
            config=config,
            messages=messages,
            actions=actions,
            meta_events=meta_events,
        )
        return StreamingResponse(events, media_type="application/json")
    except AgentNotFoundException as exc:
        logger.error("Agent not found: %s", exc, exc_info=True)
        return JSONResponse(content={"error": str(exc)}, status_code=404)
    except AgentExecutionException as exc:
        logger.error("Agent execution error: %s", exc, exc_info=True)
        return JSONResponse(content={"error": str(exc)}, status_code=500)
    except Exception as exc: # pylint: disable=broad-except
        logger.error("Agent execution error: %s", exc, exc_info=True)
        return JSONResponse(content={"error": str(exc)}, status_code=500)


async def handle_get_agent_state(
        *,
        sdk: CopilotKitRemoteEndpoint,
        context: CopilotKitContext,
        thread_id: str,
        name: str,
    ):
    """
    에이전트의 현재 상태를 조회합니다.

    특정 스레드에 저장된 에이전트의 상태를 가져옵니다.
    대화 기록, 내부 상태 변수, 메시지 목록 등을 포함합니다.

    State Structure:
    ```mermaid
    graph LR
        A[Agent State] --> B[threadId]
        A --> C[threadExists]
        A --> D[state]
        A --> E[messages]

        D --> D1[내부 변수]
        D --> D2[컨텍스트]
        D --> D3[메타데이터]

        E --> E1[사용자 메시지]
        E --> E2[AI 응답]
        E --> E3[시스템 메시지]
    ```

    Parameters
    ----------
    sdk : CopilotKitRemoteEndpoint
        CopilotKit SDK 인스턴스
    context : CopilotKitContext
        요청 컨텍스트
    thread_id : str
        조회할 스레드 ID
    name : str
        에이전트 이름

    Returns
    -------
    JSONResponse
        에이전트 상태 정보

    Examples
    --------
    성공 응답:
    {
        "threadId": "thread_123",
        "threadExists": true,
        "state": {
            "step": 3,
            "context": {...}
        },
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
    }

    스레드가 없는 경우:
    {
        "threadId": "",
        "threadExists": false,
        "state": {},
        "messages": []
    }
    """
    try:
        result = await sdk.get_agent_state(
            context=context,
            thread_id=thread_id,
            name=name,
        )
        return JSONResponse(content=jsonable_encoder(result))
    except AgentNotFoundException as exc:
        logger.error("Agent not found: %s", exc, exc_info=True)
        return JSONResponse(content={"error": str(exc)}, status_code=404)
    except Exception as exc: # pylint: disable=broad-except
        logger.error("Agent get state error: %s", exc, exc_info=True)
        return JSONResponse(content={"error": str(exc)}, status_code=500)
