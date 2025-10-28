"""
CopilotKit 예외 클래스 - 에러 처리 및 예외 계층

이 모듈은 CopilotKit SDK의 모든 커스텀 예외 클래스를 정의합니다.
액션 및 에이전트 실행 중 발생할 수 있는 다양한 에러 상황을 명확하게 구분하여
적절한 에러 처리와 디버깅을 지원합니다.

Exception Hierarchy
-------------------

```mermaid
classDiagram
    Exception <|-- ActionNotFoundException
    Exception <|-- AgentNotFoundException
    Exception <|-- ActionExecutionException
    Exception <|-- AgentExecutionException

    class Exception {
        <<built-in>>
    }

    class ActionNotFoundException {
        +str name
        +__init__(name)
        Not Found 계열
    }

    class AgentNotFoundException {
        +str name
        +__init__(name)
        Not Found 계열
    }

    class ActionExecutionException {
        +str name
        +Exception error
        +__init__(name, error)
        Execution 계열
    }

    class AgentExecutionException {
        +str name
        +Exception error
        +__init__(name, error)
        Execution 계열
    }

    note for ActionNotFoundException "액션 조회 실패"
    note for AgentNotFoundException "에이전트 조회 실패"
    note for ActionExecutionException "액션 실행 실패<br/>원본 예외 포함"
    note for AgentExecutionException "에이전트 실행 실패<br/>원본 예외 포함"
```

Exception Categories
--------------------

**1. Not Found 예외 (조회 실패)**:
- ActionNotFoundException: 요청한 액션이 SDK에 등록되지 않음
- AgentNotFoundException: 요청한 에이전트가 SDK에 등록되지 않음
- 발생 시점: execute_action(), execute_agent() 호출 시
- 해결: SDK.add_action() 또는 SDK.add_agent()로 등록 확인

**2. Execution 예외 (실행 실패)**:
- ActionExecutionException: 액션 핸들러 실행 중 예외 발생
- AgentExecutionException: 에이전트 실행 중 예외 발생
- 발생 시점: 액션/에이전트 핸들러 내부
- 원본 예외: error 속성으로 접근 가능

Core Concepts
-------------

**Exception Wrapping (예외 래핑)**:
- 원본 예외(error)를 보존하면서 컨텍스트(name) 추가
- 어떤 액션/에이전트에서 에러가 발생했는지 명확히 표시
- 스택 트레이스와 원본 에러 메시지 모두 보존

**Error Context (에러 컨텍스트)**:
- name 속성: 실패한 액션/에이전트 이름
- error 속성 (Execution 계열만): 원본 예외 객체
- 메시지: 사용자 친화적인 에러 설명

Usage Examples
--------------

Not Found 예외 처리:

>>> from copilotkit.exc import ActionNotFoundException
>>> from copilotkit import CopilotKitSDK
>>>
>>> sdk = CopilotKitSDK()
>>> try:
...     result = sdk.execute_action("non_existent_action", {})
... except ActionNotFoundException as e:
...     print(f"액션을 찾을 수 없습니다: {e.name}")
...     print("사용 가능한 액션 목록을 확인하세요.")
액션을 찾을 수 없습니다: non_existent_action
사용 가능한 액션 목록을 확인하세요.

Execution 예외 처리:

>>> from copilotkit.exc import ActionExecutionException
>>>
>>> try:
...     result = sdk.execute_action("faulty_action", {})
... except ActionExecutionException as e:
...     print(f"액션 실행 실패: {e.name}")
...     print(f"원본 에러: {e.error}")
...     print(f"에러 타입: {type(e.error).__name__}")
액션 실행 실패: faulty_action
원본 에러: division by zero
에러 타입: ZeroDivisionError

에이전트 예외 처리:

>>> from copilotkit.exc import AgentNotFoundException, AgentExecutionException
>>>
>>> try:
...     async for event in sdk.execute_agent("my_agent", {}):
...         process(event)
... except AgentNotFoundException as e:
...     print(f"에이전트 '{e.name}'가 등록되지 않았습니다.")
... except AgentExecutionException as e:
...     print(f"에이전트 '{e.name}' 실행 중 에러 발생")
...     print(f"원본 에러: {e.error}")

모든 CopilotKit 예외 처리:

>>> from copilotkit import exc
>>>
>>> # 모든 CopilotKit 예외는 Exception을 상속
>>> try:
...     # SDK 작업
...     pass
... except exc.ActionNotFoundException as e:
...     handle_not_found(e.name)
... except exc.ActionExecutionException as e:
...     handle_execution_error(e.name, e.error)
... except exc.AgentNotFoundException as e:
...     handle_not_found(e.name)
... except exc.AgentExecutionException as e:
...     handle_execution_error(e.name, e.error)
... except Exception as e:
...     # 기타 예외 처리
...     handle_unexpected_error(e)

Best Practices
--------------

1. **구체적 예외 우선 처리**:
   - 가장 구체적인 예외부터 catch
   - NotFound → Execution → 일반 Exception 순서

2. **원본 예외 보존**:
   - Execution 계열 예외의 error 속성 활용
   - 로깅 시 전체 스택 트레이스 포함

3. **사용자 친화적 메시지**:
   - name 속성으로 어떤 액션/에이전트인지 명시
   - 해결 방법 제시 (예: "액션 등록 확인")

4. **로깅 전략**:
   - NotFound: INFO 레벨 (설정 문제)
   - Execution: ERROR 레벨 (코드 버그)

5. **재시도 로직**:
   - NotFound: 재시도 불필요 (설정 수정 필요)
   - Execution: 일시적 에러라면 재시도 고려

Common Pitfalls
---------------

1. **예외 무시**: 예외를 catch만 하고 처리 안 함 → 디버깅 어려움
2. **과도한 catch**: 모든 Exception을 catch → 구체적 처리 불가
3. **원본 예외 손실**: error 속성 무시 → 근본 원인 파악 불가
4. **재시도 남용**: NotFound를 재시도 → 무한 루프
5. **부적절한 로깅**: 에러 발생 시 name과 error 로깅 안 함

Error Handling Pattern
----------------------

권장 패턴:

>>> import logging
>>> from copilotkit.exc import (
...     ActionNotFoundException, ActionExecutionException,
...     AgentNotFoundException, AgentExecutionException
... )
>>>
>>> logger = logging.getLogger(__name__)
>>>
>>> def execute_action_safely(sdk, action_name, params):
...     try:
...         return sdk.execute_action(action_name, params)
...     except ActionNotFoundException as e:
...         logger.warning(f"Action not found: {e.name}")
...         return {"error": f"Action '{e.name}' is not registered"}
...     except ActionExecutionException as e:
...         logger.error(
...             f"Action execution failed: {e.name}",
...             exc_info=e.error  # 원본 예외 스택 트레이스
...         )
...         return {"error": f"Failed to execute '{e.name}'"}

See Also
--------
sdk : CopilotKitSDK 클래스 (예외 발생 지점)
action : Action 실행 로직
agent : Agent 실행 로직
"""

