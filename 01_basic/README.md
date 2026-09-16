## FastAPI 기본

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