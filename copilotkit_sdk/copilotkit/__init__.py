"""
CopilotKit Python SDK - AI 코파일럿 통합 프레임워크

이 패키지는 AI 코파일럿과 에이전트를 애플리케이션에 통합하기 위한 Python SDK입니다.
LangGraph/LangChain 프레임워크와의 손쉬운 연동을 제공하며, FastAPI 엔드포인트를 통해
클라이언트와 실시간으로 통신할 수 있습니다.

주요 컴포넌트
-------------

1. **CopilotKitRemoteEndpoint** (sdk.py)
   - SDK의 핵심 진입점
   - 액션(Action)과 에이전트(Agent) 등록 및 관리
   - 클라이언트 요청을 적절한 핸들러로 라우팅

2. **Action** (action.py)
   - 사용자 정의 액션 (함수 호출) 정의
   - 동기/비동기 핸들러 지원
   - 파라미터 스키마 정의

3. **Agent** (agent.py)
   - 에이전트 추상 베이스 클래스
   - LangGraphAgent, LangGraphAGUIAgent 등 구현체 제공
   - 상태 기반 대화 관리

4. **Parameter** (parameter.py)
   - 액션 파라미터 타입 정의
   - SimpleParameter, ObjectParameter, StringParameter 지원
   - 중첩 객체 및 배열 타입 지원

5. **CopilotKitState** (langgraph.py)
   - LangGraph 상태 관리를 위한 TypedDict
   - 메시지, 프로퍼티, 인터럽트 정보 포함

Package Structure
-----------------

```mermaid
graph TB
    subgraph "Public API (사용자 대면)"
    SDK[CopilotKitRemoteEndpoint]
    ACT[Action]
    AGT[Agent]
    PARAM[Parameter]
    STATE[CopilotKitState]
    end

    subgraph "Agent Implementations (에이전트 구현)"
    LG[LangGraphAgent]
    LGAGUI[LangGraphAGUIAgent]
    end

    subgraph "Integration Layer (통합 레이어)"
    FASTAPI[integrations.fastapi]
    end

    subgraph "Core Utilities (핵심 유틸리티)"
    LANGGRAPH[langgraph.py]
    PROTOCOL[protocol.py]
    RUNLOOP[runloop.py]
    end

    subgraph "Type Definitions (타입 정의)"
    TYPES[types.py]
    end

    SDK --> ACT
    SDK --> AGT
    AGT --> LG
    AGT --> LGAGUI
    ACT --> PARAM
    LG --> LANGGRAPH
    LGAGUI --> LANGGRAPH
    LANGGRAPH --> STATE
    LANGGRAPH --> TYPES
    FASTAPI --> SDK
    SDK --> PROTOCOL
    SDK --> RUNLOOP
    PROTOCOL --> TYPES

    style SDK fill:#e1f5ff,stroke:#0066cc,stroke-width:3px
    style ACT fill:#fff4e1,stroke:#ff9900,stroke-width:2px
    style AGT fill:#ffe1e1,stroke:#cc0000,stroke-width:2px
    style PARAM fill:#e1ffe1,stroke:#00cc00,stroke-width:2px
    style STATE fill:#f0e1ff,stroke:#9900cc,stroke-width:2px
```

Quick Start
-----------

### 1. 간단한 액션 정의

```python
from copilotkit import CopilotKitRemoteEndpoint, Action
from copilotkit.integrations.fastapi import add_fastapi_endpoint
from fastapi import FastAPI
import uvicorn

# 액션 핸들러 정의
def send_email(to: str, subject: str, body: str):
    '''이메일을 전송합니다'''
    print(f"Sending email to {to}: {subject}")
    return {"status": "sent", "to": to}

# 액션 생성
email_action = Action(
    name="send_email",
    description="사용자에게 이메일을 전송합니다",
    handler=send_email,
    parameters=[
        {"name": "to", "type": "string", "description": "수신자 이메일"},
        {"name": "subject", "type": "string", "description": "이메일 제목"},
        {"name": "body", "type": "string", "description": "이메일 본문"}
    ]
)

# SDK 인스턴스 생성
sdk = CopilotKitRemoteEndpoint(actions=[email_action])

# FastAPI 앱에 엔드포인트 추가
app = FastAPI()
add_fastapi_endpoint(app, sdk, "/copilotkit")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 2. LangGraph 에이전트 통합

```python
from copilotkit import CopilotKitRemoteEndpoint, LangGraphAGUIAgent
from langgraph.graph import StateGraph, MessagesState
from langchain_core.messages import AIMessage

# LangGraph 그래프 정의
def agent_node(state: MessagesState):
    return {"messages": [AIMessage(content="Hello! How can I help?")]}

graph = StateGraph(MessagesState)
graph.add_node("agent", agent_node)
graph.set_entry_point("agent")
graph.set_finish_point("agent")
compiled_graph = graph.compile()

# 에이전트 생성
agent = LangGraphAGUIAgent(
    name="assistant",
    description="도움을 주는 AI 어시스턴트",
    graph=compiled_graph
)

# SDK 인스턴스 생성
sdk = CopilotKitRemoteEndpoint(agents=[agent])
```

### 3. 프론트엔드 연결

```typescript
import { CopilotKit } from "@copilotkit/react-core";

function App() {
  return (
    <CopilotKit runtimeUrl="http://localhost:8000/copilotkit">
      {/* Your app components */}
    </CopilotKit>
  );
}
```

Public API Reference
--------------------

이 패키지에서 export하는 모든 클래스와 함수:

- **CopilotKitRemoteEndpoint**: SDK 메인 클래스
- **CopilotKitSDK**: RemoteEndpoint의 별칭 (deprecated)
- **Action**: 액션 정의 클래스
- **Agent**: 에이전트 추상 베이스 클래스
- **LangGraphAgent**: LangGraph 통합 에이전트
- **LangGraphAGUIAgent**: LangGraph AG-UI 이벤트 지원 에이전트
- **Parameter**: 파라미터 타입 정의 (Union type)
- **CopilotKitState**: LangGraph 상태 TypedDict
- **CopilotKitContext**: 실행 컨텍스트 (동적 빌더용)
- **CopilotKitSDKContext**: SDK 컨텍스트 (별칭)

Import Examples
---------------

### 기본 import
```python
from copilotkit import CopilotKitRemoteEndpoint, Action, Parameter
```

### 에이전트 import
```python
from copilotkit import Agent, LangGraphAgent, LangGraphAGUIAgent
```

### LangGraph 유틸리티 import (직접 import 필요)
```python
from copilotkit.langgraph import (
    CopilotKitState,
    copilotkit_messages_to_langchain,
    langchain_messages_to_copilotkit,
    copilotkit_customize_config,
    copilotkit_emit_state,
    copilotkit_interrupt
)
```

### FastAPI 통합 import (직접 import 필요)
```python
from copilotkit.integrations.fastapi import add_fastapi_endpoint
```

Notes
-----

- **CrewAI 지원**: 이 버전에서는 CrewAI 지원이 비활성화되었습니다
  (Customization #1 참조)

- **LangGraph 전용**: 이 SDK는 LangGraph/LangChain 프레임워크에 최적화되어 있습니다

- **한글 문서**: 핵심 모듈에 상세한 한글 주석과 Mermaid 다이어그램이
  포함되어 있습니다. 자세한 내용은 각 모듈의 docstring을 참조하세요.

See Also
--------

- CopilotKitRemoteEndpoint: SDK 메인 클래스 (copilotkit.sdk)
- Action: 액션 정의 (copilotkit.action)
- Agent: 에이전트 베이스 클래스 (copilotkit.agent)
- LangGraphAGUIAgent: AG-UI 에이전트 (copilotkit.langgraph_agui_agent)
- add_fastapi_endpoint: FastAPI 통합 (copilotkit.integrations.fastapi)
- CODE_NAVIGATION.md: 코드 네비게이션 가이드 (../docs/)
- README.md: 프로젝트 전체 문서 (../README.md)

Version
-------

이 버전은 CopilotKit Python SDK의 커스터마이징 버전입니다.
Base Version: v0.1.70 (2025-10-28)
Upstream: https://github.com/CopilotKit/CopilotKit/tree/main/sdk-python
"""
from .sdk import CopilotKitRemoteEndpoint, CopilotKitContext, CopilotKitSDK, CopilotKitSDKContext
from .action import Action
from .langgraph import CopilotKitState
from .parameter import Parameter
from .agent import Agent
from .langgraph_agent import LangGraphAgent
from .langgraph_agui_agent import LangGraphAGUIAgent



__all__ = [
    'CopilotKitRemoteEndpoint',
    'CopilotKitSDK',
    'Action',
    'CopilotKitState',
    'Parameter',
    'Agent',
    'CopilotKitContext',
    'CopilotKitSDKContext',
    # 'CrewAIAgent', # pyright: ignore[reportUnsupportedDunderAll] pylint: disable=undefined-all-variable  # CUSTOMIZATION: CrewAI support disabled
    'LangGraphAgent', # pyright: ignore[reportUnsupportedDunderAll] pylint: disable=undefined-all-variable
    "LangGraphAGUIAgent"
]
