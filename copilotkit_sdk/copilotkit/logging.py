"""
CopilotKit 로깅 시스템 - 환경변수 기반 로거 설정 및 터미널 출력 유틸리티

이 모듈은 CopilotKit SDK의 로깅 설정을 담당합니다.
환경변수를 통한 로그 레벨 제어와 터미널 출력 포맷팅 기능을 제공합니다.

Core Functions
--------------

**get_logger(name)**:
- 표준 Python logging 모듈 기반 로거 생성
- LOG_LEVEL 환경변수로 로그 레벨 제어
- 모듈별 독립적인 로거 관리

**bold(text)**:
- 터미널 환경에서 볼드체 출력
- TTY 감지로 자동 활성화/비활성화
- ANSI escape code 사용

Usage Examples
--------------

기본 로거 생성:

>>> from copilotkit.logging import get_logger
>>> logger = get_logger(__name__)
>>> logger.info("SDK initialized")
>>> logger.debug("Debug information")
>>> logger.error("An error occurred")

환경변수로 로그 레벨 제어:

>>> import os
>>> os.environ['LOG_LEVEL'] = 'DEBUG'
>>> logger = get_logger('my_module')
>>> logger.debug("This will be printed")  # DEBUG 레벨이므로 출력됨
>>>
>>> os.environ['LOG_LEVEL'] = 'WARNING'
>>> logger2 = get_logger('another_module')
>>> logger2.debug("This won't be printed")  # WARNING 이상만 출력
>>> logger2.warning("This will be printed")

볼드 텍스트 출력:

>>> from copilotkit.logging import bold
>>> print(f"{bold('CopilotKit SDK')} initialized")
>>> print(f"Status: {bold('READY')}")

터미널 감지:

>>> # TTY 환경 (터미널)
>>> print(bold("Bold text"))  # ANSI 코드 포함: "\033[1mBold text\033[0m"
>>>
>>> # Non-TTY 환경 (파이프, 파일 리다이렉션)
>>> print(bold("Bold text"))  # 일반 텍스트: "Bold text"

실제 사용 예제:

>>> logger = get_logger('copilotkit.sdk')
>>> logger.info(f"{bold('Action')} 'search_database' registered")
>>> logger.warning(f"{bold('Warning')}: No agents registered")
>>> logger.error(f"{bold('Error')}: Failed to execute action")

Log Levels
----------

Python logging 표준 레벨 사용:
- **DEBUG**: 상세한 디버깅 정보 (개발 중)
- **INFO**: 일반 정보 메시지 (기본 권장)
- **WARNING**: 경고 메시지 (주의 필요)
- **ERROR**: 에러 메시지 (기능 실패)
- **CRITICAL**: 치명적 에러 (시스템 중단)

환경변수 설정:
```bash
# 개발 환경
export LOG_LEVEL=DEBUG

# 프로덕션 환경
export LOG_LEVEL=INFO

# 에러만 출력
export LOG_LEVEL=ERROR
```

Best Practices
--------------

1. **모듈별 로거 사용**:
   ```python
   # 각 모듈마다 독립적인 로거
   logger = get_logger(__name__)
   ```

2. **적절한 로그 레벨**:
   - DEBUG: 변수값, 상태 변화
   - INFO: 주요 이벤트 (액션 실행, 에이전트 시작)
   - WARNING: 복구 가능한 문제
   - ERROR: 실패, 예외

3. **구조화된 로깅**:
   ```python
   logger.info(
       f"Action executed: {action_name}",
       extra={"action": action_name, "duration": duration}
   )
   ```

4. **볼드 사용 지침**:
   - 중요 키워드 강조
   - 사용자 출력에만 사용 (로그 파일에는 사용 안 함)

5. **성능 고려**:
   ```python
   # 비용이 큰 작업은 레벨 체크 후 실행
   if logger.isEnabledFor(logging.DEBUG):
       logger.debug(f"State: {expensive_serialize(state)}")
   ```

Common Pitfalls
---------------

1. **로그 레벨 미설정**: 기본 WARNING 레벨로 INFO 로그 누락
2. **과도한 DEBUG**: 프로덕션에서 DEBUG 레벨 사용 → 성능 저하
3. **Non-TTY 환경 무시**: 파이프/파일 출력 시 ANSI 코드 깨짐 (bold() 자동 처리)
4. **로거 재생성**: 매번 get_logger() 호출 → 모듈 레벨에서 한 번만 생성
5. **예외 로깅 누락**: exc_info=True 미사용 → 스택 트레이스 손실

Environment Variables
---------------------

**LOG_LEVEL**:
- 설명: 로그 출력 최소 레벨
- 값: DEBUG, INFO, WARNING, ERROR, CRITICAL (대소문자 무관)
- 기본값: 설정 안 함 (Python logging 기본값 사용, 보통 WARNING)
- 예: `export LOG_LEVEL=INFO`

TTY Detection
-------------

bold() 함수는 자동으로 TTY 환경을 감지합니다:
- **TTY 환경** (터미널 직접 출력): ANSI escape code 사용
- **Non-TTY** (파이프, 파일): 일반 텍스트 반환

```python
# 터미널
$ python -c "from copilotkit.logging import bold; print(bold('test'))"
# 출력: \033[1mtest\033[0m (볼드체로 표시)

# 파이프
$ python -c "from copilotkit.logging import bold; print(bold('test'))" | cat
# 출력: test (일반 텍스트)
```

Integration with SDK
--------------------

SDK 전반에서 사용:
- FastAPI 통합: 요청/응답 로깅
- LangGraph Agent: 노드 실행 로깅
- Action 실행: 성공/실패 로깅
- 에러 처리: 예외 스택 트레이스

See Also
--------
exc : 예외 클래스 (에러 로깅과 함께 사용)
sdk : CopilotKitSDK (info 메서드 출력에 bold() 사용)
"""

