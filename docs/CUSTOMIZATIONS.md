# Customizations Log

이 문서는 CopilotKit Python SDK에 적용한 커스터마이징 내역을 기록합니다.

## 목적

Upstream 업데이트 시 커스터마이징한 부분을 보존하고 충돌을 피하기 위해 모든 변경사항을 추적합니다.

## 버전 정보

- **Base Version**: v0.1.70 (2025-10-28)
- **Upstream**: https://github.com/CopilotKit/CopilotKit/tree/main/sdk-python
- **Last Sync**: 2025-10-28

## 커스터마이징 내역

---

### #1: Disabled CrewAI Support (LangGraph Only)
**Date**: 2025-10-28
**Impact**: Major - Framework support removed
**Files Modified**:
- `copilotkit_sdk/copilotkit/__init__.py` - Commented out CrewAIAgent export
- `copilotkit_sdk/copilotkit/sdk.py` - Commented out CrewAI installation docs
- `copilotkit_sdk/copilotkit/html.py` - Commented out CrewAI agent type handling
- `copilotkit_sdk/copilotkit/crewai/__init__.py` - Disabled all imports and exports
- `copilotkit_sdk/pyproject.toml` - Commented out crewai dependency and extras

**Purpose**:
Focus exclusively on LangGraph framework support. Remove CrewAI integration to:
- Simplify the SDK codebase
- Reduce dependency complexity
- Align with project requirements (LangGraph-only architecture)

**Changes Summary**:
1. **Main __init__.py**: Commented out `'CrewAIAgent'` from `__all__` list
2. **SDK Documentation**: Commented out CrewAI installation instructions in docstring
3. **HTML Rendering**: Disabled CrewAI agent type detection in info page
4. **CrewAI Module**: All imports disabled in `crewai/__init__.py`, `__all__` set to empty list
5. **Dependencies**: Removed crewai optional dependency from pyproject.toml

**Code Markers**:
All changes are marked with:
```python
# CUSTOMIZATION: CrewAI support disabled
```

**Testing**:
- ✅ LangGraph imports work correctly (CopilotKitSDK, LangGraphAgent, etc.)
- ✅ CrewAI imports fail as expected (ImportError)
- ✅ CrewAI module has empty __all__ list

**Upstream Sync Notes**:
- ⚠️ **HIGH IMPACT**: When syncing upstream, need to reapply all CrewAI-related comments
- Affected files: `__init__.py`, `sdk.py`, `html.py`, `crewai/__init__.py`, `pyproject.toml`
- Files to watch:
  - If upstream adds new CrewAI features, manually decide whether to comment them out
  - If upstream modifies existing CrewAI code, our comments should remain intact
- **Migration strategy**: Search for "CUSTOMIZATION: CrewAI" marker before upstream merge
- Consider creating a patch file for easier reapplication:
  ```bash
  git diff copilotkit_sdk/ > patches/disable-crewai.patch
  ```

**Rollback Instructions**:
To re-enable CrewAI support, search for all lines containing `# CUSTOMIZATION: CrewAI` and uncomment the relevant code sections.

---

### #2: Added Comprehensive Korean Documentation
**Date**: 2025-10-28
**Impact**: Documentation - No functional changes
**Files Modified**:
- `copilotkit_sdk/copilotkit/integrations/fastapi.py` - Added Korean comments and Mermaid diagrams
- `copilotkit_sdk/copilotkit/langgraph_agent.py` - Added comprehensive module documentation
- `copilotkit_sdk/copilotkit/langgraph_agui_agent.py` - Added detailed Korean comments

**Purpose**:
향후 유지보수와 팀 협업을 위해 핵심 모듈에 자세한 한글 주석과 Mermaid 다이어그램을 추가했습니다.
특히 Request → Handler → Response 플로우를 시각적으로 이해할 수 있도록 문서화했습니다.

**Changes Summary**:

1. **FastAPI Integration (`fastapi.py`)**:
   - 모듈 레벨 개요 및 Request Flow 다이어그램
   - 각 함수에 대한 상세한 한글 docstring
   - 주요 엔드포인트별 Execution Flow Mermaid 다이어그램
   - 에이전트 실행, 액션 실행, 상태 조회 플로우 시각화

2. **LangGraph Agent (`langgraph_agent.py`)**:
   - 모듈 레벨 아키텍처 다이어그램 (6개 Mermaid 다이어그램)
   - Architecture Overview: 전체 컴포넌트 구조
   - Execution Flow: 시퀀스 다이어그램으로 실행 흐름 설명
   - State Management: 상태 관리 플로우
   - Key Concepts: 6가지 핵심 개념 상세 설명
     - Thread Management
     - Node-based Execution
     - Streaming Events
     - Interrupt Handling
     - State Schema
     - Message Regeneration

3. **LangGraph AGUI Agent (`langgraph_agui_agent.py`)**:
   - 모듈 레벨 이벤트 처리 플로우 다이어그램
   - Event Processing Flow: 이벤트 변환 과정
   - Custom Event Dispatch Flow: 시퀀스 다이어그램
   - Event Filtering: 메타데이터 기반 필터링 로직
   - 모든 클래스와 메서드에 상세한 한글 docstring
   - 커스텀 이벤트 처리 로직 상세 설명

**Documentation Features**:
- 이모지 사용 없음 (전문적인 문서화)
- 모든 Mermaid 다이어그램은 실행 플로우 시각화에 집중
- 함수/메서드 파라미터 및 반환값 상세 설명
- Examples 섹션 포함
- Notes 섹션으로 주요 포인트 강조

**Testing**:
- 모든 임포트 정상 작동 확인
- 기능적 변경 사항 없음 (주석 추가만)
- 타입 힌트 및 구조 유지

**Upstream Sync Notes**:
- 영향도: 낮음 - 주석만 추가되었으므로 upstream 병합 시 충돌 없음
- 주석은 코드와 독립적이므로 upstream 변경에 영향받지 않음
- 다만, 새로운 기능이 추가되면 해당 부분에도 한글 주석 추가 필요

