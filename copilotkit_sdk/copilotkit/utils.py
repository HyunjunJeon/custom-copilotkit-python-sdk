"""
CopilotKit 유틸리티 함수 - 스키마 기반 객체 필터링

이 모듈은 CopilotKit SDK의 유틸리티 함수들을 제공합니다.
현재는 스키마 키 기반 딕셔너리 필터링 함수가 포함되어 있습니다.

Usage Examples
--------------

기본 사용:

>>> from copilotkit.utils import filter_by_schema_keys
>>> obj = {"name": "John", "age": 30, "city": "Seoul", "messages": [...]}
>>> schema = {"name": str, "age": int}
>>> filtered = filter_by_schema_keys(obj, schema)
>>> print(filtered)
{'name': 'John', 'age': 30, 'messages': [...]}

LangGraph 상태 필터링:

>>> state = {
...     "user_id": 123,
...     "user_name": "Alice",
...     "messages": [...],
...     "internal_flag": True,
...     "temp_data": {...}
... }
>>> schema = {"user_id": int, "user_name": str}
>>> # user_id, user_name, messages만 보존
>>> filtered = filter_by_schema_keys(state, schema)

에러 방어:

>>> # 딕셔너리가 아닌 객체 전달 시 원본 반환
>>> result = filter_by_schema_keys("not a dict", schema)
>>> print(result)
'not a dict'

Common Use Cases
----------------

1. **LangGraph 상태 정리**: 스키마에 정의된 필드만 유지
2. **API 응답 필터링**: 클라이언트에 전송할 필드만 선택
3. **메시지 보존**: "messages" 키는 항상 보존 (LangGraph 대화 히스토리)
4. **안전한 필터링**: 에러 발생 시 원본 객체 반환

See Also
--------
langgraph : LangGraph 상태 관리
runloop : 상태 필터링 (_filter_state)
"""

def filter_by_schema_keys(obj, schema):
    """
    스키마에 정의된 키만 유지하고 나머지를 제거하는 필터링 함수

    객체(딕셔너리)에서 스키마에 정의된 키와 "messages" 키만 남기고
    나머지 키를 제거합니다. 에러 발생 시 원본 객체를 그대로 반환합니다.

    Parameters
    ----------
    obj : dict
        필터링할 딕셔너리 객체
    schema : dict
        키 이름이 정의된 스키마 딕셔너리
        값(타입)은 사용되지 않으며 키만 확인

    Returns
    -------
    dict or Any
        필터링된 딕셔너리 (스키마 키 + "messages")
        에러 발생 시 원본 obj 반환

    Examples
    --------
    기본 필터링:

    >>> obj = {"a": 1, "b": 2, "c": 3, "messages": []}
    >>> schema = {"a": int, "b": int}
    >>> result = filter_by_schema_keys(obj, schema)
    >>> print(result)
    {'a': 1, 'b': 2, 'messages': []}

    messages 키는 항상 보존:

    >>> obj = {"user": "Alice", "messages": ["msg1", "msg2"], "temp": "data"}
    >>> schema = {"user": str}
    >>> result = filter_by_schema_keys(obj, schema)
    >>> print(result)
    {'user': 'Alice', 'messages': ['msg1', 'msg2']}

    에러 발생 시 원본 반환:

    >>> # 딕셔너리가 아닌 경우
    >>> result = filter_by_schema_keys(None, schema)
    >>> print(result)
    None
    >>>
    >>> result = filter_by_schema_keys("string", schema)
    >>> print(result)
    'string'

    LangGraph 상태 필터링:

    >>> from typing import TypedDict
    >>> class State(TypedDict):
    ...     user_id: int
    ...     user_name: str
    ...     messages: list
    >>>
    >>> state_dict = {
    ...     "user_id": 123,
    ...     "user_name": "Alice",
    ...     "messages": [],
    ...     "internal_counter": 5,
    ...     "temp_flag": True
    ... }
    >>> schema = {"user_id": int, "user_name": str}  # State의 annotations
    >>> filtered = filter_by_schema_keys(state_dict, schema)
    >>> # internal_counter, temp_flag 제거됨
    >>> print(filtered)
    {'user_id': 123, 'user_name': 'Alice', 'messages': []}

    Notes
    -----
    키 보존 규칙:
    1. schema에 있는 키: 보존
    2. "messages" 키: 항상 보존 (LangGraph 대화 히스토리용)
    3. 그 외 키: 제거

    에러 처리:
    - obj.items() 호출 실패 (딕셔너리가 아닌 경우)
    - 딕셔너리 컴프리헨션 중 예외 발생
    - 모든 예외는 무시하고 원본 obj 반환

    Performance:
    - 딕셔너리 컴프리헨션으로 O(n) 시간 복잡도
    - 작은 객체에 최적화 (일반적인 상태 크기)

    Special Cases:
    - obj가 None: None 반환
    - obj가 빈 딕셔너리: {} 반환
    - schema가 빈 딕셔너리: {"messages": ...} 만 반환 (있는 경우)

    See Also
    --------
    runloop._filter_state : 비슷한 상태 필터링 함수 (exclude 기반)
    """
    try:
        return {
            k: v for k, v in obj.items()
            if k in schema or k == "messages"
        }
    except Exception:
        return obj