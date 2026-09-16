# FastAPI 학습 정리 (1일차)

##  1. FastAPI 기본

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}
```

실행:
```bash
uvicorn main:app --reload
```
- `main` = 파일명, `app` = FastAPI 인스턴스 변수명
- `--reload`: 코드 저장 시 서버 자동 재시작 (개발용)
- `/docs`: Swagger UI로 자동 문서화 + 브라우저에서 API 테스트 가능

## 3. Path Parameter vs Query Parameter

```python
# Path Parameter — URL 경로 자체에 값
@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id}

# Query Parameter — ?key=value 형식
@app.get("/search")
def search_items(q: str = "", limit: int = 10):
    return {"query": q, "limit": limit}
```

**중요**: 경로의 `{변수명}`과 함수 파라미터명이 **정확히 일치**해야 path parameter로 인식됨. 철자가 다르면 엉뚱하게 query parameter로 취급되어 라우팅이 깨짐.

## 4. Pydantic 모델 & POST 요청

```python
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    price: float
    is_available: bool = True   # 기본값 있으면 선택적 필드

@app.post("/items")
def create_item(item: Item):
    return {"received": item}
```

- 함수 파라미터에 Pydantic 모델 타입을 쓰면, FastAPI가 요청 바디(JSON)를 자동으로 파싱 + 검증
- `item.model_dump()`: Pydantic 모델 → 딕셔너리 변환

## 5. 에러 종류 구분 (중요)

| 상황 | 응답 코드 | 원인 |
|---|---|---|
| 정의 안 된 HTTP 메서드로 요청 | `405 Method Not Allowed` | 예: `/items`에 POST만 있는데 GET으로 접속 |
| JSON 문법 자체가 깨짐 | `422` + `json_invalid` | 따옴표 누락, trailing comma 등 |
| JSON은 맞는데 타입이 스키마와 불일치 | `422` + 필드 타입 에러 | 예: `price`에 문자열 입력 |
| 존재하지 않는 리소스 조회 | `404 Not Found` | `HTTPException(status_code=404)`로 직접 발생시킴 |
| 정상 처리 | `200 OK` | - |

## 6. CRUD 전체 구현 (메모리 저장)

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float
    is_available: bool = True

items_db: dict[int, Item] = {}
next_id = 1

# CREATE
@app.post("/items")
def create_item(item: Item):
    global next_id
    items_db[next_id] = item
    result = {"id": next_id, **item.model_dump()}
    next_id += 1
    return result

# READ (전체)
@app.get("/items")
def list_items():
    return [{"id": k, **v.model_dump()} for k, v in items_db.items()]

# READ (단건)
@app.get("/items/{item_id}")
def read_item(item_id: int):
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"id": item_id, **items_db[item_id].model_dump()}

# UPDATE
@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item):
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found!")
    items_db[item_id] = item   # 실제 저장 — 빠뜨리기 쉬운 부분!
    return {"id": item_id, **item.model_dump()}

# DELETE
@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found!!")
    del items_db[item_id]
    return {"message": f"Item {item_id} deleted"}
```

### 실제로 겪었던 버그: PUT이 반영 안 되는 문제

- **증상**: PUT 요청은 200 OK로 성공 응답을 주는데, 이후 GET으로 조회하면 값이 그대로였음
- **원인**: `update_item` 함수에서 `items_db`에 존재하는지 **확인만** 하고, 정작 `items_db[item_id] = item`으로 **실제 저장하는 코드가 빠져 있었음**
- **알게된 점**: GET(조회)과 PUT(수정)은 코드 구조가 비슷해 보이지만, PUT은 반드시 저장소에 값을 다시 써주는 로직이 필요함. 응답이 200이어도 실제 데이터가 안 바뀔 수 있다는 걸 기억할 것

## 7. 메모리 저장의 한계

- `items_db`는 파이썬 딕셔너리라서 **서버 프로세스가 살아있는 동안만** 데이터 유지
- `--reload` 옵션 때문에 파일 저장 시 서버가 재시작되면 **데이터가 초기화**됨
- 실무에서는 서버가 꺼졌다 켜져도 데이터가 남도록 **데이터베이스(SQLite, PostgreSQL 등)**를 사용함 → 다음 학습 주제

## 8. 디버깅 습관 (이번에 실제로 연습한 것)

1. 응답 코드(200 / 404 / 405 / 422)를 먼저 확인
2. `/docs`의 Curl 탭, Request URL, Response body를 같이 대조
3. 타임스탬프(로그의 시간)를 비교해서 "언제 무슨 일이 있었는지" 순서를 재구성
4. 코드에서 "확인만 하고 저장은 안 하는" 것처럼 로직이 빠진 부분이 없는지 점검

## 다음 학습 예정

- SQLite + SQLAlchemy로 진짜 DB 연동
- Pydantic 고급 검증 (이메일 형식, 값 범위 제한 등)
- 폴더 구조 정리 (라우터 파일 분리)