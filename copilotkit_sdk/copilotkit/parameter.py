"""
CopilotKit Parameter - 액션 파라미터 타입 시스템

이 모듈은 액션의 파라미터 스키마를 정의하는 타입 시스템을 제공합니다.
파라미터는 AI가 액션을 호출할 때 전달할 인자의 타입, 설명, 필수 여부 등을
명시하며, OpenAPI 스키마와 유사한 구조를 가집니다.

Parameter Types
---------------

CopilotKit은 3가지 파라미터 타입을 지원합니다:

1. **SimpleParameter**: 기본 타입 파라미터
   - number, boolean, number[], boolean[]
   - 단일 값 또는 배열

2. **StringParameter**: 문자열 파라미터
   - string, string[]
   - enum 옵션 지원 (선택 가능한 값 목록)

3. **ObjectParameter**: 객체 파라미터
   - object, object[]
   - 중첩된 attributes 정의 가능
   - 복잡한 데이터 구조 지원

**Parameter**: 위 3가지 타입의 Union type

Type Hierarchy
--------------

```mermaid
graph TD
    P[Parameter Union Type]
    SP[SimpleParameter]
    STP[StringParameter]
    OP[ObjectParameter]

    P --> SP
    P --> STP
    P --> OP

    subgraph "SimpleParameter Types"
    SP --> N[number]
    SP --> B[boolean]
    SP --> NA[number array]
    SP --> BA[boolean array]
    end

    subgraph "StringParameter Types"
    STP --> S[string]
    STP --> SA[string array]
    STP -.enum.-> ENUM[Enum Values]
    end

    subgraph "ObjectParameter Types"
    OP --> O[object]
    OP --> OA[object array]
    OP -.attributes.-> ATTR[List of Parameters]
    ATTR --> P
    end

    style P fill:#e1f5ff,stroke:#0066cc,stroke-width:3px
    style SP fill:#fff4e1,stroke:#ff9900,stroke-width:2px
    style STP fill:#ffe1e1,stroke:#cc0000,stroke-width:2px
    style OP fill:#e1ffe1,stroke:#00cc00,stroke-width:2px
```

Usage Examples
--------------

### 1. SimpleParameter - 기본 타입

```python
# 숫자 파라미터
age_param = {
    "name": "age",
    "type": "number",
    "description": "사용자 나이",
    "required": True
}

# 불리언 파라미터
is_active_param = {
    "name": "is_active",
    "type": "boolean",
    "description": "활성화 여부",
    "required": False
}

# 숫자 배열
scores_param = {
    "name": "scores",
    "type": "number[]",
    "description": "점수 목록"
}
```

### 2. StringParameter - 문자열 및 Enum

```python
# 일반 문자열
name_param = {
    "name": "name",
    "type": "string",
    "description": "사용자 이름"
}

# Enum 문자열 (선택지 제한)
priority_param = {
    "name": "priority",
    "type": "string",
    "description": "우선순위",
    "enum": ["low", "medium", "high"]
}

# 문자열 배열
tags_param = {
    "name": "tags",
    "type": "string[]",
    "description": "태그 목록",
    "required": False
}
```

### 3. ObjectParameter - 중첩 객체

```python
# 주소 객체
address_param = {
    "name": "address",
    "type": "object",
    "description": "주소 정보",
    "attributes": [
        {"name": "street", "type": "string", "description": "도로명"},
        {"name": "city", "type": "string", "description": "도시"},
        {"name": "zipcode", "type": "string", "description": "우편번호"}
    ]
}

# 객체 배열
contacts_param = {
    "name": "contacts",
    "type": "object[]",
    "description": "연락처 목록",
    "attributes": [
        {"name": "name", "type": "string"},
        {"name": "email", "type": "string"},
        {"name": "phone", "type": "string", "required": False}
    ]
}
```

### 4. normalize_parameters() 사용

```python
from copilotkit.parameter import normalize_parameters

# 정규화 전 (일부 필드 누락)
params = [
    {"name": "name"},  # type, required, description 없음
    {"name": "age", "type": "number"},  # required, description 없음
    {"name": "email", "type": "string", "description": "이메일 주소"}
]

# 정규화 후 (기본값 추가)
normalized = normalize_parameters(params)
# [
#     {"name": "name", "type": "string", "required": True, "description": ""},
#     {"name": "age", "type": "number", "required": True, "description": ""},
#     {"name": "email", "type": "string", "required": True, "description": "이메일 주소"}
# ]
```

### 5. Action과 함께 사용

```python
from copilotkit import Action

def create_user(name: str, email: str, address: dict, tags: list):
    return {"id": "user_123", "name": name}

action = Action(
    name="create_user",
    handler=create_user,
    parameters=[
        {
            "name": "name",
            "type": "string",
            "description": "사용자 이름"
        },
        {
            "name": "email",
            "type": "string",
            "description": "이메일 주소"
        },
        {
            "name": "address",
            "type": "object",
            "description": "주소 정보",
            "attributes": [
                {"name": "street", "type": "string"},
                {"name": "city", "type": "string"}
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

Normalization Rules
-------------------

normalize_parameters()는 다음 규칙으로 파라미터를 정규화합니다:

1. **type 기본값**: 없으면 "string" 추가
2. **required 기본값**: 없으면 True 추가
3. **description 기본값**: 없으면 빈 문자열("") 추가
4. **객체 타입**: attributes도 재귀적으로 정규화

정규화 예시:
```python
# 입력
{"name": "user"}

# 출력
{"name": "user", "type": "string", "required": True, "description": ""}
```

Best Practices
--------------

1. **항상 description 추가**:
   - AI가 파라미터의 용도를 이해할 수 있도록 명확한 설명 작성
   - 예: "사용자 이름" (O) vs "" (X)

2. **적절한 타입 선택**:
   - 숫자는 number, 문자열은 string
   - 배열은 type[] 형식 사용
   - 복잡한 구조는 object 사용

3. **required 명시**:
   - 필수가 아닌 파라미터는 required: False 설정
   - 기본값이 있는 경우 required: False

4. **enum 활용**:
   - 선택지가 제한된 경우 enum 사용
   - AI가 잘못된 값을 전달하는 것을 방지

5. **객체 구조 설계**:
   - 너무 깊은 중첩은 피하기 (2-3 레벨까지 권장)
   - attributes에는 모든 필드 명시

Common Pitfalls
---------------

- ❌ **잘못된 타입 이름**: "int", "str" 등 Python 타입 사용
  ```python
  {"name": "age", "type": "int"}  # 잘못됨!
  ```

- ❌ **배열 표기 오류**: "array[string]" 형식 사용
  ```python
  {"name": "tags", "type": "array[string]"}  # 잘못됨!
  ```

- ❌ **attributes 없는 object**:
  ```python
  {"name": "user", "type": "object"}  # attributes 누락!
  ```

- ✅ **올바른 구현**:
  ```python
  {"name": "age", "type": "number"}  # number 사용
  {"name": "tags", "type": "string[]"}  # type[] 형식
  {
      "name": "user",
      "type": "object",
      "attributes": [...]  # attributes 필수
  }
  ```

See Also
--------

- copilotkit.action.Action : 파라미터를 사용하는 액션 클래스
- copilotkit.action.ActionDict : 액션 스키마 정의
"""

