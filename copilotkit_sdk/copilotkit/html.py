"""
CopilotKit HTML 렌더링 - 브라우저 친화적 Info 페이지

이 모듈은 CopilotKit SDK의 /info 엔드포인트를 브라우저에서 접근했을 때
보여줄 HTML 페이지를 생성합니다. 등록된 액션과 에이전트의 정보를
사용자 친화적인 형식으로 표시합니다.

Core Components
---------------

**HTML Templates**:
- HEAD_HTML: 공통 헤더 (CSS 스타일 포함)
- INFO_TEMPLATE: 메인 페이지 템플릿
- ACTION_TEMPLATE: 개별 액션 카드 템플릿
- AGENT_TEMPLATE: 개별 에이전트 카드 템플릿
- NO_ACTIONS_FOUND_HTML: 액션 없을 때 메시지
- NO_AGENTS_FOUND_HTML: 에이전트 없을 때 메시지

**Generation Function**:
- generate_info_html(): InfoDict를 받아 HTML 문자열 생성

Page Structure
--------------

브라우저로 /info 접근 시 표시되는 페이지:

1. **Header**:
   - CopilotKit 로고 (🪁)
   - SDK 버전 표시

2. **Actions Section**:
   - 등록된 액션 목록
   - 각 액션: 이름, 설명, 파라미터 (JSON 형식)

3. **Agents Section**:
   - 등록된 에이전트 목록
   - 각 에이전트: 이름, 타입 배지, 설명

Design Features
---------------

- **반응형 디자인**: 다양한 화면 크기 지원
- **카드 레이아웃**: 깔끔한 그리드 시스템
- **코드 하이라이팅**: 파라미터 JSON 표시
- **타입 배지**: 에이전트 타입 (LangGraph) 표시
- **깔끔한 스타일**: 모던한 UI (Arial, 그림자 효과 등)

Usage Examples
--------------

FastAPI 통합:

>>> from fastapi import FastAPI
>>> from copilotkit import CopilotKitSDK
>>> from copilotkit.html import generate_info_html
>>>
>>> app = FastAPI()
>>> sdk = CopilotKitSDK()
>>>
>>> @app.get("/info", response_class=HTMLResponse)
>>> async def info():
...     info_dict = sdk.info()
...     return generate_info_html(info_dict)

브라우저 접근:
```
GET http://localhost:8000/info
→ 등록된 액션/에이전트 정보가 HTML로 표시됨
```

직접 HTML 생성:

>>> from copilotkit.html import generate_info_html
>>> info = {
...     "sdkVersion": "0.1.12",
...     "actions": [
...         {
...             "name": "search_database",
...             "description": "Search the database",
...             "parameters": [{"name": "query", "type": "string"}]
...         }
...     ],
...     "agents": [
...         {
...             "name": "research_agent",
...             "description": "Research agent",
...             "type": "langgraph"
...         }
...     ]
... }
>>> html = generate_info_html(info)
>>> # html 변수에 완전한 HTML 문서 포함

Template Variables
------------------

**INFO_TEMPLATE** 변수:
- {head_html}: HEAD_HTML 삽입
- {version}: SDK 버전
- {action_html}: 액션 카드들
- {agent_html}: 에이전트 카드들

**ACTION_TEMPLATE** 변수:
- {name}: 액션 이름
- {description}: 액션 설명
- {arguments}: JSON 형식 파라미터

**AGENT_TEMPLATE** 변수:
- {name}: 에이전트 이름
- {type}: 에이전트 타입 (LangGraph)
- {description}: 에이전트 설명

CSS Styling
-----------

주요 스타일:
- **body**: 깔끔한 배경 (#f4f4f4), Arial 폰트
- **.container**: 중앙 정렬, 최대 800px
- **.card**: 흰 배경, 그림자 효과, 둥근 모서리
- **.badge**: 파란색 배지 (타입 표시)
- **pre/code**: 코드 블록 스타일 (JSON 파라미터)

Agent Type Mapping
------------------

- "langgraph" → "LangGraph" (대문자 표시)
- "crewai" → (비활성화됨, CUSTOMIZATION 참고)

Notes
-----
- HTML 페이지는 정적 (실시간 업데이트 없음)
- 페이지 새로고침으로 최신 정보 확인
- JSON API는 /info (Accept: application/json)로 별도 제공
- CrewAI 타입은 비활성화됨 (CUSTOMIZATION: CrewAI support disabled)

See Also
--------
sdk : CopilotKitSDK.info() 메서드
integrations.fastapi : FastAPI 통합 (info 엔드포인트)
"""
import json
from copilotkit.sdk import InfoDict