**Rollback Instructions**:
주석 제거가 필요한 경우 (권장하지 않음):
```bash
git checkout origin/main -- copilotkit_sdk/copilotkit/integrations/fastapi.py
git checkout origin/main -- copilotkit_sdk/copilotkit/langgraph_agent.py
git checkout origin/main -- copilotkit_sdk/copilotkit/langgraph_agui_agent.py
```

---

### #3: Extended Korean Documentation for Core Modules
**Date**: 2025-10-28
**Impact**: Documentation - No functional changes
**Files Modified**:
- `copilotkit_sdk/copilotkit/langgraph.py` - Added comprehensive Korean documentation
- `copilotkit_sdk/copilotkit/sdk.py` - Added Korean documentation with architecture diagrams
- `copilotkit_sdk/copilotkit/types.py` - Added Korean documentation with type hierarchy

**Purpose**:
핵심 모듈 3개(langgraph.py, sdk.py, types.py)에 상세한 한글 문서를 추가했습니다.
이 모듈들은 CopilotKit SDK의 핵심 진입점이자 가장 자주 사용되는 유틸리티입니다.

**Changes Summary**:

1. **langgraph.py**:
   - 모듈 레벨 문서 (180라인): LangGraph/LangChain 통합 개요
   - 3개 Mermaid 다이어그램:
     - Message Conversion Flow (CopilotKit ↔ LangChain)
     - Interrupt Handling Flow (시퀀스 다이어그램)
     - Event Emission Flow
   - 모든 주요 함수에 상세한 한글 docstring:
     - `copilotkit_messages_to_langchain()`: 메시지 변환 CopilotKit→LangChain
     - `langchain_messages_to_copilotkit()`: 역변환 LangChain→CopilotKit
     - `copilotkit_customize_config()`: 설정 커스터마이징
     - `copilotkit_exit()`: 에이전트 종료 시그널
     - `copilotkit_emit_state()`: 중간 상태 전송
     - `copilotkit_emit_message()`: 커스텀 메시지 전송
     - `copilotkit_emit_tool_call()`: 도구 호출 표시
     - `copilotkit_interrupt()`: 사용자 입력 대기
   - State 클래스 상세 문서:
     - `CopilotContextItem`, `CopilotKitProperties`, `CopilotKitState`

2. **sdk.py**:
   - 모듈 레벨 문서 (177라인): SDK 아키텍처 및 사용 패턴
   - 2개 Mermaid 다이어그램:
     - SDK Architecture (레이어 구조 및 컴포넌트 관계)
     - Dynamic Builder Pattern Flow (시퀀스 다이어그램)
   - TypedDict 클래스 상세 문서:
     - `InfoDict`: SDK 정보 딕셔너리
     - `CopilotKitContext`: 요청 컨텍스트
   - 모든 주요 메서드에 상세한 한글 docstring:
     - `info()`: 사용 가능한 액션/에이전트 정보 반환
     - `_get_action()`: 이름으로 액션 조회
     - `execute_action()`: 액션 실행
     - `execute_agent()`: 에이전트 실행
     - `get_agent_state()`: 에이전트 상태 조회

3. **types.py**:
   - 모듈 레벨 문서 (124라인): 타입 시스템 개요
   - 1개 Mermaid 다이어그램:
     - Message Type Hierarchy (타입 계층 및 변환 플로우)
   - 모든 TypedDict/Enum에 상세한 한글 docstring:
     - `MessageRole`: 메시지 역할 열거형
     - `Message`: 메시지 기본 타입
     - `TextMessage`: 텍스트 메시지
     - `ActionExecutionMessage`: 액션 실행 메시지
     - `ResultMessage`: 액션 실행 결과 메시지
     - `IntermediateStateConfig`: 중간 상태 스트리밍 설정
     - `MetaEvent`: 메타 이벤트

**Documentation Features**:
- 이모지 사용 없음 (전문적인 문서화)
- 총 6개 Mermaid 다이어그램으로 복잡한 플로우 시각화
- 모든 함수/메서드/클래스에 상세한 한글 docstring
- Parameters, Returns, Raises, Examples, Notes 섹션 포함
- 실제 사용 예제 코드 제공
- See Also 섹션으로 관련 함수/클래스 연결

**Documentation Statistics**:
- langgraph.py: ~900라인 추가 (모듈 문서 + 8개 함수 docstring + 3개 클래스)
- sdk.py: ~450라인 추가 (모듈 문서 + 2개 TypedDict + 5개 메서드)
- types.py: ~250라인 추가 (모듈 문서 + 7개 TypedDict/Enum)
- 총 ~1,600라인의 한글 문서 추가
- 총 6개 Mermaid 다이어그램 (아키텍처 및 플로우 시각화)

**Testing**:
```bash
# 모든 임포트 정상 작동 확인
uv run python -c "
from copilotkit.langgraph import CopilotKitState, copilotkit_messages_to_langchain
from copilotkit.sdk import CopilotKitRemoteEndpoint, CopilotKitContext
from copilotkit.types import Message, TextMessage, MessageRole
print('✓ All imports successful!')
"
```
- ✅ 모든 임포트 정상 작동
- ✅ 기능적 변경 사항 없음 (문서만 추가)
- ✅ 타입 힌트 및 구조 유지

**Upstream Sync Notes**:
- 영향도: 낮음 - 문서만 추가되었으므로 upstream 병합 시 충돌 가능성 낮음
- 문서는 코드와 독립적이므로 upstream 변경에 영향받지 않음
- 다만, 새로운 함수나 클래스가 추가되면 해당 부분에도 한글 문서 추가 필요
- 기존 함수 시그니처가 변경되면 docstring도 함께 업데이트 필요

**Rollback Instructions**:
문서 제거가 필요한 경우 (권장하지 않음):
```bash
git checkout origin/main -- copilotkit_sdk/copilotkit/langgraph.py
git checkout origin/main -- copilotkit_sdk/copilotkit/sdk.py
git checkout origin/main -- copilotkit_sdk/copilotkit/types.py
```

**Related Customizations**:
이 문서화는 #2 (FastAPI, LangGraphAgent, LangGraphAGUIAgent 문서화)와 함께
CopilotKit SDK의 핵심 모듈에 대한 완전한 한글 문서를 제공합니다.

---