class ActionNotFoundException(Exception):
    """
    액션을 찾을 수 없을 때 발생하는 예외

    SDK에 등록되지 않은 액션을 실행하려고 할 때 발생합니다.
    execute_action() 메서드에서 throw됩니다.

    Attributes
    ----------
    name : str
        찾을 수 없는 액션의 이름

    Parameters
    ----------
    name : str
        찾을 수 없는 액션 이름

    Examples
    --------
    >>> from copilotkit.exc import ActionNotFoundException
    >>> try:
    ...     sdk.execute_action("non_existent", {})
    ... except ActionNotFoundException as e:
    ...     print(f"액션 '{e.name}'가 등록되지 않았습니다.")
    ...     print("sdk.info()로 사용 가능한 액션 확인")

    Notes
    -----
    이 예외가 발생하면:
    1. SDK.info()로 등록된 액션 목록 확인
    2. SDK.add_action()으로 액션 등록 확인
    3. 액션 이름 오타 확인

    See Also
    --------
    AgentNotFoundException : 에이전트를 찾을 수 없을 때
    """

    def __init__(self, name: str):
        self.name = name
        super().__init__(f"Action '{name}' not found.")

class AgentNotFoundException(Exception):
    """
    에이전트를 찾을 수 없을 때 발생하는 예외

    SDK에 등록되지 않은 에이전트를 실행하려고 할 때 발생합니다.
    execute_agent() 메서드에서 throw됩니다.

    Attributes
    ----------
    name : str
        찾을 수 없는 에이전트의 이름

    Parameters
    ----------
    name : str
        찾을 수 없는 에이전트 이름

    Examples
    --------
    >>> from copilotkit.exc import AgentNotFoundException
    >>> try:
    ...     async for event in sdk.execute_agent("non_existent", {}):
    ...         pass
    ... except AgentNotFoundException as e:
    ...     print(f"에이전트 '{e.name}'가 등록되지 않았습니다.")
    ...     print("sdk.info()로 사용 가능한 에이전트 확인")

    Notes
    -----
    이 예외가 발생하면:
    1. SDK.info()로 등록된 에이전트 목록 확인
    2. SDK.add_agent()으로 에이전트 등록 확인
    3. 에이전트 이름 오타 확인

    See Also
    --------
    ActionNotFoundException : 액션을 찾을 수 없을 때
    """

    def __init__(self, name: str):
        self.name = name
        super().__init__(f"Agent '{name}' not found.")

