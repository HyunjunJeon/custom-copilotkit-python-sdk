# CopilotKit Python SDK (한글 문서화 버전)

> **Note**: 이 프로젝트는 [CopilotKit Python SDK](https://github.com/CopilotKit/CopilotKit/tree/main/sdk-python)를 커스터마이징한 버전입니다.
> **LangGraph 전용** - CrewAI 지원이 제거되었습니다.
> **완전한 한글 문서** - 핵심 모듈에 상세한 한글 주석과 Mermaid 다이어그램이 포함되어 있습니다.

[![PyPI version](https://badge.fury.io/py/copilotkit.svg)](https://badge.fury.io/py/copilotkit)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

AI 코파일럿과 에이전트를 애플리케이션에 통합하기 위한 Python SDK입니다.

---

## 주요 특징

- 🚀 **LangGraph/LangChain 통합** - 손쉬운 연동
- 🔄 **상태 기반 대화** - 스레드 기반 대화 관리 및 체크포인트
- 🛠 **확장 가능한 에이전트** - LangGraphAGUIAgent로 커스텀 에이전트 구축
- 🔌 **FastAPI 엔드포인트** - 즉시 사용 가능한 REST API
- 📚 **완전한 한글 문서** - 핵심 모듈에 상세한 한글 주석 및 Mermaid 다이어그램

<!-- CUSTOMIZATION: CrewAI support disabled -->
<!-- - 🤝 Optional CrewAI integration -->

---

## 설치

```bash
pip install copilotkit
```

<!-- CUSTOMIZATION: CrewAI support disabled -->
<!-- With CrewAI support:
```bash
pip install "copilotkit[crewai]"
``` -->

**로컬 개발 (이 커스터마이징 버전)**:

```bash
# uv를 사용한 설치
uv sync

# 또는 pip를 사용한 editable 설치
pip install -e copilotkit_sdk
```

---

## 빠른 시작

### 1. LangGraph 에이전트 정의

```python
from langgraph.graph import StateGraph, MessagesState
from langchain_core.messages import HumanMessage, AIMessage

# 간단한 에이전트 그래프 정의
def agent_node(state: MessagesState):
    return {
        "messages": [AIMessage(content="Hello! How can I help you?")]
    }

graph = StateGraph(MessagesState)
graph.add_node("agent", agent_node)
graph.set_entry_point("agent")
graph.set_finish_point("agent")

compiled_graph = graph.compile()
```

### 2. CopilotKit SDK 설정

```python
from copilotkit import CopilotKitRemoteEndpoint, LangGraphAGUIAgent
from copilotkit.integrations.fastapi import add_fastapi_endpoint
from fastapi import FastAPI
import uvicorn

# 에이전트 정의
agent = LangGraphAGUIAgent(
    name="assistant",
    description="도움을 주는 AI 어시스턴트",
    graph=compiled_graph
)

# SDK 인스턴스 생성
sdk = CopilotKitRemoteEndpoint(
    agents=[agent]
)

# FastAPI 앱에 엔드포인트 추가
app = FastAPI()
add_fastapi_endpoint(app, sdk, "/copilotkit")

# 서버 실행
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
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

---

## 한글 문서화

이 버전은 핵심 모듈에 대한 **완전한 한글 문서**를 제공합니다:

### 문서화된 모듈

#### 1. **`copilotkit/langgraph.py`** - LangGraph 통합 유틸리티
- **3개 Mermaid 다이어그램**:
  - Message Conversion Flow (CopilotKit ↔ LangChain)
  - Interrupt Handling Flow
  - Event Emission Flow
- **11개 함수/클래스 상세 문서**:
  - `copilotkit_messages_to_langchain()` - 메시지 변환
  - `langchain_messages_to_copilotkit()` - 역변환
  - `copilotkit_customize_config()` - 설정 커스터마이징
  - `copilotkit_exit()` - 에이전트 종료
  - `copilotkit_emit_state()` - 중간 상태 전송
  - `copilotkit_emit_message()` - 메시지 전송
  - `copilotkit_emit_tool_call()` - 도구 호출 표시
  - `copilotkit_interrupt()` - 사용자 입력 대기
  - `CopilotKitState`, `CopilotKitProperties`, `CopilotContextItem`

#### 2. **`copilotkit/sdk.py`** - SDK 진입점
- **2개 Mermaid 다이어그램**:
  - SDK Architecture (레이어 구조)
  - Dynamic Builder Pattern Flow
- **7개 메서드/클래스 상세 문서**:
  - `CopilotKitRemoteEndpoint` - 메인 SDK 클래스
  - `info()` - 사용 가능한 액션/에이전트 정보
  - `execute_action()` - 액션 실행
  - `execute_agent()` - 에이전트 실행
  - `get_agent_state()` - 에이전트 상태 조회

#### 3. **`copilotkit/types.py`** - 타입 정의
- **1개 Mermaid 다이어그램**:
  - Message Type Hierarchy
- **7개 TypedDict/Enum 상세 문서**:
  - `MessageRole`, `Message`, `TextMessage`
  - `ActionExecutionMessage`, `ResultMessage`
  - `IntermediateStateConfig`, `MetaEvent`

#### 4. **`copilotkit/integrations/fastapi.py`** - FastAPI 통합
- **4개 Mermaid 다이어그램**: 요청 라우팅 및 처리 플로우

#### 5. **`copilotkit/langgraph_agent.py`** - LangGraph 에이전트
- **3개 Mermaid 다이어그램**: 아키텍처 및 실행 플로우

#### 6. **`copilotkit/langgraph_agui_agent.py`** - AG-UI 에이전트
- **3개 Mermaid 다이어그램**: 이벤트 처리 플로우

### 문서 통계
- **총 ~2,400라인**의 한글 문서
- **16개 Mermaid 다이어그램**
- **모든 핵심 함수/클래스에 상세 docstring**
- Parameters, Returns, Raises, Examples, Notes 섹션 포함

---

## 커스터마이징 내역

이 버전은 다음과 같이 커스터마이징되었습니다:

### #1: CrewAI 지원 비활성화 (LangGraph 전용)
- **목적**: LangGraph 프레임워크에만 집중
- **영향**: CrewAI 관련 의존성 및 코드 제거
- **파일**: `__init__.py`, `sdk.py`, `html.py`, `crewai/__init__.py`, `pyproject.toml`

### #2: 한글 문서화 (FastAPI, LangGraph, AG-UI Agent)
- **목적**: 핵심 통합 및 에이전트 모듈 문서화
- **내용**: 10개 Mermaid 다이어그램, 상세 한글 주석

### #3: 한글 문서화 (Core Modules)
- **목적**: SDK 핵심 모듈 문서화
- **내용**: 6개 Mermaid 다이어그램, ~1,600라인 문서

**상세 내역**: [`../docs/CUSTOMIZATIONS.md`](../docs/CUSTOMIZATIONS.md) 참조

---

## 업스트림 동기화

이 프로젝트는 upstream CopilotKit SDK와 동기화를 유지합니다:

```bash
# 업스트림 추가 (최초 1회)
git subtree add --prefix=copilotkit_sdk \
  https://github.com/CopilotKit/CopilotKit.git main:sdk-python --squash

# 업스트림 업데이트 (새 버전 가져오기)
git subtree pull --prefix=copilotkit_sdk \
  https://github.com/CopilotKit/CopilotKit.git main:sdk-python --squash
```

**주의**: 업스트림 업데이트 후 커스터마이징을 재적용해야 합니다.
상세 가이드: [`../docs/UPSTREAM_SYNC.md`](../docs/UPSTREAM_SYNC.md)

---

## 프로젝트 구조

```
251029_online_seminar/
├── copilotkit_sdk/          # CopilotKit SDK (커스터마이징 버전)
│   ├── copilotkit/
│   │   ├── langgraph.py     # ⭐ LangGraph 유틸리티 (한글 문서)
│   │   ├── sdk.py           # ⭐ SDK 진입점 (한글 문서)
│   │   ├── types.py         # ⭐ 타입 정의 (한글 문서)
│   │   ├── langgraph_agent.py         # ⭐ LangGraph 에이전트 (한글 문서)
│   │   ├── langgraph_agui_agent.py    # ⭐ AG-UI 에이전트 (한글 문서)
│   │   ├── integrations/
│   │   │   └── fastapi.py   # ⭐ FastAPI 통합 (한글 문서)
│   │   └── ...
│   └── pyproject.toml
├── src/                     # 커스텀 코드
├── docs/                    # 문서
│   ├── CUSTOMIZATIONS.md    # ⭐ 커스터마이징 로그
│   └── UPSTREAM_SYNC.md     # 업스트림 동기화 가이드
└── tests/                   # 테스트
```

---

## 개발 가이드

### 의존성 설치

```bash
# uv 사용 (권장)
uv sync

# pip 사용
pip install -e copilotkit_sdk
```

### 테스트

```bash
# 임포트 테스트
uv run python -c "
from copilotkit import CopilotKitRemoteEndpoint, LangGraphAGUIAgent
from copilotkit.langgraph import CopilotKitState
print('✓ All imports successful!')
"
```

### 커스터마이징 추가 시

1. 변경사항 구현
2. `docs/CUSTOMIZATIONS.md`에 기록
3. 테스트 실행
4. 커밋 (마커 추가: `# CUSTOMIZATION: ...`)

---

**Base Version**: v0.1.70 (2025-10-28)
**Upstream**: https://github.com/CopilotKit/CopilotKit/tree/main/sdk-python
**Last Sync**: 2025-10-28

Built with ❤️ by the CopilotKit team | 한글 문서화 by Development Team