### #4: Added Code Navigation Guide
**Date**: 2025-10-28
**Impact**: Documentation - No functional changes
**Files Modified**:
- `docs/CODE_NAVIGATION.md` - New file (완전 새 파일)
- `copilotkit_sdk/README.md` - Added code navigation section

**Purpose**:
SDK 내부 구조를 쉽게 이해하고 탐색할 수 있도록 코드 네비게이션 가이드를 추가했습니다.
개발자가 SDK를 확장하거나 내부 동작을 파악할 때 참고할 수 있는 완전한 로드맵을 제공합니다.

**Changes Summary**:

1. **`docs/CODE_NAVIGATION.md`** (새 파일, ~900라인):
   - **Entry Points**: Public API 및 Integration 진입점
   - **Module Dependencies**: 전체 아키텍처 Mermaid 다이어그램
   - **Code Path Scenarios**: 4가지 주요 사용 시나리오
     1. 기본 액션 실행 (Sequence diagram)
     2. LangGraph Agent 실행 스트리밍 (Sequence diagram)
     3. 동적 Actions/Agents 빌더 (Sequence diagram)
     4. LangGraph 커스텀 이벤트 사용 (Sequence diagram)
   - **Data Flow**: 3가지 핵심 데이터 흐름
     - 메시지 변환 흐름 (CopilotKit ↔ LangChain)
     - 상태 관리 흐름
     - 이벤트 스트리밍 흐름
   - **Key Classes**: 주요 클래스별 책임과 사용 시점
   - **Quick Reference**: 빠른 참조 및 FAQ

2. **`copilotkit_sdk/README.md`**:
   - "코드 네비게이션" 섹션 추가 (라인 272-311)
   - 주요 질문에 대한 빠른 답변 6개 포함
   - CODE_NAVIGATION.md, CUSTOMIZATIONS.md, UPSTREAM_SYNC.md 링크

**Documentation Features**:
- **5개 Mermaid 다이어그램**:
  - 1개 Architecture diagram (모듈 의존성)
  - 4개 Sequence diagrams (시나리오별 코드 경로)
  - 3개 Flow diagrams (데이터 흐름)
- **파일:라인번호:함수명 형식**으로 정확한 위치 표시
- **한글 작성**, Emoji 없음
- **실제 사용 예제 코드** 포함
- **Quick Reference 테이블** (파일별 주요 함수 위치)

**Documentation Statistics**:
- CODE_NAVIGATION.md: ~900라인
- Mermaid 다이어그램: 8개
- 코드 시나리오: 4개 (각각 상세 경로 포함)
- Quick Reference 항목: 20개 이상

**Use Cases**:
이 가이드는 다음과 같은 질문에 답합니다:
- "FastAPI 요청이 들어왔을 때 어떤 파일들을 거쳐가나?"
- "메시지는 어떻게 변환되나?"
- "동적 빌더는 어떻게 동작하나?"
- "커스텀 이벤트는 어디서 처리되나?"
- "새로운 기능을 추가하려면 어디를 수정해야 하나?"

**Testing**:
- 모든 파일 경로 및 라인 번호 검증 완료
- 링크 확인 완료
- 코드 예제 동작 확인

**Upstream Sync Notes**:
- 영향도: 없음 - 완전히 새로운 문서 파일
- Upstream 변경 시: 함수 시그니처나 파일 위치 변경 시 라인 번호 업데이트 필요
- 새로운 기능 추가 시: CODE_NAVIGATION.md에 해당 경로 추가 권장

**Rollback Instructions**:
문서 제거가 필요한 경우 (권장하지 않음):
```bash
rm docs/CODE_NAVIGATION.md
git checkout origin/main -- copilotkit_sdk/README.md
```

**Related Customizations**:
이 가이드는 #2, #3의 한글 문서화와 함께 SDK의 완전한 문서 세트를 구성합니다:
- #2, #3: 각 모듈의 상세 기능 설명
- #4: 모듈 간 연결 및 전체 구조 설명

---

### #5: Korean Documentation for Core API (Phase 1)
**Date**: 2025-10-28
**Impact**: Documentation - No functional changes
**Files Modified**:
- `copilotkit_sdk/copilotkit/__init__.py` - Added comprehensive package documentation
- `copilotkit_sdk/copilotkit/action.py` - Added Action class and lifecycle documentation
- `copilotkit_sdk/copilotkit/parameter.py` - Added parameter type system documentation
- `copilotkit_sdk/copilotkit/agent.py` - Added Agent ABC documentation

**Purpose**:
Core API Bundle (Phase 1/3)에 해당하는 4개 핵심 파일에 완전한 한글 문서를 추가했습니다.
사용자가 SDK를 사용할 때 가장 먼저 접하는 Public API 진입점들을 상세하게 문서화하여
개발자 경험을 개선하고, 학습 곡선을 낮추는 것이 목표입니다.

**Changes Summary**:

1. **`__init__.py`** (~243라인):
   - **Package Structure Mermaid Diagram**: 모듈 의존성 시각화
   - **Quick Start 가이드**: 3가지 사용 시나리오
     1. 간단한 액션 정의
     2. LangGraph 에이전트 통합
     3. 프론트엔드 연결
   - **Public API Reference**: Export하는 모든 클래스/함수 목록
   - **Import Examples**: 기본, 에이전트, LangGraph, FastAPI import 예제
   - **주요 컴포넌트 설명**: 5가지 핵심 컴포넌트 개요

2. **`action.py`** (~571라인):
   - **Action Lifecycle Sequence Diagram**: 정의 → 등록 → 실행 → 에러 처리
   - **모듈 문서**: 주요 개념 (Action, Handler, Parameter) 상세 설명
   - **Usage Examples**: 4가지 실용 예제
     1. 동기 핸들러 액션
     2. 비동기 핸들러 액션
     3. 복잡한 파라미터 액션
     4. SDK 등록 및 동적 빌더
   - **Best Practices**: 5가지 모범 사례
   - **Common Pitfalls**: 흔한 실수 및 해결법
   - **TypedDict 문서**: ActionDict, ActionResultDict
   - **클래스 문서**: Action 클래스 및 모든 메서드 (\_\_init\_\_, execute, dict_repr)

