from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session

from database import engine, SessionLocal, Base
import models
import schemas

Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "Hello FastAPI"}

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
def read_item(item_id:int, db:Session = Depends(get_db)):
    db_item = db.query(models.ItemModel).filter(models.ItemModel.id==item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item

@app.put("/items/{item_id}", response_model=schemas.ItemResponse)
def update_item(item_id:int, item: schemas.ItemCreate, db:Session= Depends(get_db)):
    db_item = db.query(models.ItemModel).filter(models.ItemModel.id==item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    db_item.name = item.name
    db_item.price = item.price
    db_item.is_available = item.is_available
    
    db.commit()
    db.refresh(db_item)
    return db_item

@app.delete("/items/{item_id}")
def delete_item(item_id:int, db: Session = Depends(get_db)):
    db_item = db.query(models.ItemModel).filter(models.ItemModel.id==item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    
    db.delete(db_item)
    db.commit()
    return {"message": f"Item {item_id} deleted"}