# Pydantic 고급 검증

## 왜 필요한가

타입 힌트만으로는 `price`에 음수가 들어와도, `name`에 빈 문자열이 들어와도 통과함. "문자열이다", "숫자다"까지만 검사하기 때문. 값의 **범위, 길이, 내용**까지 검증하려면 추가 규칙이 필요함.

---

## 1. Field로 제약 걸기

```python
from pydantic import BaseModel, Field

class ItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    price: float = Field(gt=0)
    is_available: bool = True

class ItemResponse(ItemCreate):
    id: int

    class Config:
        from_attributes = True
```

| 옵션 | 의미 | 대상 |
|---|---|---|
| `min_length`, `max_length` | 글자 수 제한 | 문자열 |
| `gt`, `ge` | 초과(>), 이상(>=) | 숫자 |
| `lt`, `le` | 미만(<), 이하(<=) | 숫자 |
| `pattern` | 정규식 일치 | 문자열 |

- `gt=0`은 **0 자체도 불가** (0 이상을 허용하려면 `ge=0`)
- 규칙을 어기면 FastAPI가 자동으로 **422**를 반환

---

## 2. field_validator로 직접 검증 로직 작성

`Field`로 표현하기 어려운 규칙은 함수로 직접 작성함. 예: "공백만 있는 이름은 안 된다" (`" "`는 길이가 1이라 `min_length=1`로는 못 막음)

```python
from pydantic import BaseModel, Field, field_validator

class ItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    price: float = Field(gt=0)
    is_available: bool = True

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("이름은 공백일 수 없습니다")
        return v
```

- `@field_validator("name")`: `name`이 기본 검증을 통과한 **뒤에** 실행됨
- `ValueError`를 던지면 422로 응답됨
- **반드시 `return v`** 해야 함. 반환값이 최종 저장되는 값이라 빼먹으면 `None`이 됨
- `strip()`으로 앞뒤 공백을 제거한 값이 저장됨 (`"  pen  "` → `"pen"`)

---

## 3. 테스트 케이스

| 요청 바디 | 결과 |
|---|---|
| `{"name": "keyboard", "price": 29900}` | 200 |
| `{"name": "", "price": 100}` | 422 (최소 길이) |
| `{"name": "   ", "price": 100}` | 422 (공백만 있음) |
| `{"name": "pen", "price": -5}` | 422 (0보다 커야 함) |
| `{"name": "pen", "price": 0}` | 422 (`gt`는 0 불가) |
| `{"name": "  pen  ", "price": 100}` | 200, 저장된 이름은 `"pen"` |

422 응답의 `type`은 규칙마다 다름 (`string_too_short`, `greater_than` 등). 어떤 규칙에 걸렸는지 `msg`와 `type`으로 확인할 수 있음.

---

## 4. 주의: 기존 데이터와 새 규칙의 충돌

`ItemResponse`는 `ItemCreate`를 상속하므로 **응답할 때도 같은 검증이 적용됨.** 새 규칙을 추가하기 **전에** 저장된 데이터(예: `price: 0`)가 DB에 남아 있으면, `GET`에서 `ResponseValidationError`(500)가 날 수 있음.

- 코드 문제가 아니라 **옛날 데이터가 새 규칙을 위반**하는 것
- 학습 단계에서는 `items.db`를 삭제하고 서버를 다시 켜면 해결
- 실무에서는 기존 데이터를 정리하는 마이그레이션이 필요한 상황

---

## 5. 규칙이 적용됐는지 확인하는 법

검증이 안 걸리는 것 같으면 `/docs` 맨 아래 **Schemas → `ItemCreate`**를 펼쳐서 확인함.

```
name   string  (minLength: 1, maxLength: 50)
price  number  (exclusiveMinimum: 0)
```

이 표시가 없으면 서버가 규칙이 들어간 `schemas.py`를 읽지 못하고 있다는 뜻. 저장 여부, 수정한 폴더가 실행 중인 폴더와 같은지를 확인할 것.

---

## 6. EmailStr (이메일 형식 검증)

```python
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
```

추가 패키지가 필요함: `pipenv install "pydantic[email]"`

---