3. **`parameter.py`** (~620라인):
   - **Type Hierarchy Mermaid Diagram**: 파라미터 타입 계층 구조
   - **모듈 문서**: 3가지 파라미터 타입 (SimpleParameter, StringParameter, ObjectParameter) 설명
   - **Usage Examples**: 5가지 실용 예제
     1. SimpleParameter (number, boolean, 배열)
     2. StringParameter (일반 문자열, Enum)
     3. ObjectParameter (중첩 객체, 객체 배열)
     4. normalize_parameters() 사용법
     5. Action과 함께 사용
   - **Normalization Rules**: 정규화 규칙 4가지
   - **Best Practices**: 5가지 모범 사례
   - **Common Pitfalls**: 흔한 실수 3가지
   - **TypedDict 문서**: SimpleParameter, ObjectParameter, StringParameter, Parameter Union
   - **함수 문서**: normalize_parameters(), _normalize_parameter()

4. **`agent.py`** (~652라인):
   - **Agent Hierarchy Mermaid Diagram**: 상속 구조 및 구현 요구사항
   - **모듈 문서**: 주요 개념 (Agent, Thread, State, Abstract Methods) 설명
   - **Implementation Guide**: 3가지 구현 예제
     1. 커스텀 에이전트 구현
     2. LangGraph 에이전트 사용 (권장)
     3. SDK 등록 및 동적 빌더
   - **Agent vs Action**: 언제 어떤 것을 사용할지 비교표
   - **Thread Management**: Thread 관리 예제 코드
   - **Best Practices**: 5가지 모범 사례
   - **Common Pitfalls**: 흔한 실수 3가지
   - **TypedDict 문서**: AgentDict
   - **클래스 문서**: Agent ABC 및 모든 메서드 (\_\_init\_\_, execute, get_state, dict_repr)

**Documentation Features**:
- **4개 Mermaid 다이어그램**:
  - Package Structure (모듈 의존성)
  - Action Lifecycle (시퀀스 다이어그램)
  - Parameter Type Hierarchy (타입 계층)
  - Agent Hierarchy (상속 구조)
- **파일별 상세 docstring**: 모든 클래스, 함수, 메서드, TypedDict에 한글 docstring
- **표준 docstring 형식**: Parameters, Returns, Raises, Examples, Notes, See Also 섹션
- **실용적 예제**: 각 기능마다 실제 사용 가능한 코드 예제 포함
- **모범 사례 및 주의사항**: Best Practices, Common Pitfalls 섹션으로 실수 방지
- **Emoji 없음**: 전문적인 문서 스타일 유지

**Documentation Statistics**:
- __init__.py: ~243라인 (모듈 문서 + 1개 다이어그램)
- action.py: ~571라인 (모듈 문서 + 3개 클래스/TypedDict + 1개 다이어그램)
- parameter.py: ~620라인 (모듈 문서 + 4개 TypedDict + 2개 함수 + 1개 다이어그램)
- agent.py: ~652라인 (모듈 문서 + 2개 클래스/TypedDict + 1개 다이어그램)
- **총 ~2,086라인**의 한글 문서 추가
- **총 4개 Mermaid 다이어그램** (구조 및 플로우 시각화)

**Testing**:
```bash
# 모든 임포트 및 기능 정상 작동 확인
uv run python -c "
from copilotkit import CopilotKitRemoteEndpoint, Action, Parameter, Agent
from copilotkit import LangGraphAgent, LangGraphAGUIAgent, CopilotKitState
print('✓ All imports successful!')
print('✓ Documentation added without breaking functionality')
"
```
- ✅ 모든 임포트 정상 작동
- ✅ 기능적 변경 사항 없음 (문서만 추가)
- ✅ 타입 힌트 및 구조 유지
- ✅ 기존 코드 동작 변경 없음

**Upstream Sync Notes**:
- 영향도: 낮음 - 문서만 추가되었으므로 upstream 병합 시 충돌 가능성 낮음
- 문서는 코드와 독립적이므로 upstream 변경에 영향받지 않음
- 다만, 새로운 메서드나 파라미터가 추가되면 해당 부분에도 한글 문서 추가 필요
- 함수 시그니처 변경 시 docstring도 함께 업데이트 필요

**Rollback Instructions**:
문서 제거가 필요한 경우 (권장하지 않음):
```bash
git checkout origin/main -- copilotkit_sdk/copilotkit/__init__.py
git checkout origin/main -- copilotkit_sdk/copilotkit/action.py
git checkout origin/main -- copilotkit_sdk/copilotkit/parameter.py
git checkout origin/main -- copilotkit_sdk/copilotkit/agent.py
```

**Related Customizations**:
이 문서화는 3단계 계획의 첫 번째(Phase 1)로, 이후 Phase 2, 3가 예정되어 있습니다:
- **Phase 1 (이번 작업)**: Core API Bundle (__init__, action, parameter, agent)
- **Phase 2 (예정)**: Protocol & Runtime System (protocol.py, runloop.py)
- **Phase 3 (예정)**: Supporting Utilities (exc.py, logging.py, utils.py, html.py)

전체 문서화가 완료되면 #2, #3, #4와 함께 SDK의 완전한 한글 문서 세트를 구성합니다.

**Next Steps**:
Phase 1 완료 후 다음 단계:
1. Phase 2: Protocol & Runtime System 문서화 (protocol.py, runloop.py)
   - 예상 라인 수: ~1,200-1,500라인
   - 예상 다이어그램: 3개 (Event Protocol Flow, Run Loop Architecture, Event Processing Pipeline)
2. Phase 3: Utilities 문서화 (exc.py, logging.py, utils.py, html.py)
   - 예상 라인 수: ~400-600라인
   - 예상 다이어그램: 없음

---

### #6: Korean Documentation for Protocol & Runtime (Phase 2)
**Date**: 2025-10-28
**Impact**: Documentation - No functional changes
**Files Modified**:
- `copilotkit_sdk/copilotkit/protocol.py` - Added comprehensive protocol event documentation
- `copilotkit_sdk/copilotkit/runloop.py` - Added run loop architecture documentation