class ActionExecutionException(Exception):
    """
    액션 실행 중 예외가 발생했을 때의 예외

    액션 핸들러 내부에서 예외가 발생했을 때, 원본 예외를 래핑하여
    어떤 액션에서 에러가 발생했는지 컨텍스트를 추가합니다.

    Attributes
    ----------
    name : str
        실행에 실패한 액션의 이름
    error : Exception
        원본 예외 객체 (핸들러에서 발생한 실제 에러)

    Parameters
    ----------
    name : str
        실행에 실패한 액션 이름
    error : Exception
        원본 예외

    Examples
    --------
    >>> from copilotkit.exc import ActionExecutionException
    >>> try:
    ...     result = sdk.execute_action("buggy_action", {})
    ... except ActionExecutionException as e:
    ...     print(f"액션 실행 실패: {e.name}")
    ...     print(f"원본 에러: {e.error}")
    ...     print(f"에러 타입: {type(e.error).__name__}")
    ...     # 로깅 시 원본 스택 트레이스 포함
    ...     logger.error("Action failed", exc_info=e.error)

    원본 예외 재발생:

    >>> try:
    ...     result = sdk.execute_action("action", {})
    ... except ActionExecutionException as e:
    ...     # 원본 예외를 그대로 재발생
    ...     raise e.error

    Notes
    -----
    - error 속성으로 원본 예외에 접근 가능
    - 원본 예외의 스택 트레이스는 보존됨
    - 로깅 시 exc_info=e.error로 전체 트레이스 기록

    See Also
    --------
    AgentExecutionException : 에이전트 실행 실패
    """

    def __init__(self, name: str, error: Exception):
        self.name = name
        self.error = error
        super().__init__(f"Action '{name}' failed to execute: {error}")

class AgentExecutionException(Exception):
    """
    에이전트 실행 중 예외가 발생했을 때의 예외

    에이전트 실행 중 예외가 발생했을 때, 원본 예외를 래핑하여
    어떤 에이전트에서 에러가 발생했는지 컨텍스트를 추가합니다.

    Attributes
    ----------
    name : str
        실행에 실패한 에이전트의 이름
    error : Exception
        원본 예외 객체 (에이전트 실행 중 발생한 실제 에러)

    Parameters
    ----------
    name : str
        실행에 실패한 에이전트 이름
    error : Exception
        원본 예외

    Examples
    --------
    >>> from copilotkit.exc import AgentExecutionException
    >>> try:
    ...     async for event in sdk.execute_agent("my_agent", {}):
    ...         process(event)
    ... except AgentExecutionException as e:
    ...     print(f"에이전트 실행 실패: {e.name}")
    ...     print(f"원본 에러: {e.error}")
    ...     # 로깅 시 원본 스택 트레이스 포함
    ...     logger.error(f"Agent {e.name} failed", exc_info=e.error)

    스트리밍 중 에러 처리:

    >>> try:
    ...     async for event in sdk.execute_agent("agent", {}):
    ...         if event["type"] == "error":
    ...             # 스트리밍 중 에러 감지
    ...             break
    ... except AgentExecutionException as e:
    ...     # 에이전트 실행 자체 실패
    ...     handle_agent_failure(e.name, e.error)

    Notes
    -----
    - error 속성으로 원본 예외에 접근 가능
    - LangGraph 에이전트의 경우 노드 실행 에러도 포함
    - 스트리밍 도중 발생한 에러는 RUN_ERROR 이벤트로도 전달됨

    See Also
    --------
    ActionExecutionException : 액션 실행 실패
    """

    def __init__(self, name: str, error: Exception):
        self.name = name
        self.error = error
        super().__init__(f"Agent '{name}' failed to execute: {error}")