from typing import TypedDict, Optional, Literal, List, Union, cast, Any
from typing_extensions import NotRequired

class SimpleParameter(TypedDict):
    """
    기본 타입 파라미터

    숫자와 불리언 타입의 단일 값 또는 배열을 정의합니다.
    가장 단순한 형태의 파라미터 타입입니다.

    Attributes
    ----------
    name : str
        파라미터 이름 (필수)
    description : str, optional
        파라미터 설명 (AI가 이해할 수 있도록 작성)
        정규화 시 기본값: ""
    required : bool, optional
        필수 여부 (True: 필수, False: 선택)
        정규화 시 기본값: True
    type : Literal["number", "boolean", "number[]", "boolean[]"], optional
        파라미터 타입
        - number: 숫자 (int, float)
        - boolean: 불리언 (True, False)
        - number[]: 숫자 배열
        - boolean[]: 불리언 배열
        정규화 시 기본값: "string" (SimpleParameter가 아닌 경우)

    Examples
    --------
    >>> # 숫자 파라미터
    >>> age: SimpleParameter = {
    ...     "name": "age",
    ...     "type": "number",
    ...     "description": "사용자 나이",
    ...     "required": True
    ... }

    >>> # 불리언 배열 파라미터
    >>> flags: SimpleParameter = {
    ...     "name": "flags",
    ...     "type": "boolean[]",
    ...     "description": "플래그 목록"
    ... }
    """
    name: str
    description: NotRequired[str]
    required: NotRequired[bool]
    type: NotRequired[Literal[
        "number",
        "boolean",
        "number[]",
        "boolean[]"
    ]]

