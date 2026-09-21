# SQLAlchemy + SQLite 연동

## 왜 필요한가

이전 단계(`items_db: dict[int, Item] = {}`)는 메모리 저장이라 **서버가 재시작되면 데이터가 전부 사라지는 한계**가 있었음. 이걸 해결하려면 서버가 꺼졌다 켜져도 데이터가 남는 **진짜 데이터베이스**가 필요함.

## 설치

```bash
pipenv install sqlalchemy
```

SQLite 자체는 파이썬에 기본 내장(`sqlite3`)이라 별도 설치 불필요. 서버 프로그램 없이 파일 하나로 DB가 동작하는 게 특징.

## 파일 구조

```
main.py          # FastAPI 앱 + 라우트
database.py      # DB 연결 설정
models.py        # SQLAlchemy 테이블 정의
schemas.py       # Pydantic 스키마 (요청/응답 형태)
```

역할 분리 이유: **DB 안의 실제 구조(models.py)**와 **API가 주고받는 형태(schemas.py)**가 항상 같지는 않기 때문 (예: 비밀번호 컬럼은 DB엔 있어도 응답엔 절대 포함하면 안 되는 경우 등).

---

## 1. database.py — DB 연결

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./items.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
```

| 요소 | 역할 | 비유 |
|---|---|---|
| `SQLALCHEMY_DATABASE_URL` | DB 주소. `sqlite:///./items.db`는 현재 폴더에 `items.db` 파일로 DB 생성 | 집 주소 |
| `engine` | 파이썬과 DB 파일 사이를 연결하는 통로 | 수도관 |
| `connect_args={"check_same_thread": False}` | SQLite는 기본적으로 커넥션을 만든 스레드에서만 써야 하는데, FastAPI는 요청마다 다른 스레드를 쓸 수 있어서 필요. **SQLite만의 특수 사정** (PostgreSQL/MySQL에는 불필요) | - |
| `SessionLocal` | 세션(작업 단위)을 만들어주는 공장. 호출할 때마다 새 세션 생성 | 수도관에서 물 떠 쓰는 컵 |
| `autocommit=False` | 명시적으로 `commit()`을 호출해야 실제 DB에 반영됨 (원치 않는 순간 저장 방지) | - |
| `Base` | 모든 테이블 클래스가 상속받는 부모 클래스. 이걸 상속하면 "이건 실제 DB 테이블이다"라고 인식됨 | 테이블 설계 공용 템플릿 |

---

## 2. models.py — 테이블 정의 (SQLAlchemy)

```python
from sqlalchemy import Column, Integer, String, Float, Boolean
from database import Base

class ItemModel(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    price = Column(Float)
    is_available = Column(Boolean, default=True)
```

- `__tablename__`: 실제 SQLite 안에 생성될 테이블 이름 (필수)
- `primary_key=True`: 기본키. 자동으로 1, 2, 3... 채번(auto-increment) — 예전에 직접 관리하던 `next_id`를 DB가 대신 해줌
- `index=True`: 검색 인덱스 → 해당 컬럼으로 조회할 때 속도 향상
- `default=True`: 값을 안 넣으면 DB가 자동으로 채워줌

이 클래스 자체는 데이터가 아니라 **테이블의 설계도**. 실제 데이터는 `ItemModel(name="키보드", price=29900)`처럼 인스턴스를 만들어서 다룸.

---

## 3. schemas.py — Pydantic 스키마

```python
from pydantic import BaseModel

class ItemCreate(BaseModel):
    name: str
    price: float
    is_available: bool = True

class ItemResponse(ItemCreate):
    id: int

    class Config:
        from_attributes = True
```

- `ItemCreate`: 클라이언트가 **보낼 때** 쓰는 형태 (id 없음 — 아직 DB가 채번 안 했으니까)
- `ItemResponse(ItemCreate)`: `ItemCreate`를 상속 + `id` 추가 → 서버가 **응답할 때** 쓰는 형태
- `from_attributes = True`: DB 조회 결과는 딕셔너리가 아니라 **SQLAlchemy 객체**로 나오는데, 이 옵션을 켜야 Pydantic이 객체의 속성(`.name`, `.price`)으로도 값을 읽어올 수 있음. (Pydantic v1에서는 `orm_mode = True`였고 v2부터 이름 변경됨)

---

## 4. main.py — DB 연동 라우트

```python
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session

from database import engine, SessionLocal, Base
import models
import schemas

Base.metadata.create_all(bind=engine)   # 테이블 없으면 자동 생성

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/items", response_model=schemas.ItemResponse)
def create_item(item: schemas.ItemCreate, db: Session = Depends(get_db)):
    db_item = models.ItemModel(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.get("/items", response_model=list[schemas.ItemResponse])
def list_items(db: Session = Depends(get_db)):
    return db.query(models.ItemModel).all()

@app.get("/items/{item_id}", response_model=schemas.ItemResponse)
def read_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(models.ItemModel).filter(models.ItemModel.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item

@app.put("/items/{item_id}", response_model=schemas.ItemResponse)
def update_item(item_id: int, item: schemas.ItemCreate, db: Session = Depends(get_db)):
    db_item = db.query(models.ItemModel).filter(models.ItemModel.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    db_item.name = item.name
    db_item.price = item.price
    db_item.is_available = item.is_available
    db.commit()
    db.refresh(db_item)
    return db_item

@app.delete("/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(models.ItemModel).filter(models.ItemModel.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(db_item)
    db.commit()
    return {"message": f"Item {item_id} deleted"}
```

### 핵심 개념

| 개념 | 설명 |
|---|---|
| `Base.metadata.create_all(bind=engine)` | 서버 시작 시 테이블이 없으면 자동 생성 (있으면 건드리지 않음) |
| `get_db()` + `yield` | 요청마다 세션을 새로 만들고, 요청이 끝나면 `finally`에서 반드시 세션을 닫는 패턴 |
| `Depends(get_db)` | 의존성 주입. 라우트 함수 실행 전에 `get_db()`를 먼저 실행해서 결과(세션)를 파라미터로 넣어줌 |
| `response_model=schemas.ItemResponse` | SQLAlchemy 객체를 자동으로 `ItemResponse` 형태로 변환해서 응답 |

### CRUD 패턴 요약

```python
# CREATE
db.add(db_item); db.commit(); db.refresh(db_item)

# READ
db.query(Model).filter(Model.id == item_id).first()   # 단건
db.query(Model).all()                                 # 전체

# UPDATE
db_item.속성 = 새값 ... ; db.commit(); db.refresh(db_item)

# DELETE
db.delete(db_item); db.commit()
```

---