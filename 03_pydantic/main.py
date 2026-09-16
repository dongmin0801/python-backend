from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float
    is_available: bool = True

@app.post("/items")
def create_item(item: Item):
    return {"received": item}