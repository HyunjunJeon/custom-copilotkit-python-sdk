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