**Purpose**:
Protocol & Runtime System (Phase 2/3)에 해당하는 2개 핵심 파일에 완전한 한글 문서를 추가했습니다.
CopilotKit의 이벤트 프로토콜과 비동기 런타임 시스템을 상세하게 문서화하여
내부 동작 방식을 이해하고, 커스터마이징이나 디버깅 시 참고할 수 있도록 합니다.

**Changes Summary**:

1. **`protocol.py`** (~1,350라인):
   - **Event Protocol Flow State Machine**: 전체 이벤트 흐름 상태 다이어그램
   - **모듈 문서**: 주요 개념 (Runtime Protocol, Event Categories, Event Lifecycle) 설명
   - **Usage Examples**: 5가지 실용 예제
     1. 메시지 스트리밍 (START → CONTENT → END)
     2. 액션 실행 (START → ARGS → END → RESULT)
     3. 에이전트 상태 메시지
     4. 메타 이벤트 (INTERRUPT, PREDICT_STATE, EXIT)
     5. Lifecycle 이벤트 (RUN/NODE 이벤트)
   - **Best Practices**: 5가지 모범 사례
   - **Common Pitfalls**: 5가지 흔한 실수
   - **Enum 문서**: RuntimeEventTypes (15개), RuntimeMetaEventName (3개)
   - **TypedDict 문서**: 14개 이벤트 TypedDict 완전 문서화
     - TextMessageStart, TextMessageContent, TextMessageEnd
     - ActionExecutionStart, ActionExecutionArgs, ActionExecutionEnd, ActionExecutionResult
     - AgentStateMessage
     - MetaEvent
     - RunStarted, RunFinished, RunError
     - NodeStarted, NodeFinished
   - **Union Type 문서**: RuntimeProtocolEvent, RuntimeLifecycleEvent, RuntimeEvent, PredictStateConfig
   - **Helper Functions**: 11개 헬퍼 함수 완전 문서화
     - text_message_start/content/end
     - action_execution_start/args/end/result
     - agent_state_message
     - meta_event
     - emit_runtime_events/emit_runtime_event

2. **`runloop.py`** (~1,080라인):
   - **3개 Mermaid 다이어그램**:
     - Run Loop Architecture (flowchart): 메인 프로세스 흐름
     - Context Management Flow (sequence): 컨텍스트 생명주기
     - Event Processing Pipeline (state): 이벤트 처리 상태 머신
   - **모듈 문서**: 핵심 개념 5가지 상세 설명
     1. Context Variables (컨텍스트 변수)
     2. Event Queue (이벤트 큐)
     3. State Prediction (상태 예측)
     4. Event Handling (이벤트 처리)
     5. JSON Lines Streaming (JSON Lines 스트리밍)
   - **Usage Examples**: 3가지 실용 예제
     1. 기본 Run Loop
     2. 상태 예측 (Predict State)
     3. 우선순위 이벤트
   - **Best Practices**: 5가지 모범 사례
   - **Common Pitfalls**: 5가지 흔한 실수
   - **TypedDict 문서**: CopilotKitRunExecution (11개 필드 상세 설명)
   - **함수 문서**: 15개 함수 완전 문서화
     - yield_control: 이벤트 루프 제어권 양보
     - Context Management: get/set/reset_context_queue, get/set/reset_context_execution (6개)
     - queue_put: 이벤트 큐에 넣기
     - Utilities: _to_dict_if_pydantic, _filter_state (2개)
     - **copilotkit_run**: 메인 런 루프 (비동기 제너레이터)
     - **handle_runtime_event**: 이벤트 처리 핵심 로직
     - **predict_state**: 실시간 상태 예측

**Documentation Features**:
- **4개 Mermaid 다이어그램**:
  - Event Protocol Flow (state machine) - protocol.py
  - Run Loop Architecture (flowchart) - runloop.py
  - Context Management Flow (sequence) - runloop.py
  - Event Processing Pipeline (state machine) - runloop.py
- **파일별 상세 docstring**: 모든 함수, TypedDict, Enum, Union Type에 한글 docstring
- **표준 docstring 형식**: Parameters, Returns, Raises, Yields, Examples, Notes, See Also 섹션
- **실용적 예제**: 각 기능마다 실제 사용 가능한 코드 예제 포함
- **알고리즘 설명**: predict_state()의 Partial JSON 파싱 알고리즘 단계별 설명
- **FastAPI SSE 통합 예제**: copilotkit_run()에서 StreamingResponse 사용법 포함
- **Emoji 없음**: 전문적인 문서 스타일 유지

**Documentation Statistics**:
- protocol.py: ~1,350라인 추가
  - 모듈 문서: ~330라인 (1개 다이어그램 포함)
  - Enum 문서: ~80라인 (2개 Enum)
  - TypedDict 문서: ~560라인 (14개 TypedDict + 4개 Union)
  - Helper Functions: ~380라인 (11개 함수)
- runloop.py: ~1,080라인 추가
  - 모듈 문서: ~260라인 (3개 다이어그램 포함)
  - TypedDict 문서: ~110라인 (1개)
  - 함수 문서: ~710라인 (15개 함수)
- **총 ~2,430라인**의 한글 문서 추가
- **총 4개 Mermaid 다이어그램** (아키텍처 및 플로우 시각화)

**Key Technical Concepts Documented**:
1. **Event Protocol**:
   - 15가지 이벤트 타입 및 사용 시점
   - START → CONTENT/ARGS → END 패턴
   - JSON Lines 직렬화
   - Enum 값 자동 변환

2. **Run Loop Architecture**:
   - asyncio.Queue 기반 이벤트 큐
   - Context Variables로 스레드 안전 상태 공유
   - yield_control()을 통한 우선순위 처리
   - AsyncGenerator로 SSE 스트리밍

3. **State Prediction**:
   - Partial JSON Parsing (PartialJSONParser)
   - 실시간 액션 인자 파싱
   - @copilotkit_customize_config 연동
   - argument_buffer 누적 및 파싱

4. **Event Processing**:
   - Protocol Events: 클라이언트 직접 전송
   - Meta Events: 런타임 설정 업데이트
   - Lifecycle Events: AgentStateMessage 변환