# HTML 템플릿: 공통 헤더 (CSS 스타일 포함)
HEAD_HTML = """
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CopilotKit Remote Endpoint v0.1.12</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f4f4f4;
            margin: 0;
            padding: 0;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 30px;
        }
        header {
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 40px;
        }
        h1 {
            font-size: 2rem;
            margin: 0;
        }
        h2 {
            font-size: 1.8rem;
            margin-bottom: 20px;
        }
        h3 {
            font-size: 1.4rem;
            margin-bottom: 10px;
        }
        .version {
          font-family: 'Courier New', Courier, monospace;
          font-size: 1.2rem;
        }
        .kite-icon {
            font-size: 38px;
            margin-right: 16px;
        }
        .grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 20px;
            margin-bottom: 40px;
        }
        .card {
            background-color: #fff;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            padding: 20px;
        }
        .badge {
            display: inline-block;
            padding: 4px 8px;
            font-size: 0.75rem;
            font-weight: bold;
            border-radius: 4px;
            margin-left: 10px;
            background-color: #dbeafe;
            color: #1e40af;
        }
        pre {
            background-color: #f1f1f1;
            padding: 10px;
            border-radius: 4px;
            overflow-x: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        code {
            font-family: 'Courier New', Courier, monospace;
        }
    </style>
</head>
"""

# HTML 템플릿: 메인 페이지 (헤더, Actions, Agents 섹션)
INFO_TEMPLATE= """
<!DOCTYPE html>
<html lang="en">
{head_html}
<body>
    <div class="container">
        <header>
            <h1><span class="kite-icon">🪁</span>CopilotKit Remote Endpoint <span class="version">(v{version})</span></h1>
        </header>

        <main>
            <section>
                <h2>Actions</h2>
                <div class="grid">
                    {action_html}
                </div>
            </section>
            <section>
                <h2>Agents</h2>
                <div class="grid">
                    {agent_html}
                </div>
            </section>
        </main>
    </div>
</body>
</html>
"""

# HTML 템플릿: 개별 액션 카드 (이름, 설명, 파라미터)
ACTION_TEMPLATE = """
<div class="card">
    <h3>{name}</h3>
    <p>{description}</p>
    <h4>Arguments:</h4>
    <pre><code>{arguments}</code></pre>
</div>
"""

# HTML 템플릿: 개별 에이전트 카드 (이름, 타입 배지, 설명)
AGENT_TEMPLATE = """
<div class="card">
    <h3>{name} <span class="badge">{type}</span></h3>
    <p>{description}</p>
</div>
"""

# HTML 템플릿: 액션이 없을 때 표시되는 메시지
NO_ACTIONS_FOUND_HTML = """
<div class="card">
    <p>No actions found</p>
</div>
"""

# HTML 템플릿: 에이전트가 없을 때 표시되는 메시지
NO_AGENTS_FOUND_HTML = """
<div class="card">
    <p>No agents found</p>
</div>
"""

