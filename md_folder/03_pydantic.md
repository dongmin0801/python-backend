## Pydantic 모델 & POST 요청

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