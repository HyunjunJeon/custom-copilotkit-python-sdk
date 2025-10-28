"""
CopilotKit Action - 사용자 정의 액션 (함수 호출) 정의

이 모듈은 CopilotKit에서 AI 에이전트가 호출할 수 있는 커스텀 액션을 정의합니다.
액션은 특정 작업을 수행하는 Python 함수를 AI에 노출시키는 방법으로,
이메일 전송, 데이터베이스 쿼리, API 호출 등 다양한 작업에 사용됩니다.

주요 개념
--------

**Action (액션)**:
  - AI가 호출할 수 있는 사용자 정의 함수
  - 함수명, 설명, 파라미터 스키마, 핸들러 함수로 구성
  - 동기/비동기 핸들러 모두 지원
  - LangChain의 도구(Tool)와 유사한 개념

**Handler (핸들러)**:
  - 액션이 실행될 때 호출되는 실제 Python 함수
  - 동기 함수 또는 async 함수 가능
  - 키워드 인자로 파라미터를 받음
  - 반환값은 JSON 직렬화 가능해야 함

**Parameter (파라미터)**:
  - 액션 호출 시 전달할 인자의 스키마
  - 타입, 설명, 필수 여부 등을 정의
  - SimpleParameter, ObjectParameter, StringParameter 지원
  - 자세한 내용은 copilotkit.parameter 모듈 참조

Action Lifecycle
----------------

```mermaid
sequenceDiagram
    participant User as 사용자/AI
    participant SDK as CopilotKitRemoteEndpoint
    participant Action as Action 인스턴스
    participant Handler as 핸들러 함수

    Note over User,Handler: 1. 액션 정의 및 등록
    User->>Action: Action(name, handler, params)
    Action->>Action: 이름 검증 (정규식)
    User->>SDK: CopilotKitRemoteEndpoint(actions=[action])
    SDK->>SDK: 액션 등록

    Note over User,Handler: 2. 액션 정보 조회 (선택)
    User->>SDK: info()
    SDK->>Action: dict_repr()
    Action-->>SDK: ActionDict
    SDK-->>User: 액션 스키마 반환

    Note over User,Handler: 3. 액션 실행
    User->>SDK: execute_action(name, arguments)
    SDK->>SDK: _get_action(name)
    SDK->>Action: execute(arguments=args)
    Action->>Handler: handler(**arguments)

    alt 동기 핸들러
        Handler-->>Action: 결과 반환
    else 비동기 핸들러
        Handler-->>Action: coroutine 반환
        Action->>Action: await result
    end

    Action-->>SDK: ActionResultDict
    SDK-->>User: 실행 결과

    Note over User,Handler: 4. 에러 처리
    alt 액션을 찾을 수 없음
        SDK-->>User: ActionNotFoundException
    else 실행 중 에러
        Handler-->>Action: Exception
        Action-->>SDK: ActionExecutionException
        SDK-->>User: 에러 메시지
    end
```

Usage Examples
--------------

### 1. 동기 핸들러를 사용한 간단한 액션

```python
from copilotkit import Action

def greet(name: str, greeting: str = "Hello"):
    '''사용자에게 인사합니다'''
    return f"{greeting}, {name}!"

greet_action = Action(
    name="greet_user",
    description="사용자에게 친근하게 인사합니다",
    handler=greet,
    parameters=[
        {"name": "name", "type": "string", "description": "사용자 이름"},
        {
            "name": "greeting",
            "type": "string",
            "description": "인사말",
            "required": False
        }
    ]
)

# 실행 예제
result = await greet_action.execute(arguments={"name": "Alice"})
print(result)  # {"result": "Hello, Alice!"}
```

### 2. 비동기 핸들러를 사용한 액션

```python
import asyncio
from copilotkit import Action

async def fetch_data(url: str):
    '''외부 API에서 데이터를 가져옵니다'''
    await asyncio.sleep(1)  # 네트워크 요청 시뮬레이션
    return {"url": url, "status": "success", "data": [...]}

fetch_action = Action(
    name="fetch_external_data",
    description="외부 API에서 데이터를 비동기로 가져옵니다",
    handler=fetch_data,
    parameters=[
        {"name": "url", "type": "string", "description": "API 엔드포인트 URL"}
    ]
)
```

### 3. 복잡한 파라미터를 사용한 액션

```python
from copilotkit import Action

def create_user(name: str, email: str, address: dict, tags: list):
    '''새로운 사용자를 생성합니다'''
    return {
        "id": "user_123",
        "name": name,
        "email": email,
        "address": address,
        "tags": tags
    }

create_user_action = Action(
    name="create_user",
    description="시스템에 새로운 사용자를 생성합니다",
    handler=create_user,
    parameters=[
        {"name": "name", "type": "string", "description": "사용자 이름"},
        {"name": "email", "type": "string", "description": "이메일 주소"},
        {
            "name": "address",
            "type": "object",
            "description": "주소 정보",
            "attributes": [
                {"name": "street", "type": "string"},
                {"name": "city", "type": "string"},
                {"name": "zipcode", "type": "string"}
            ]
        },
        {
            "name": "tags",
            "type": "string[]",
            "description": "사용자 태그",
            "required": False
        }
    ]
)
```

### 4. SDK에 액션 등록

```python
from copilotkit import CopilotKitRemoteEndpoint, Action

# 여러 액션 정의
actions = [greet_action, fetch_action, create_user_action]

# SDK 인스턴스 생성
sdk = CopilotKitRemoteEndpoint(actions=actions)

# 또는 동적 빌더 사용 (컨텍스트 기반)
def build_actions(context):
    '''사용자 컨텍스트에 따라 액션을 동적으로 생성'''
    if context.user.is_admin:
        return [greet_action, create_user_action]
    else:
        return [greet_action]

sdk = CopilotKitRemoteEndpoint(actions=build_actions)
```

Best Practices
--------------

1. **액션 이름 규칙**:
   - 영문자, 숫자, 언더스코어(_), 하이픈(-)만 사용
   - 동사로 시작하는 명확한 이름 (예: send_email, get_data)
   - 정규식: `^[a-zA-Z0-9_-]+$`

2. **설명 작성**:
   - AI가 이해할 수 있도록 명확하고 구체적으로 작성
   - 언제 이 액션을 사용해야 하는지 설명
   - 예: "사용자에게 이메일을 전송합니다 (긴급 알림용)"

3. **파라미터 정의**:
   - 모든 파라미터에 description 추가
   - 필수/선택 여부를 명확히 (required 필드)
   - 타입을 정확하게 지정

4. **핸들러 구현**:
   - 에러 발생 시 명확한 예외 메시지 제공
   - 긴 작업은 async 핸들러 사용
   - 반환값은 JSON 직렬화 가능하게 (dict, list, str, int 등)
   - 파일 객체, 클래스 인스턴스 등은 피하기

5. **비동기 처리**:
   - I/O 작업(네트워크, 파일)은 async/await 사용
   - CPU 집약적 작업은 ThreadPoolExecutor 고려
   - 타임아웃 설정으로 무한 대기 방지

Common Pitfalls
---------------

- ❌ **잘못된 액션 이름**: 공백, 특수문자 사용
  ```python
  Action(name="send email")  # ValueError 발생!
  ```

- ❌ **직렬화 불가능한 반환값**:
  ```python
  def bad_handler():
      return open("file.txt")  # 파일 객체는 JSON 직렬화 불가!
  ```

- ❌ **위치 인자 사용**:
  ```python
  def bad_handler(name, email):  # 키워드 인자를 사용해야 함!
      pass
  ```

- ✅ **올바른 구현**:
  ```python
  Action(name="send_email")  # 언더스코어 사용

  def good_handler():
      return {"status": "success"}  # dict 반환

  def good_handler(name: str, email: str):  # 키워드 인자
      pass
  ```

See Also
--------

- copilotkit.parameter: 파라미터 타입 정의
- copilotkit.sdk.CopilotKitRemoteEndpoint: SDK 메인 클래스
- copilotkit.exc.ActionNotFoundException: 액션을 찾을 수 없는 경우
- copilotkit.exc.ActionExecutionException: 액션 실행 중 에러
"""

