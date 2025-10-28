# Custom CopilotKit Python SDK

CopilotKit Python SDK를 기반으로 한 커스텀 버전입니다. LangGraph v1.0 완전 호환 및 한글 문서화가 완료되었습니다.

[![LangGraph v1.0.1](https://img.shields.io/badge/LangGraph-v1.0.1-blue)](https://github.com/langchain-ai/langgraph)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-15%2F15%20passing-brightgreen)](./copilotkit_sdk/tests/)

## 프로젝트 개요

이 프로젝트는 CopilotKit 공식 Python SDK를 기반으로 다음과 같은 커스터마이징을 적용했습니다:

- **LangGraph v1.0.1 완전 호환 검증** (15개 테스트 100% 통과)
- **전체 코드베이스 한글 문서화** (~5,116 lines, 9 Mermaid diagrams)
- **포괄적 테스트 인프라 구축** (pytest, fixtures, 146개 테스트 케이스 계획)
- **CrewAI 지원 제거** (LangGraph 전용)
- **Python 3.13 지원**

## 주요 특징

### 1. LangGraph v1.0 완전 호환

```bash
# 호환성 테스트 실행
uv run pytest copilotkit_sdk/tests/test_langgraph_v1_compatibility/ -v

# 결과: 15/15 tests passed in 0.03s
```

**검증된 API**:
- MessagesState (상태 관리)
- CompiledStateGraph (그래프 실행)
- interrupt() / Command (인터럽트 처리)
- astream_events(version="v2") (이벤트 스트리밍)

자세한 내용: [`docs/LANGGRAPH_V1_COMPATIBILITY.md`](./docs/LANGGRAPH_V1_COMPATIBILITY.md)

### 2. 완전한 한글 문서화

**Phase 1**: Core API Bundle (4 files, ~2,086 lines, 4 diagrams)
- `sdk.py`, `action.py`, `parameter.py`, `agent.py`

**Phase 2**: Protocol & Runtime (2 files, ~2,430 lines, 4 diagrams)
- `protocol.py`, `runloop.py`

**Phase 3**: Supporting Utilities (4 files, ~600 lines, 1 diagram)
- `exc.py`, `logging.py`, `utils.py`, `html.py`

모든 모듈이 다음을 포함합니다:
- 상세한 사용 예시 (docstring examples)
- Mermaid 다이어그램 (아키텍처, 흐름도, 상태 머신)
- Best Practices 및 Common Pitfalls
- See Also 참조 링크

### 3. 테스트 인프라

```
copilotkit_sdk/tests/
├── conftest.py                      # 공통 fixtures
├── fixtures/                        # 재사용 가능한 테스트 데이터
│   ├── sample_actions.py
│   ├── sample_messages.py
│   ├── sample_graphs.py
│   └── sample_configs.py
└── test_langgraph_v1_compatibility/ # LangGraph v1.0 호환성 테스트
    └── test_core_apis.py            # 15 tests
```

테스트 계획: [`docs/TEST_PLAN.md`](./docs/TEST_PLAN.md) (146 test cases)

## 설치 및 사용

### 요구사항

- **Python**: 3.10 이상 (3.13 지원)
- **패키지 매니저**: [uv](https://github.com/astral-sh/uv)

### 설치

```bash
# 저장소 클론
git clone https://github.com/HyunjunJeon/custom-copilotkit-python-sdk.git
cd custom-copilotkit-python-sdk

# 의존성 설치
uv sync

# LangGraph 버전 확인
uv pip list | grep langgraph
```

예상 출력:
```
langgraph            1.0.1
langgraph-checkpoint 3.0.0
langgraph-prebuilt   1.0.1
```

### 기본 사용법

```python
from copilotkit import CopilotKitSDK, Action, LangGraphAgent

# 액션 정의
def search_handler(query: str):
    return {"results": [f"Result for {query}"]}

action = Action(
    name="search",
    description="Search the database",
    parameters=[...],
    handler=search_handler
)

# SDK 초기화
sdk = CopilotKitSDK(actions=[action])

# FastAPI 통합
from fastapi import FastAPI
from copilotkit.integrations.fastapi import add_fastapi_endpoint

app = FastAPI()
add_fastapi_endpoint(app, sdk, "/copilotkit")
```

## 테스트 실행

### 전체 테스트

```bash
uv run pytest copilotkit_sdk/tests/ -v
```

### 호환성 테스트만

```bash
uv run pytest copilotkit_sdk/tests/test_langgraph_v1_compatibility/ -v
```

### 커버리지 측정

```bash
uv run pytest copilotkit_sdk/tests/ \
    --cov=copilotkit \
    --cov-report=html \
    --cov-report=term-missing

# HTML 리포트 확인
open copilotkit_sdk/htmlcov/index.html
```

## 프로젝트 구조

```
.
├── README.md                        # 이 파일
├── pyproject.toml                   # 프로젝트 설정
├── copilotkit_sdk/                  # 커스텀 CopilotKit SDK
│   ├── copilotkit/                  # SDK 소스 코드
│   │   ├── __init__.py
│   │   ├── sdk.py                   # 메인 SDK 클래스
│   │   ├── action.py                # Action 정의
│   │   ├── parameter.py             # Parameter 정의
│   │   ├── agent.py                 # Agent 추상 클래스
│   │   ├── protocol.py              # 프로토콜 이벤트 타입
│   │   ├── runloop.py               # 런타임 실행 루프
│   │   ├── exc.py                   # 예외 클래스
│   │   ├── logging.py               # 로깅 유틸리티
│   │   ├── utils.py                 # 유틸리티 함수
│   │   ├── html.py                  # HTML 렌더링
│   │   ├── langgraph.py             # LangGraph 통합 (핵심)
│   │   ├── langgraph_agent.py       # LangGraph Agent 래퍼
│   │   └── integrations/
│   │       └── fastapi.py           # FastAPI 통합
│   ├── tests/                       # 테스트 코드
│   │   ├── conftest.py
│   │   ├── fixtures/
│   │   └── test_langgraph_v1_compatibility/
│   └── pyproject.toml               # SDK 의존성
│
└── docs/                            # 문서
    ├── CUSTOMIZATIONS.md            # 커스터마이징 내역 (#1-#8)
    ├── TEST_PLAN.md                 # 테스트 전략 문서
    ├── LANGGRAPH_V1_COMPATIBILITY.md # 호환성 보고서
    ├── CODE_NAVIGATION.md           # 코드 탐색 가이드
    └── UPSTREAM_SYNC.md             # Upstream 동기화 가이드
```

## 커스터마이징 내역

전체 커스터마이징 내역은 [`docs/CUSTOMIZATIONS.md`](./docs/CUSTOMIZATIONS.md)를 참조하세요.

### 주요 변경사항

| # | 변경 내용 | 날짜 | 영향도 |
|---|---------|------|--------|
| #1 | CrewAI 지원 제거 (LangGraph 전용) | 2025-10-28 | Major |
| #2-#7 | 전체 코드베이스 한글 문서화 | 2025-10-28 | Major |
| #8 | LangGraph v1.0 호환성 테스팅 | 2025-10-29 | Medium |

## 문서

### 핵심 문서

- [**테스트 계획**](./docs/TEST_PLAN.md) - 포괄적 테스트 전략 (146 test cases)
- [**LangGraph v1.0 호환성**](./docs/LANGGRAPH_V1_COMPATIBILITY.md) - 호환성 검증 보고서
- [**커스터마이징 내역**](./docs/CUSTOMIZATIONS.md) - 모든 변경사항 추적
- [**코드 탐색 가이드**](./docs/CODE_NAVIGATION.md) - 코드베이스 네비게이션

### 코드 내 문서

모든 Python 모듈이 상세한 docstring을 포함합니다:

```python
# 예시: copilotkit/sdk.py
"""
CopilotKit SDK - 메인 엔트리포인트

이 모듈은 CopilotKit Python SDK의 핵심 클래스를 제공합니다.
액션과 에이전트를 등록하고, 실행하고, 정보를 조회하는 통합 인터페이스입니다.

Usage Examples
--------------
>>> from copilotkit import CopilotKitSDK, Action
>>> sdk = CopilotKitSDK()
>>> ...
"""
```

## 개발 가이드

### 새로운 테스트 추가

1. `copilotkit_sdk/tests/fixtures/`에 필요한 fixture 추가
2. 적절한 테스트 디렉토리에 테스트 파일 작성
3. `conftest.py`에 공통 fixture 추가 (필요 시)
4. pytest 실행 및 검증

```bash
# 새 테스트 작성 후
uv run pytest copilotkit_sdk/tests/your_new_test.py -v
```

### 코드 스타일

- **Docstring**: NumPy/Google style
- **언어**: 한글 (코드 주석 및 docstring)
- **타입 힌팅**: TypedDict, Annotated 사용
- **Diagram**: Mermaid 사용 (flowchart, state diagram, sequence diagram)

## Upstream 동기화

공식 CopilotKit 저장소의 업데이트를 받으려면:

```bash
# 1. Upstream 추가 (한 번만)
git remote add upstream https://github.com/CopilotKit/CopilotKit.git

# 2. Upstream 변경사항 확인
git fetch upstream

# 3. 변경사항 머지
git merge upstream/main

# 4. 충돌 해결 (필요 시)
# docs/CUSTOMIZATIONS.md를 참고하여 커스텀 변경사항 보존
```

자세한 내용: [`docs/UPSTREAM_SYNC.md`](./docs/UPSTREAM_SYNC.md)

## 버전 정보

- **Base Version**: CopilotKit v0.1.70
- **LangGraph**: v1.0.1
- **LangChain**: v0.3.28
- **Python**: 3.10+ (3.13 지원)

## 라이선스

MIT License (CopilotKit 공식 SDK와 동일)

## 기여

이 프로젝트는 CopilotKit 공식 SDK의 커스텀 포크입니다.

### 기여 방법

1. 이슈 생성 (버그 리포트, 기능 제안)
2. 브랜치 생성 (`git checkout -b feature/amazing-feature`)
3. 변경사항 커밋 (`git commit -m 'feat: Add amazing feature'`)
4. 브랜치 푸시 (`git push origin feature/amazing-feature`)
5. Pull Request 생성

### 커스터마이징 추가 시

새로운 커스터마이징을 추가할 때는 반드시:
1. `docs/CUSTOMIZATIONS.md`에 기록
2. 코드에 `# CUSTOMIZATION:` 마커 추가
3. 영향받는 파일 목록 작성
4. 테스트 추가 (가능한 경우)

## 참고 링크

- [CopilotKit 공식 문서](https://docs.copilotkit.ai/)
- [CopilotKit GitHub](https://github.com/CopilotKit/CopilotKit)
- [LangGraph 문서](https://langchain-ai.github.io/langgraph/)
- [LangChain 문서](https://python.langchain.com/)

## 문의

프로젝트 관련 문의나 이슈는 GitHub Issues를 통해 제출해주세요.

---

**Last Updated**: 2025-10-29
**Status**: Production-ready with LangGraph v1.0.1
