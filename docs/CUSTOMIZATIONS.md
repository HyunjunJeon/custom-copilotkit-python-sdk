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

**작성일**: 2025-10-28
**작성자**: Development Team
**최종 업데이트**: 2025-10-28