import re
from inspect import iscoroutinefunction
from typing import Optional, List, Callable, TypedDict, Any, cast
from .parameter import Parameter, normalize_parameters

class ActionDict(TypedDict):
    """
    액션의 딕셔너리 표현

    Action 인스턴스를 JSON 직렬화 가능한 딕셔너리로 변환한 형태입니다.
    주로 info() 엔드포인트에서 클라이언트에 액션 스키마를 전달할 때 사용됩니다.

    Attributes
    ----------
    name : str
        액션 이름 (영문자, 숫자, _, - 만 허용)
    description : str
        액션 설명 (AI가 이해할 수 있는 명확한 설명)
    parameters : List[Parameter]
        파라미터 스키마 리스트 (정규화된 형태)

    Examples
    --------
    >>> action = Action(name="greet", handler=lambda name: f"Hello {name}")
    >>> action_dict = action.dict_repr()
    >>> print(action_dict)
    {
        "name": "greet",
        "description": "",
        "parameters": []
    }
    """
    name: str
    description: str
    parameters: List[Parameter]

class ActionResultDict(TypedDict):
    """
    액션 실행 결과의 딕셔너리 표현

    Action.execute() 메서드가 반환하는 결과 형식입니다.
    핸들러 함수의 반환값을 "result" 키에 담아 전달합니다.

    Attributes
    ----------
    result : Any
        핸들러 함수의 실행 결과
        JSON 직렬화 가능한 타입이어야 함 (dict, list, str, int, float, bool, None)

    Examples
    --------
    >>> def add(a: int, b: int):
    ...     return a + b
    >>> action = Action(name="add", handler=add)
    >>> result = await action.execute(arguments={"a": 1, "b": 2})
    >>> print(result)
    {"result": 3}
    """
    result: Any

