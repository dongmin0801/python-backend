# APIRouter로 라우터 분리

## 왜 필요한가

지금까지는 `main.py` 하나에 모든 라우트를 넣었음. 기능이 늘어나면(유저, 주문, 결제 등) `main.py`가 수백 줄이 되어 유지보수가 힘들어짐. 그래서 **기능별로 파일을 나누고**, `main.py`는 그것들을 조립만 하는 역할로 줄임.

FastAPI의 **`APIRouter`**가 이 역할을 함.

## 폴더 구조

```
07_router/
├── main.py            # 앱 생성 + 라우터 등록만 담당
├── database.py        # DB 연결 설정
├── models.py          # SQLAlchemy 테이블 정의
├── schemas.py         # Pydantic 스키마
├── items.db
└── routers/
    ├── __init__.py    # 빈 파일 (패키지로 인식시키는 용도)
    └── items.py       # 아이템 관련 라우트
```

> `routers/__init__.py`가 있어야 파이썬이 `routers` 폴더를 패키지로 인식해서 `from routers import items`가 가능함.

---

## routers/items.py

```python
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from database import SessionLocal
import models
import schemas

router = APIRouter(prefix="/items", tags=["items"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("", response_model=schemas.ItemResponse)
def create_item(item: schemas.ItemCreate, db: Session = Depends(get_db)):
    ...

@router.get("", response_model=list[schemas.ItemResponse])
def list_items(db: Session = Depends(get_db)):
    ...

@router.get("/{item_id}", response_model=schemas.ItemResponse)
def read_item(item_id: int, db: Session = Depends(get_db)):
    ...

@router.put("/{item_id}", response_model=schemas.ItemResponse)
def update_item(item_id: int, item: schemas.ItemCreate, db: Session = Depends(get_db)):
    ...

@router.delete("/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    ...
```

### 바뀐 점

| 이전 (main.py) | 이후 (routers/items.py) |
|---|---|
| `@app.post("/items")` | `@router.post("")` |
| `@app.get("/items/{item_id}")` | `@router.get("/{item_id}")` |
| `app = FastAPI()`에 직접 등록 | `router = APIRouter(...)`에 등록 후 나중에 앱에 연결 |

- **`prefix="/items"`**: 이 라우터의 모든 경로 앞에 `/items`가 자동으로 붙음. 그래서 개별 라우트에서는 `/items`를 반복해서 쓰지 않음
  - `@router.post("")` → 실제 경로 `/items`
  - `@router.get("/{item_id}")` → 실제 경로 `/items/{item_id}`
- **`tags=["items"]`**: `/docs`에서 관련 라우트끼리 하나의 그룹으로 묶여서 보임

---

## main.py — 훨씬 짧아짐

```python
from fastapi import FastAPI
from database import engine, Base
from routers import items

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(items.router)

@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}
```

- **`app.include_router(items.router)`**: 분리해둔 라우터를 메인 앱에 등록. 이 한 줄로 `items.py`의 라우트 5개가 전부 앱에 연결됨
- 라우트 코드가 빠지면서 `main.py`는 "앱 설정 + 라우터 조립"만 담당

---


## 참고: 라우트 정의 순서

FastAPI는 위에서부터 순서대로 경로를 매칭함. 나중에 `/items/search` 같은 **고정 경로**를 추가한다면 `/{item_id}` 라우트보다 **위에** 써야 함. 아래에 쓰면 `search`라는 문자열이 `item_id`로 해석되려다 422 에러가 남.

```python
@router.get("/search")        # 고정 경로가 먼저
def search_items(): ...

@router.get("/{item_id}")     # 변수 경로는 나중에
def read_item(item_id: int): ...