def generate_info_html(info: InfoDict) -> str:
    """
    SDK 정보를 HTML 페이지로 변환하는 함수

    CopilotKitSDK.info()의 결과를 받아서 브라우저 친화적인 HTML 페이지를 생성합니다.
    등록된 액션과 에이전트를 카드 형식으로 표시하며, 파라미터는 JSON 형식으로 렌더링합니다.

    Parameters
    ----------
    info : InfoDict
        SDK 정보 딕셔너리
        필수 키: "sdkVersion", "actions", "agents"

    Returns
    -------
    str
        완전한 HTML 문서 문자열 (<!DOCTYPE html>부터 </html>까지)

    Examples
    --------
    기본 사용:

    >>> from copilotkit import CopilotKitSDK
    >>> from copilotkit.html import generate_info_html
    >>> sdk = CopilotKitSDK()
    >>> info = sdk.info()
    >>> html = generate_info_html(info)
    >>> print(type(html))
    <class 'str'>
    >>> print(html[:15])
    <!DOCTYPE html>

    FastAPI 통합:

    >>> from fastapi import FastAPI
    >>> from fastapi.responses import HTMLResponse
    >>> app = FastAPI()
    >>>
    >>> @app.get("/info", response_class=HTMLResponse)
    >>> async def info_endpoint():
    ...     return generate_info_html(sdk.info())

    커스텀 info 생성:

    >>> custom_info = {
    ...     "sdkVersion": "0.1.12",
    ...     "actions": [
    ...         {
    ...             "name": "calculate",
    ...             "description": "Perform calculation",
    ...             "parameters": [
    ...                 {"name": "x", "type": "number"},
    ...                 {"name": "y", "type": "number"}
    ...             ]
    ...         }
    ...     ],
    ...     "agents": [
    ...         {
    ...             "name": "math_agent",
    ...             "description": "Math solver agent",
    ...             "type": "langgraph"
    ...         }
    ...     ]
    ... }
    >>> html = generate_info_html(custom_info)

    액션/에이전트 없는 경우:

    >>> empty_info = {
    ...     "sdkVersion": "0.1.12",
    ...     "actions": [],
    ...     "agents": []
    ... }
    >>> html = generate_info_html(empty_info)
    >>> # "No actions found", "No agents found" 메시지 표시

    Notes
    -----
    생성되는 HTML 구조:
    1. HEAD: CSS 스타일 (HEAD_HTML)
    2. Header: 로고 + SDK 버전
    3. Actions Section: 액션 카드들
    4. Agents Section: 에이전트 카드들

    액션 카드 구성:
    - 이름 (h3)
    - 설명 (p)
    - 파라미터 (JSON, pre/code)

    에이전트 카드 구성:
    - 이름 (h3)
    - 타입 배지 (span.badge)
    - 설명 (p)

    타입 변환:
    - "langgraph" → "LangGraph" (대문자)
    - "crewai" → (비활성화됨)

    JSON 포맷팅:
    - json.dumps(indent=2)로 읽기 쉬운 형식
    - 파라미터 리스트를 JSON 문자열로 변환

    디버깅:
    - 함수 시작 시 info 딕셔너리 출력 (flush=True)
    - 터미널에서 전달된 정보 확인 가능

    See Also
    --------
    sdk.CopilotKitSDK.info : InfoDict 생성
    sdk.InfoDict : 반환 타입 정의
    integrations.fastapi : FastAPI 통합 (info 엔드포인트)
    """
    print(info, flush=True)
    action_html = ""
    for action in info["actions"]:
        action_html += ACTION_TEMPLATE.format(
            name=action["name"],
            description=action["description"],
            arguments=json.dumps(action.get("parameters", []), indent=2),
        )
    agent_html = ""
    for agent in info["agents"]:
        agent_type = agent.get("type", "Unknown")
        if agent_type == "langgraph":
            agent_type = "LangGraph"
        # CUSTOMIZATION: CrewAI support disabled
        # elif agent_type == "crewai":
        #     agent_type = "CrewAI"

        agent_html += AGENT_TEMPLATE.format(
            name=agent["name"],
            type=agent_type,
            description=agent["description"],
        )
    return INFO_TEMPLATE.format(
        head_html=HEAD_HTML,
        version=info["sdkVersion"],
        action_html=action_html or NO_ACTIONS_FOUND_HTML,
        agent_html=agent_html or NO_AGENTS_FOUND_HTML,
    )