class Action:  # pylint: disable=too-few-public-methods
    """
    CopilotKit 액션 클래스

    AI 에이전트가 호출할 수 있는 사용자 정의 함수를 정의합니다.
    액션은 이름, 설명, 파라미터 스키마, 실제 핸들러 함수로 구성되며,
    SDK에 등록되어 클라이언트로부터 호출될 수 있습니다.

    Attributes
    ----------
    name : str
        액션 이름 (영문자, 숫자, _, - 만 허용)
    description : Optional[str]
        액션 설명 (AI가 이해할 수 있는 명확한 설명)
    parameters : Optional[List[Parameter]]
        파라미터 스키마 리스트
    handler : Callable
        실제 실행될 핸들러 함수 (동기/비동기 모두 지원)

    Examples
    --------
    >>> # 동기 핸들러
    >>> def send_email(to: str, subject: str):
    ...     print(f"Sending to {to}: {subject}")
    ...     return {"status": "sent"}
    >>>
    >>> email_action = Action(
    ...     name="send_email",
    ...     description="사용자에게 이메일을 전송합니다",
    ...     handler=send_email,
    ...     parameters=[
    ...         {"name": "to", "type": "string", "description": "수신자 이메일"},
    ...         {"name": "subject", "type": "string", "description": "제목"}
    ...     ]
    ... )

    >>> # 비동기 핸들러
    >>> async def fetch_data(url: str):
    ...     # 비동기 HTTP 요청
    ...     return {"url": url, "data": [...]}
    >>>
    >>> fetch_action = Action(
    ...     name="fetch_data",
    ...     handler=fetch_data,
    ...     parameters=[{"name": "url", "type": "string"}]
    ... )

    See Also
    --------
    copilotkit.parameter.Parameter : 파라미터 타입 정의
    copilotkit.sdk.CopilotKitRemoteEndpoint : SDK 메인 클래스
    """
    def __init__(
            self,
            *,
            name: str,
            handler: Callable,
            description: Optional[str] = None,
            parameters: Optional[List[Parameter]] = None,
        ):
        """
        Action 인스턴스를 생성합니다.

        Parameters
        ----------
        name : str
            액션 이름 (영문자, 숫자, _, - 만 허용)
            정규식 패턴: ^[a-zA-Z0-9_-]+$
        handler : Callable
            액션이 실행될 때 호출될 함수
            동기 함수 또는 async 함수 모두 가능
            키워드 인자(**kwargs)로 파라미터를 받아야 함
        description : Optional[str], default=None
            액션에 대한 설명
            AI가 언제 이 액션을 사용해야 하는지 이해할 수 있도록 작성
        parameters : Optional[List[Parameter]], default=None
            파라미터 스키마 리스트
            각 파라미터는 name, type, description, required 등을 포함

        Raises
        ------
        ValueError
            name이 정규식 패턴에 맞지 않을 경우
            (공백, 특수문자 사용 불가)

        Examples
        --------
        >>> # 간단한 액션
        >>> action = Action(
        ...     name="greet",
        ...     handler=lambda name: f"Hello, {name}!",
        ...     description="사용자에게 인사합니다"
        ... )

        >>> # 파라미터가 있는 액션
        >>> def calculator(operation: str, a: float, b: float):
        ...     if operation == "add":
        ...         return a + b
        ...     elif operation == "multiply":
        ...         return a * b
        >>>
        >>> calc_action = Action(
        ...     name="calculator",
        ...     handler=calculator,
        ...     parameters=[
        ...         {"name": "operation", "type": "string", "enum": ["add", "multiply"]},
        ...         {"name": "a", "type": "number"},
        ...         {"name": "b", "type": "number"}
        ...     ]
        ... )

        >>> # 잘못된 이름 (에러 발생)
        >>> try:
        ...     Action(name="send email", handler=lambda: None)  # 공백 포함!
        ... except ValueError as e:
        ...     print(e)
        Invalid action name 'send email': must consist of alphanumeric characters, underscores, and hyphens only
        """
        self.name = name
        self.description = description
        self.parameters = parameters
        self.handler = handler

        # 액션 이름 검증 (정규식 패턴)
        if not re.match(r"^[a-zA-Z0-9_-]+$", name):
            raise ValueError(
                f"Invalid action name '{name}': " +
                "must consist of alphanumeric characters, underscores, and hyphens only"
            )

    async def execute(
            self,
            *,
            arguments: dict
        ) -> ActionResultDict:
        """
        액션 핸들러를 실행합니다.

        전달받은 arguments를 핸들러 함수에 키워드 인자로 전달하여 실행합니다.
        핸들러가 동기 함수인 경우 결과를 즉시 반환하고,
        비동기 함수인 경우 await하여 결과를 기다립니다.

        Parameters
        ----------
        arguments : dict
            핸들러 함수에 전달할 키워드 인자
            키는 파라미터 이름, 값은 파라미터 값

        Returns
        -------
        ActionResultDict
            실행 결과를 담은 딕셔너리
            {"result": <핸들러 반환값>} 형태

        Raises
        ------
        Exception
            핸들러 함수 실행 중 발생한 모든 예외는 그대로 전파됨
            SDK에서 ActionExecutionException으로 래핑됨

        Examples
        --------
        >>> # 동기 핸들러 실행
        >>> def add(a: int, b: int):
        ...     return a + b
        >>> action = Action(name="add", handler=add)
        >>> result = await action.execute(arguments={"a": 1, "b": 2})
        >>> print(result)
        {"result": 3}

        >>> # 비동기 핸들러 실행
        >>> async def fetch(url: str):
        ...     await asyncio.sleep(0.1)
        ...     return {"url": url, "data": "..."}
        >>> action = Action(name="fetch", handler=fetch)
        >>> result = await action.execute(arguments={"url": "https://api.example.com"})
        >>> print(result)
        {"result": {"url": "https://api.example.com", "data": "..."}}

        Notes
        -----
        - execute()는 항상 async 메서드이므로 await해야 합니다
        - 핸들러가 동기 함수여도 execute()는 async입니다
        - iscoroutinefunction()으로 핸들러 타입을 자동 감지합니다
        - 핸들러 함수는 **arguments로 키워드 인자를 받습니다
        """
        # 핸들러 함수 호출 (키워드 인자로 전달)
        result = self.handler(**arguments)

        # 비동기 함수인 경우 await, 동기 함수인 경우 그대로 반환
        return {
            "result": await result if iscoroutinefunction(self.handler) else result
        }

    def dict_repr(self) -> ActionDict:
        """
        액션을 딕셔너리 형태로 직렬화합니다.

        액션의 스키마 정보(이름, 설명, 파라미터)를 JSON 직렬화 가능한
        딕셔너리로 변환합니다. 주로 info() 엔드포인트에서 클라이언트에게
        사용 가능한 액션 목록을 전달할 때 사용됩니다.

        Returns
        -------
        ActionDict
            액션 스키마를 담은 딕셔너리
            - name: 액션 이름
            - description: 액션 설명 (None이면 빈 문자열)
            - parameters: 정규화된 파라미터 리스트

        Examples
        --------
        >>> action = Action(
        ...     name="send_email",
        ...     description="이메일을 전송합니다",
        ...     handler=lambda to, subject: None,
        ...     parameters=[
        ...         {"name": "to", "type": "string"},
        ...         {"name": "subject"}  # type 없음 (정규화 필요)
        ...     ]
        ... )
        >>> schema = action.dict_repr()
        >>> print(schema)
        {
            "name": "send_email",
            "description": "이메일을 전송합니다",
            "parameters": [
                {"name": "to", "type": "string", "required": True, "description": ""},
                {"name": "subject", "type": "string", "required": True, "description": ""}
            ]
        }

        Notes
        -----
        - normalize_parameters()를 호출하여 파라미터를 정규화합니다
        - 정규화 과정에서 누락된 type, required, description이 자동으로 추가됩니다
        - description이 None이면 빈 문자열로 변환됩니다
        - 핸들러 함수는 포함되지 않습니다 (직렬화 불가능)

        See Also
        --------
        copilotkit.parameter.normalize_parameters : 파라미터 정규화 함수
        ActionDict : 반환 타입 정의
        """
        return {
            'name': self.name,
            'description': self.description or '',  # None이면 빈 문자열
            'parameters': normalize_parameters(cast(Any, self.parameters)),  # 파라미터 정규화
        }
