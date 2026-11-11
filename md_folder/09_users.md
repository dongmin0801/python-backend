# users 라우터 + 비밀번호 해싱

## 이번 단계에서 배운 것

- 라우터를 하나 더 추가하기 (분리 구조의 효과)
- `EmailStr`로 이메일 형식 검증
- 비밀번호는 **해싱해서** 저장하고, 응답에는 **절대 포함하지 않기**
- 공통 코드(`get_db`)를 한 곳으로 옮겨서 공유하기

## 준비

```bash
pipenv install "pydantic[email]" "pwdlib[argon2]"
```

- `pydantic[email]`: `EmailStr`에 필요
- `pwdlib[argon2]`: 비밀번호 해싱 라이브러리

## 폴더 구조

```
09_users/
├── main.py
├── database.py      # get_db 이동
├── models.py        # UserModel 추가
├── schemas.py       # UserCreate, UserResponse 추가
├── security.py      # 해싱 함수 (새 파일)
└── routers/
    ├── __init__.py
    ├── items.py
    └── users.py     # 새 파일
```

---

## 1. database.py — get_db 공유

두 라우터가 같은 함수를 쓰므로 복사하지 않고 `database.py`로 옮김.

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

`routers/items.py`에서는 `from database import get_db`로 가져오고, 자체 정의는 삭제.

## 2. models.py — UserModel

```python
class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
```

- `unique=True`: 같은 이메일 중복 저장 방지 (DB 차원)
- `nullable=False`: 빈 값(NULL) 불가
- 컬럼명이 `password`가 아니라 `hashed_password`인 이유: 원본이 아니라 **해시값**이 들어간다는 걸 이름으로 드러내기 위해

## 3. schemas.py — Create와 Response를 분리

```python
from pydantic import BaseModel, Field, EmailStr, ConfigDict

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class UserResponse(BaseModel):
    id: int
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)
```

### 핵심: UserResponse는 UserCreate를 상속하면 안 됨

아이템에서는 `ItemResponse(ItemCreate)` 상속이 잘 맞았음. 응답에 `ItemCreate`의 필드가 전부 들어가도 되기 때문. 하지만 `UserCreate`에는 **응답에 들어가면 안 되는 `password`**가 있으므로 상속하면 안 됨. 이것이 `Create`와 `Response`를 따로 만드는 진짜 이유.

`response_model`이 `UserResponse` 모양대로 걸러서 내보내므로, 라우트 함수가 DB 객체를 통째로 리턴해도 비밀번호는 응답에 실리지 않음.

> `ConfigDict(from_attributes=True)`는 기존 `class Config:`의 최신 문법. 기능은 같고, `class Config`는 Pydantic v2에서 deprecated 경고가 날 수 있음.

## 4. security.py — 해싱

```python
from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()

def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)
```

### 해싱이 왜 필요한가

비밀번호를 그대로 저장하면 DB가 유출됐을 때 모든 사용자의 비밀번호가 노출됨. 해싱은 **한 방향으로만 변환**해서 해시값만으로는 원본을 되돌릴 수 없게 만듦. 로그인할 때는 입력값을 같은 방식으로 해싱해서 저장값과 비교(`verify`)함.

### 저장된 해시 읽는 법

```
$argon2id$v=19$m=65536,t=3,p=4$tfQW8J2PfSJ3Ut0lEEZCtA$IwpJgLMvK6Z8Ape...
```

| 부분 | 의미 |
|---|---|
| `argon2id` | 사용한 알고리즘 |
| `v=19` | 알고리즘 버전 |
| `m=65536,t=3,p=4` | 메모리, 반복 횟수, 병렬도 (일부러 무겁게 만든 설정) |
| `tfQW8J2P...` | **salt** (매번 랜덤 생성, 해시 안에 함께 저장됨) |
| 마지막 긴 문자열 | 실제 해시 결과 |

같은 비밀번호여도 salt가 달라서 매번 다른 해시가 나오지만, `verify`가 알아서 처리함.

## 5. routers/users.py

```python
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from database import get_db
from security import hash_password
import models
import schemas

router = APIRouter(prefix="/users", tags=["users"])

@router.post("", response_model=schemas.UserResponse, status_code=201)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.UserModel).filter(models.UserModel.email == user.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    db_user = models.UserModel(
        email=user.email,
        hashed_password=hash_password(user.password),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/{user_id}", response_model=schemas.UserResponse)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(models.UserModel).filter(models.UserModel.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user
```

- `status_code=201`: "새로 생성됨". 생성 API는 200보다 201이 관례
- `409 Conflict`: 이미 존재하는 이메일이라 충돌
- 저장할 때 `user.password`를 그대로 넣지 않고 **`hash_password()`를 거침**

## 6. main.py

```python
from routers import items, users

app.include_router(items.router)
app.include_router(users.router)
```

라우터를 분리해둔 덕분에 `main.py`는 두 줄만 바뀜.

---