class ObjectParameter(TypedDict):
    """
    객체 타입 파라미터

    복잡한 구조의 객체나 객체 배열을 정의합니다.
    중첩된 attributes를 통해 객체의 내부 구조를 표현할 수 있습니다.

    Attributes
    ----------
    name : str
        파라미터 이름 (필수)
    description : str, optional
        파라미터 설명
        정규화 시 기본값: ""
    required : bool, optional
        필수 여부
        정규화 시 기본값: True
    type : Literal["object", "object[]"]
        파라미터 타입 (필수)
        - object: 단일 객체
        - object[]: 객체 배열
    attributes : List[Parameter]
        객체의 속성 목록 (필수)
        각 속성은 Parameter 타입 (재귀적 구조)
        정규화 시 각 속성도 정규화됨

    Examples
    --------
    >>> # 단일 객체 파라미터
    >>> address: ObjectParameter = {
    ...     "name": "address",
    ...     "type": "object",
    ...     "description": "주소 정보",
    ...     "attributes": [
    ...         {"name": "street", "type": "string", "description": "도로명"},
    ...         {"name": "city", "type": "string", "description": "도시"},
    ...         {"name": "zipcode", "type": "string"}
    ...     ]
    ... }

    >>> # 객체 배열 파라미터 (중첩)
    >>> users: ObjectParameter = {
    ...     "name": "users",
    ...     "type": "object[]",
    ...     "description": "사용자 목록",
    ...     "attributes": [
    ...         {"name": "name", "type": "string"},
    ...         {"name": "age", "type": "number"},
    ...         {
    ...             "name": "address",  # 중첩 객체
    ...             "type": "object",
    ...             "attributes": [
    ...                 {"name": "city", "type": "string"}
    ...             ]
    ...         }
    ...     ]
    ... }
    """
    name: str
    description: NotRequired[str]
    required: NotRequired[bool]
    type: Literal["object", "object[]"]
    attributes: List['Parameter']

class StringParameter(TypedDict):
    """
    문자열 타입 파라미터

    문자열 단일 값 또는 배열을 정의합니다.
    enum 옵션을 통해 선택 가능한 값을 제한할 수 있습니다.

    Attributes
    ----------
    name : str
        파라미터 이름 (필수)
    description : str, optional
        파라미터 설명
        정규화 시 기본값: ""
    required : bool, optional
        필수 여부
        정규화 시 기본값: True
    type : Literal["string", "string[]"]
        파라미터 타입
        - string: 단일 문자열
        - string[]: 문자열 배열
        정규화 시 기본값: "string"
    enum : List[str], optional
        선택 가능한 값 목록
        enum이 있으면 AI는 이 값들 중 하나만 선택 가능

    Examples
    --------
    >>> # 일반 문자열 파라미터
    >>> name: StringParameter = {
    ...     "name": "username",
    ...     "type": "string",
    ...     "description": "사용자 이름"
    ... }

    >>> # Enum 문자열 파라미터
    >>> priority: StringParameter = {
    ...     "name": "priority",
    ...     "type": "string",
    ...     "description": "작업 우선순위",
    ...     "enum": ["low", "medium", "high", "urgent"]
    ... }

    >>> # 문자열 배열 파라미터
    >>> tags: StringParameter = {
    ...     "name": "tags",
    ...     "type": "string[]",
    ...     "description": "태그 목록",
    ...     "required": False
    ... }

    >>> # Enum 배열 파라미터
    >>> colors: StringParameter = {
    ...     "name": "colors",
    ...     "type": "string[]",
    ...     "description": "선택된 색상들",
    ...     "enum": ["red", "green", "blue", "yellow"]
    ... }
    """
    name: str
    description: NotRequired[str]
    required: NotRequired[bool]
    type: Literal["string", "string[]"]
    enum: NotRequired[List[str]]