import logging
import os
import sys

def get_logger(name: str):
    """
    환경변수 기반 로그 레벨이 설정된 로거를 반환하는 함수

    Python 표준 logging 모듈의 로거를 생성하며,
    LOG_LEVEL 환경변수가 설정되어 있으면 해당 레벨을 적용합니다.

    Parameters
    ----------
    name : str
        로거 이름 (일반적으로 __name__ 사용)
        예: 'copilotkit.sdk', 'copilotkit.action'

    Returns
    -------
    logging.Logger
        설정된 로거 인스턴스

    Examples
    --------
    기본 사용:

    >>> from copilotkit.logging import get_logger
    >>> logger = get_logger(__name__)
    >>> logger.info("Module initialized")

    환경변수로 레벨 제어:

    >>> import os
    >>> os.environ['LOG_LEVEL'] = 'DEBUG'
    >>> logger = get_logger('my_module')
    >>> logger.debug("This will be visible")

    모듈 레벨에서 사용 (권장):

    >>> # my_module.py
    >>> from copilotkit.logging import get_logger
    >>> logger = get_logger(__name__)  # 모듈 레벨에서 한 번만
    >>>
    >>> def my_function():
    ...     logger.info("Function called")  # 함수 내에서 재사용

    Notes
    -----
    - LOG_LEVEL 환경변수가 없으면 Python logging 기본 설정 사용
    - 로그 레벨은 대소문자 무관 (debug, DEBUG 모두 가능)
    - 동일한 name으로 여러 번 호출 시 같은 로거 인스턴스 반환

    환경변수 설정:
    ```bash
    export LOG_LEVEL=DEBUG  # 개발
    export LOG_LEVEL=INFO   # 프로덕션
    ```

    See Also
    --------
    bold : 터미널 출력 포맷팅
    """
    logger = logging.getLogger(name)
    log_level = os.getenv('LOG_LEVEL')
    if log_level:
        logger.setLevel(log_level.upper())
    return logger

def bold(text: str) -> str:
    """
    터미널 환경에서 텍스트를 볼드체로 포맷팅하는 함수

    TTY(터미널) 환경을 자동 감지하여 ANSI escape code를 적용합니다.
    Non-TTY 환경(파이프, 파일 리다이렉션)에서는 원본 텍스트를 반환합니다.

    Parameters
    ----------
    text : str
        볼드체로 표시할 텍스트

    Returns
    -------
    str
        TTY 환경: ANSI escape code가 적용된 볼드 텍스트
        Non-TTY 환경: 원본 텍스트

    Examples
    --------
    기본 사용:

    >>> from copilotkit.logging import bold
    >>> print(f"{bold('CopilotKit')} initialized")
    >>> print(f"Status: {bold('READY')}")

    로깅과 함께 사용:

    >>> logger.info(f"{bold('Action')} 'search' executed")
    >>> logger.error(f"{bold('Error')}: Failed to connect")

    TTY vs Non-TTY:

    >>> # 터미널에서 실행
    >>> print(bold("Test"))
    # 출력: \033[1mTest\033[0m (볼드로 표시됨)
    >>>
    >>> # 파일로 리다이렉션
    >>> print(bold("Test")) > output.txt
    # 파일 내용: Test (일반 텍스트)

    Notes
    -----
    - sys.stdout.isatty()로 TTY 환경 감지
    - ANSI escape code: `\\033[1m` (볼드 시작), `\\033[0m` (리셋)
    - 로그 파일 출력 시 ANSI 코드가 포함되지 않도록 자동 처리
    - 중요한 키워드나 상태 강조에 사용

    ANSI Escape Codes:
    - \\033[1m: 볼드 활성화
    - \\033[0m: 모든 스타일 리셋

    Use Cases:
    - 에러 메시지 강조
    - 상태 표시 (READY, ERROR, SUCCESS)
    - 중요 키워드 하이라이트

    See Also
    --------
    get_logger : 로거 생성
    """
    if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
        return f"\033[1m{text}\033[0m"
    return text
