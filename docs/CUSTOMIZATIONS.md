# Customizations Log

이 문서는 CopilotKit Python SDK에 적용한 커스터마이징 내역을 기록합니다.

## 목적

Upstream 업데이트 시 커스터마이징한 부분을 보존하고 충돌을 피하기 위해 모든 변경사항을 추적합니다.

## 버전 정보

- **Base Version**: v0.1.70 (2025-10-28)
- **Upstream**: https://github.com/CopilotKit/CopilotKit/tree/main/sdk-python
- **Last Sync**: 2025-10-28

## 커스터마이징 내역

> 아래에 각 커스터마이징 항목을 추가하세요.

---

### 예시: Custom Agent Implementation
**Date**: 2025-10-28
**Files Modified**:
- `copilotkit_sdk/copilotkit/custom_agent.py` (new file)

**Purpose**: 특정 비즈니스 로직을 처리하는 커스텀 에이전트 추가

**Changes**:
```python
# Added new CustomAgent class
class CustomAgent(Agent):
    def __init__(self, custom_param: str):
        super().__init__()
        self.custom_param = custom_param

    def execute(self):
        # Custom logic here
        pass
```

**Upstream Sync Notes**:
- 이 파일은 새로 추가된 것이므로 upstream 업데이트 시 영향 없음
- 단, `Agent` base class가 변경되면 호환성 검토 필요

---

### 예시: Modified Protocol Handler
**Date**: 2025-10-28
**Files Modified**:
- `copilotkit_sdk/copilotkit/protocol.py`

**Purpose**: 프로토콜 핸들링에 추가 로깅 기능 추가

**Changes**:
```diff
# Line 45-50
def handle_message(self, message):
+   logger.debug(f"Handling message: {message}")
    # existing code...
```

**Upstream Sync Notes**:
- ⚠️ Upstream에서 `protocol.py`가 변경되면 충돌 가능성 높음
- 업데이트 시 로깅 코드를 다시 적용해야 함
- 향후 고려사항: 로깅을 별도 wrapper로 분리 검토

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