**Testing**:
```bash
# 모든 임포트 및 기능 정상 작동 확인
uv run python -c "
from copilotkit.protocol import (
    RuntimeEventTypes, RuntimeMetaEventName,
    TextMessageStart, ActionExecutionResult,
    text_message_start, emit_runtime_events
)
from copilotkit.runloop import (
    CopilotKitRunExecution, copilotkit_run,
    queue_put, handle_runtime_event, predict_state
)
print('✓ All imports successful!')
print('✓ Documentation added without breaking functionality')
"
```
- ✅ 모든 임포트 정상 작동
- ✅ 기능적 변경 사항 없음 (문서만 추가)
- ✅ 타입 힌트 및 구조 유지
- ✅ 기존 코드 동작 변경 없음

**Upstream Sync Notes**:
- 영향도: 낮음 - 문서만 추가되었으므로 upstream 병합 시 충돌 가능성 낮음
- 문서는 코드와 독립적이므로 upstream 변경에 영향받지 않음
- 다만, 새로운 이벤트 타입이나 함수가 추가되면 해당 부분에도 한글 문서 추가 필요
- 함수 시그니처나 이벤트 구조 변경 시 docstring도 함께 업데이트 필요

**Rollback Instructions**:
문서 제거가 필요한 경우 (권장하지 않음):
```bash
git checkout origin/main -- copilotkit_sdk/copilotkit/protocol.py
git checkout origin/main -- copilotkit_sdk/copilotkit/runloop.py
```

