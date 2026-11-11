## CRUD 전체 구현 (메모리 저장)

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