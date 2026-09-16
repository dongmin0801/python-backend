from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}

# Path Parameter
@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id}

# Query Parameter
@app.get("/search")
def search_items(q: str = "", limit: int = 10):
    return {"query": q, "limit": limit}