## 테스트 결과

| 요청 | 결과 |
|---|---|
| `{"email": "a@test.com", "password": "password123"}` | 201, `id`와 `email`만 응답 |
| 같은 요청 한 번 더 | 409 |
| `{"email": "not-an-email", ...}` | 422 (이메일 형식) |
| `{"email": "b@test.com", "password": "short"}` | 422 (8자 미만) |
| `GET /users/1` | 200, `password` 없음 |
| `GET /users/999` | 404 |

DB 확인:
```bash
python -c "import sqlite3; c = sqlite3.connect('file:items.db?mode=ro', uri=True); print(c.execute('SELECT id, email, hashed_password FROM users').fetchall())"
```
→ `hashed_password`가 `$argon2id$...`로 저장되고, 원본 비밀번호는 어디에도 없음.

---

## 겪었던 문제들 (디버깅 기록)

### 1. UserResponse 상속 → 500 `ResponseValidationError`

- **증상**: `POST /users`가 500. 로그에 `'loc': ('response', 'password'), 'msg': 'Field required'`
- **원인**: `UserResponse(UserCreate)`로 상속해서 `password`가 필수 필드로 따라왔는데, DB 객체에는 `password`가 없음
- **해결**: `UserResponse`를 상속 없이 독립된 모델로 작성
- **부수 효과**: 에러는 `db.commit()` **이후** 응답을 만드는 단계에서 났으므로 **유저는 이미 저장된 상태**. 같은 이메일로 재시도하면 409가 나서 마치 중복 검사가 고장난 것처럼 보였음. 에러가 났어도 DB에는 데이터가 남을 수 있다는 점을 기억할 것

### 2. 포트 8000에 서버가 두 개 (Windows + `--reload`)

- **증상**: 새 서버를 켰는데 요청은 옛날 서버로 가고, 종료해도 `netstat`에 `LISTENING`이 계속 남음
- **원인**: `uvicorn --reload`는 **부모(reloader) + 자식(실제 서버)** 프로세스 구조. `netstat`이 보여주는 PID는 소켓을 처음 연 부모의 PID. 부모만 종료하면 자식이 포트를 쥔 채 남음
- **해결**: 프로세스 트리째 종료
  ```bash
  taskkill //PID <PID> //T //F
  ```
  (`//T`가 자식 프로세스까지 종료. Git Bash에서는 `/`를 두 번 씀)
- **예방**: 서버는 `Ctrl+C`로 종료. 켜기 전에 `netstat -ano | findstr :8000`으로 비어 있는지 확인

### 3. 오타 두 개 (둘 다 에러 메시지 없이 조용히 동작)

| 오타 | 증상 |
|---|---|
| `sqlite:///.items.db` (`/` 누락) | 서버가 `.items.db` 숨김 파일에 저장해서 `items.db`는 계속 0바이트 |
| `hassed_password` (`s` 누락) | 코드 전체에서 일관되게 틀려서 에러 없이 동작하지만 컬럼명이 틀림 |

- **찾은 방법**
  ```bash
  # 엔진이 실제로 어느 파일을 쓰는지
  python -c "from database import engine; import os; print(engine.url); print(os.path.abspath(engine.url.database))"
  # 테이블의 실제 컬럼
  python -c "import sqlite3; c = sqlite3.connect('items.db'); print(c.execute('PRAGMA table_info(users)').fetchall())"
  # 코드에서 오타 일괄 검색
  grep -rn "hassed" --include="*.py" .
  ```
- **교훈**: DB 이상 증상이 나오면 **실제 파일 경로**와 **실제 컬럼**부터 확인

### 4. create_all은 기존 테이블을 고치지 않음

- 모델의 컬럼명을 고쳐도 이미 만들어진 DB의 테이블 구조는 그대로 남음
- 학습 단계에서는 `items.db`를 지우고 서버를 다시 켜서 새로 만듦
- 서버가 파일을 열고 있으면 Windows에서 `rm`이 `Device or resource busy`로 실패 → 서버를 먼저 종료
- 실무에서는 이 문제를 **마이그레이션 도구(Alembic)**로 해결 (나중에 배울 주제)

### 5. 터미널을 새로 열면 가상환경 활성화가 풀림

- `uvicorn: command not found`의 원인. 활성화는 **그 터미널 창에만** 적용됨
- 프롬프트에 `(환경이름)` 표시가 있는지 확인
- `pipenv run uvicorn main:app --reload`로 활성화 없이 실행 가능
- VS Code 인터프리터를 프로젝트 환경으로 선택해두면 자동 활성화

### 6. `sqlite3.connect()`는 파일이 없으면 새로 만든다

- 확인용 명령이 엉뚱한 곳에 **빈 DB 파일을 만들 수 있음**
- 읽기 전용으로 열면 파일이 없을 때 에러가 나서 안전함
  ```python
  sqlite3.connect('file:items.db?mode=ro', uri=True)
  ```

---