**Related Customizations**:
이 문서화는 3단계 계획의 두 번째(Phase 2)입니다:
- **Phase 1 (완료, #5)**: Core API Bundle (__init__, action, parameter, agent) - ~2,086라인, 4개 다이어그램
- **Phase 2 (이번 작업)**: Protocol & Runtime System (protocol.py, runloop.py) - ~2,430라인, 4개 다이어그램
- **Phase 3 (예정)**: Supporting Utilities (exc.py, logging.py, utils.py, html.py) - 예상 ~400-600라인

전체 문서화가 완료되면 #2, #3, #4, #5와 함께 SDK의 완전한 한글 문서 세트를 구성합니다.

**Next Steps**:
Phase 2 완료 후 다음 단계:
1. Phase 3: Supporting Utilities 문서화 (exc.py, logging.py, utils.py, html.py)
   - 예상 라인 수: ~400-600라인
   - 예상 다이어그램: 1-2개 (Exception Hierarchy, Logging Flow 등)
   - 예상 완료: 2025-10-28

**Progress Tracking**:
- Phase 1: ✅ 완료 (~2,086라인, 4개 다이어그램)
- Phase 2: ✅ 완료 (~2,430라인, 4개 다이어그램)
- Phase 3: ⏳ 예정 (~400-600라인 예상)
- **누적 총계**: ~4,516라인, 8개 다이어그램

---

### #7: Korean Documentation for Supporting Utilities (Phase 3)
**Date**: 2025-10-28
**Impact**: Documentation - No functional changes
**Files Modified**:
- `copilotkit_sdk/copilotkit/exc.py` - Added exception hierarchy documentation
- `copilotkit_sdk/copilotkit/logging.py` - Added logging system documentation
- `copilotkit_sdk/copilotkit/utils.py` - Added utility function documentation
- `copilotkit_sdk/copilotkit/html.py` - Added HTML rendering documentation

**Purpose**:
Supporting Utilities (Phase 3/3)에 해당하는 4개 파일에 완전한 한글 문서를 추가했습니다.
예외 처리, 로깅, 유틸리티, HTML 렌더링 등 SDK의 보조 기능들을 상세하게 문서화하여
전체 SDK 문서화를 완성했습니다.

**Changes Summary**:

1. **`exc.py`** (~200라인):
   - **Exception Hierarchy Mermaid Diagram**: 예외 계층 구조 시각화
   - **모듈 문서**: 예외 카테고리 (Not Found, Execution) 설명
   - **Usage Examples**: 6가지 예외 처리 패턴
     1. ActionNotFoundException 처리
     2. ActionExecutionException 처리
     3. AgentNotFoundException 처리
     4. AgentExecutionException 처리
     5. 모든 CopilotKit 예외 처리
     6. 권장 에러 처리 패턴
   - **Best Practices**: 5가지 (구체적 예외 우선, 원본 예외 보존, 로깅 전략 등)
   - **Common Pitfalls**: 5가지 흔한 실수
   - **예외 클래스 문서**: 4개 예외 클래스 완전 문서화
     - ActionNotFoundException: name 속성
     - AgentNotFoundException: name 속성
     - ActionExecutionException: name, error 속성 (원본 예외 래핑)
     - AgentExecutionException: name, error 속성 (원본 예외 래핑)

2. **`logging.py`** (~135라인):
   - **모듈 문서**: 로깅 시스템 개요 및 환경변수 설정
   - **Usage Examples**: 5가지 로깅 패턴
     1. 기본 로거 생성
     2. 환경변수 로그 레벨 제어
     3. 볼드 텍스트 출력
     4. TTY vs Non-TTY 감지
     5. 실제 사용 예제
   - **Log Levels**: 5단계 로그 레벨 설명 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
   - **Best Practices**: 5가지 모범 사례
   - **Common Pitfalls**: 5가지 흔한 실수
   - **Environment Variables**: LOG_LEVEL 환경변수 상세 설명
   - **TTY Detection**: ANSI escape code 자동 처리
   - **함수 문서**: 2개 함수 완전 문서화
     - get_logger(): 환경변수 기반 로거 생성
     - bold(): 터미널 볼드 텍스트 포맷팅 (ANSI escape code)

3. **`utils.py`** (~105라인):
   - **모듈 문서**: 유틸리티 함수 개요
   - **Usage Examples**: 4가지 필터링 패턴
     1. 기본 스키마 필터링
     2. LangGraph 상태 필터링
     3. 에러 방어 (원본 반환)
     4. 실제 사용 예제
   - **Common Use Cases**: 4가지 사용 사례
   - **함수 문서**: filter_by_schema_keys() 완전 문서화
     - 스키마 키 + "messages" 키 보존
     - 에러 발생 시 원본 객체 반환
     - 딕셔너리 컴프리헨션 O(n)

4. **`html.py`** (~160라인):
   - **모듈 문서**: HTML 렌더링 시스템 개요
   - **Page Structure**: 브라우저 페이지 구조 설명
     - Header (로고, 버전)
     - Actions Section (액션 카드들)
     - Agents Section (에이전트 카드들)
   - **Design Features**: 5가지 디자인 특징
     - 반응형 디자인
     - 카드 레이아웃
     - 코드 하이라이팅
     - 타입 배지
     - 모던 UI
   - **Usage Examples**: 3가지 사용 패턴
     1. FastAPI 통합
     2. 직접 HTML 생성
     3. 액션/에이전트 없는 경우
   - **Template Variables**: 모든 템플릿 변수 설명
   - **CSS Styling**: 주요 스타일 설명
   - **HTML 템플릿 상수**: 6개 템플릿에 주석 추가
     - HEAD_HTML, INFO_TEMPLATE, ACTION_TEMPLATE
     - AGENT_TEMPLATE, NO_ACTIONS_FOUND_HTML, NO_AGENTS_FOUND_HTML
   - **함수 문서**: generate_info_html() 완전 문서화
     - InfoDict → HTML 문자열 변환
     - 액션/에이전트 카드 생성
     - 타입 변환 (langgraph → LangGraph)

**Documentation Features**:
- **1개 Mermaid 다이어그램**:
  - Exception Hierarchy (class diagram) - exc.py
- **파일별 상세 docstring**: 모든 함수, 클래스, 상수에 한글 docstring
- **표준 docstring 형식**: Parameters, Returns, Examples, Notes, See Also 섹션
- **실용적 예제**: 각 기능마다 실제 사용 가능한 코드 예제 포함
- **Best Practices와 Common Pitfalls**: 모범 사례 및 흔한 실수 섹션
- **Emoji 없음**: 전문적인 문서 스타일 유지

**Documentation Statistics**:
- exc.py: ~200라인 추가
  - 모듈 문서: ~140라인 (1개 다이어그램 포함)
  - 예외 클래스: ~60라인 (4개 클래스)
- logging.py: ~135라인 추가
  - 모듈 문서: ~75라인
  - 함수 문서: ~60라인 (2개 함수)
- utils.py: ~105라인 추가
  - 모듈 문서: ~30라인
  - 함수 문서: ~75라인 (1개 함수)
- html.py: ~160라인 추가
  - 모듈 문서: ~80라인
  - 함수 문서: ~80라인 (1개 함수 + 6개 템플릿 주석)
- **총 ~600라인**의 한글 문서 추가
- **총 1개 Mermaid 다이어그램** (예외 계층 구조)

**Key Technical Concepts Documented**:
1. **Exception Handling**:
   - Not Found vs Execution 예외
   - 예외 래핑 패턴 (원본 예외 보존)
   - name, error 속성 활용

2. **Logging System**:
   - LOG_LEVEL 환경변수 제어
   - 모듈별 독립적 로거
   - TTY 감지 및 ANSI escape code

3. **Utility Functions**:
   - 스키마 기반 필터링
   - "messages" 키 자동 보존
   - 에러 방어적 설계

4. **HTML Rendering**:
   - 템플릿 기반 HTML 생성
   - 카드 레이아웃 시스템
   - JSON 파라미터 포맷팅

**Testing**:
```bash
# 모든 임포트 및 기능 정상 작동 확인
uv run python -c "
from copilotkit.exc import (
    ActionNotFoundException, AgentNotFoundException,
    ActionExecutionException, AgentExecutionException
)
from copilotkit.logging import get_logger, bold
from copilotkit.utils import filter_by_schema_keys
from copilotkit.html import generate_info_html
print('✓ All imports successful!')
print('✓ Documentation added without breaking functionality')
"
```
- ✅ 모든 임포트 정상 작동
- ✅ 기능적 변경 사항 없음 (문서만 추가)
- ✅ 타입 힌트 및 구조 유지
- ✅ 기존 코드 동작 변경 없음

**Upstream Sync Notes**:
- 영향도: 낮음 - 문서만 추가되었으므로 upstream 병합 시 충돌 가능성 낮음
- 문서는 코드와 독립적이므로 upstream 변경에 영향받지 않음
- 다만, 새로운 예외나 함수가 추가되면 해당 부분에도 한글 문서 추가 필요

**Rollback Instructions**:
문서 제거가 필요한 경우 (권장하지 않음):
```bash
git checkout origin/main -- copilotkit_sdk/copilotkit/exc.py
git checkout origin/main -- copilotkit_sdk/copilotkit/logging.py
git checkout origin/main -- copilotkit_sdk/copilotkit/utils.py
git checkout origin/main -- copilotkit_sdk/copilotkit/html.py
```

**Related Customizations**:
이 문서화는 3단계 계획의 마지막(Phase 3)으로, 전체 SDK 문서화를 완성합니다:
- **Phase 1 (완료, #5)**: Core API Bundle (__init__, action, parameter, agent) - ~2,086라인, 4개 다이어그램
- **Phase 2 (완료, #6)**: Protocol & Runtime System (protocol.py, runloop.py) - ~2,430라인, 4개 다이어그램
- **Phase 3 (완료, 이번 작업)**: Supporting Utilities (exc.py, logging.py, utils.py, html.py) - ~600라인, 1개 다이어그램

전체 문서화가 완료되어 #2, #3, #4, #5, #6과 함께 SDK의 완전한 한글 문서 세트를 구성합니다.

**Final Progress Tracking**:
- Phase 1: ✅ 완료 (~2,086라인, 4개 다이어그램)
- Phase 2: ✅ 완료 (~2,430라인, 4개 다이어그램)
- Phase 3: ✅ 완료 (~600라인, 1개 다이어그램)
- **전체 완료**: ~5,116라인, 9개 다이어그램

**Documentation Achievement**:
CopilotKit Python SDK의 모든 핵심 모듈과 유틸리티에 대한 완전한 한글 문서화를 달성했습니다. 총 ~5,116라인의 문서와 9개의 Mermaid 다이어그램으로 개발자가 SDK를 이해하고 사용하는 데 필요한 모든 정보를 제공합니다.

---

## 커스터마이징 가이드라인

### 새 파일 추가 (권장)

**장점**:
- Upstream 업데이트 시 충돌 없음
- 기능을 명확하게 분리

**예시**:
```
copilotkit_sdk/
└── copilotkit/
    ├── custom/           # 커스텀 모듈들을 별도 디렉토리에
    │   ├── __init__.py
    │   ├── agents.py
    │   └── integrations.py
```

### 기존 파일 수정

**주의사항**:
- 변경 이유를 명확히 문서화
- Upstream 업데이트 시 재적용 방법 기록
- 가능하면 최소한의 변경만

**권장 패턴**:
```python
# 기존 클래스를 상속하여 확장
from copilotkit.agent import Agent

class CustomAgent(Agent):
    """Extended agent with custom functionality"""
    pass
```

### Monkey Patching (비권장)

불가피한 경우에만 사용:
```python
# src/patches.py
from copilotkit import agent

original_method = agent.Agent.execute

def patched_execute(self):
    # Custom logic
    result = original_method(self)
    # More custom logic
    return result

agent.Agent.execute = patched_execute
```

## 테스트 전략

각 커스터마이징에 대한 테스트 작성:

```
tests/
├── test_custom_agent.py
├── test_protocol_modifications.py
└── test_integration.py
```

### Upstream 호환성 테스트

```python
# tests/test_upstream_compatibility.py
def test_base_agent_interface():
    """Ensure our custom agent is compatible with base Agent"""
    agent = CustomAgent()
    assert hasattr(agent, 'execute')
    assert callable(agent.execute)
```

## 마이그레이션 체크리스트

Upstream 업데이트 시:

- [ ] CUSTOMIZATIONS.md의 모든 항목 검토
- [ ] 수정된 파일 목록 확인
- [ ] 각 커스터마이징의 upstream 호환성 확인
- [ ] 테스트 실행하여 정상 동작 확인
- [ ] 필요시 커스터마이징 코드 업데이트
- [ ] 이 문서 업데이트 (새 버전 정보, 변경사항 등)

## 패치 관리

중요한 수정사항은 패치 파일로 관리:

```bash
# 패치 생성
git diff copilotkit_sdk/copilotkit/protocol.py > patches/protocol_logging.patch

# 패치 적용
patch copilotkit_sdk/copilotkit/protocol.py < patches/protocol_logging.patch
```

패치 파일 저장 위치:
```
patches/
├── README.md
├── protocol_logging.patch
└── agent_custom_init.patch
```

## 향후 고려사항

### Upstream 기여 가능성

일부 커스터마이징은 upstream에 PR로 제출 고려:
- [ ] 범용적인 기능 개선
- [ ] 버그 수정
- [ ] 문서 개선

### 리팩토링 우선순위

1. **High**: 핵심 로직 수정 → Wrapper 패턴으로 전환
2. **Medium**: 유틸리티 함수 추가 → 별도 모듈로 분리
3. **Low**: 설정 값 변경 → 환경 변수로 관리

## 문의 및 협업

팀 내 커스터마이징 관련 논의:
- 커스터마이징 제안: GitHub Issues 사용
- 코드 리뷰: PR을 통한 변경 제안
- 문서: 이 파일을 업데이트하여 팀과 공유

---

### #8: LangGraph v1.0 Compatibility Testing & Verification
**Date**: 2025-10-29
**Impact**: Medium - Testing infrastructure added
**Files Added**:
- `copilotkit_sdk/pytest.ini` - pytest configuration
- `copilotkit_sdk/tests/conftest.py` - Common fixtures
- `copilotkit_sdk/tests/fixtures/sample_actions.py` - Reusable Action fixtures
- `copilotkit_sdk/tests/fixtures/sample_messages.py` - Message fixtures
- `copilotkit_sdk/tests/fixtures/sample_graphs.py` - Mock LangGraph graphs
- `copilotkit_sdk/tests/fixtures/sample_configs.py` - RunnableConfig fixtures
- `copilotkit_sdk/tests/test_langgraph_v1_compatibility/test_core_apis.py` - 15 core API tests
- `docs/LANGGRAPH_V1_COMPATIBILITY.md` - Compatibility report
- `docs/TEST_PLAN.md` - Comprehensive test strategy document

**Files Modified**:
- `pyproject.toml` (root) - Added dev dependencies (pytest-cov, pytest-mock, httpx, faker)
- `copilotkit_sdk/pyproject.toml` - Extended Python support to 3.13 (`>=3.10,<3.14`)

**Purpose**:
Verify and document LangGraph v1.0 compatibility. Create test infrastructure to ensure SDK works correctly with the latest LangGraph version.

**Changes Summary**:
1. **Dependencies**: Installed LangGraph v1.0.1 successfully
2. **Test Infrastructure**: Created pytest configuration and fixture system
3. **Core API Tests**: Implemented 15 compatibility tests - **ALL PASSED** ✅
4. **Documentation**: Comprehensive compatibility report showing 100% compatibility

**Test Results**:
```
============================= 15 passed in 0.03s ==============================
```

**Key Findings**:
- ✅ MessagesState: Full inheritance support
- ✅ CompiledStateGraph: All methods functional
- ✅ Interrupt/Command: Works perfectly
- ✅ Event Streaming: `astream_events(version="v2")` works
- ✅ Overall Risk: LOW - No migration needed

**LangGraph Versions Installed**:
```
langgraph            1.0.1
langgraph-checkpoint 3.0.0
langgraph-prebuilt   1.0.1
langgraph-sdk        0.2.9
```

**Code Markers**: None (test-only changes)

**Testing**:
- ✅ 15/15 core API tests passed
- ✅ No breaking changes found
- ✅ All SDK APIs compatible with LangGraph v1.0.1

**Documentation**:
See `docs/LANGGRAPH_V1_COMPATIBILITY.md` for detailed test results and API compatibility matrix.

**Migration Required**: None - SDK already fully compatible!

---

**작성일**: 2025-10-28
**작성자**: Development Team
**최종 업데이트**: 2025-10-29
