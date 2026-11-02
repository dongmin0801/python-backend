from pydantic import BaseModel

class ItemCreate(BaseModel):
    name:str
    price:float
    is_available:bool = True

class ItemResponse(ItemCreate):
    id:int

    class Config:
        from_attributes = True
        