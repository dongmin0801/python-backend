## Path Parameter vs Query Parameter

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