Parameter = Union[SimpleParameter, ObjectParameter, StringParameter]
"""
파라미터 타입의 Union

SimpleParameter, ObjectParameter, StringParameter 중 하나입니다.
액션의 parameters 리스트에 사용되는 타입입니다.

Examples
--------
>>> from typing import List
>>> from copilotkit.parameter import Parameter
>>>
>>> params: List[Parameter] = [
...     {"name": "age", "type": "number"},  # SimpleParameter
...     {"name": "name", "type": "string"},  # StringParameter
...     {
...         "name": "address",  # ObjectParameter
...         "type": "object",
...         "attributes": [{"name": "city", "type": "string"}]
...     }
... ]
"""

def normalize_parameters(parameters: Optional[List[Parameter]]) -> List[Parameter]:
    """
    파라미터 리스트를 정규화합니다.

    파라미터 리스트의 각 파라미터에 대해 누락된 필드를 기본값으로 채웁니다.
    None이 전달되면 빈 리스트를 반환합니다.

    Parameters
    ----------
    parameters : Optional[List[Parameter]]
        정규화할 파라미터 리스트
        None이면 빈 리스트 반환

    Returns
    -------
    List[Parameter]
        정규화된 파라미터 리스트
        각 파라미터는 type, required, description 필드를 가짐

    Examples
    --------
    >>> # None 처리
    >>> normalize_parameters(None)
    []

    >>> # 기본값 추가
    >>> params = [{"name": "user"}]
    >>> normalize_parameters(params)
    [{"name": "user", "type": "string", "required": True, "description": ""}]

    >>> # 객체 파라미터의 재귀적 정규화
    >>> params = [
    ...     {
    ...         "name": "address",
    ...         "type": "object",
    ...         "attributes": [
    ...             {"name": "city"}  # type, required, description 없음
    ...         ]
    ...     }
    ... ]
    >>> normalized = normalize_parameters(params)
    >>> print(normalized[0]["attributes"])
    [{"name": "city", "type": "string", "required": True, "description": ""}]

    See Also
    --------
    _normalize_parameter : 단일 파라미터 정규화 (내부 함수)
    """
    if parameters is None:
        return []
    return [_normalize_parameter(parameter) for parameter in parameters]

def _normalize_parameter(parameter: Parameter) -> Parameter:
    """
    단일 파라미터를 정규화합니다 (내부 함수).

    파라미터 딕셔너리에 누락된 필드를 기본값으로 채웁니다.
    객체 타입인 경우 attributes도 재귀적으로 정규화합니다.

    Parameters
    ----------
    parameter : Parameter
        정규화할 파라미터

    Returns
    -------
    Parameter
        정규화된 파라미터 (in-place 수정됨)
        - type: 없으면 "string" 추가
        - required: 없으면 True 추가
        - description: 없으면 "" 추가
        - attributes (객체인 경우): 재귀적으로 정규화

    Notes
    -----
    - 이 함수는 파라미터를 in-place로 수정합니다
    - 객체 타입(object, object[])인 경우 attributes를 재귀적으로 정규화합니다
    - 외부에서 직접 호출하기보다는 normalize_parameters()를 사용하세요

    Examples
    --------
    >>> param = {"name": "user"}
    >>> _normalize_parameter(param)
    {"name": "user", "type": "string", "required": True, "description": ""}

    >>> # 객체 타입 정규화
    >>> param = {
    ...     "name": "address",
    ...     "type": "object",
    ...     "attributes": [{"name": "city"}]
    ... }
    >>> _normalize_parameter(param)
    {
        "name": "address",
        "type": "object",
        "required": True,
        "description": "",
        "attributes": [
            {"name": "city", "type": "string", "required": True, "description": ""}
        ]
    }
    """
    # type 필드 기본값: "string"
    if not "type" in parameter:
        cast(Any, parameter)['type'] = 'string'

    # required 필드 기본값: True
    if not 'required' in parameter:
        parameter['required'] = True

    # description 필드 기본값: ""
    if not 'description' in parameter:
        parameter['description'] = ''

    # 객체 타입인 경우 attributes도 재귀적으로 정규화
    if 'type' in parameter and (parameter['type'] == 'object' or parameter['type'] == 'object[]'):
        cast(Any, parameter)['attributes'] = normalize_parameters(parameter.get('attributes'))

    return parameter
