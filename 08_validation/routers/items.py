from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from database import SessionLocal
import models
import schemas

router = APIRouter(prefix="/items", tags=["items"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("", response_model=schemas.ItemResponse)
def create_item(item: schemas.ItemCreate, db: Session = Depends(get_db)):
    db_item = models.ItemModel(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.get("", response_model=list[schemas.ItemResponse])
def list_items(db:Session=Depends(get_db)):
    return db.query(models.ItemModel).all()

@router.get("/{item_id}", response_model=schemas.ItemResponse)
def read_item(item_id:int, db:Session=Depends(get_db)):
    db_item = db.query(models.ItemModel).filter(models.ItemModel.id==item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item Not Found")
    return db_item

@router.put("/{item_id}", response_model=schemas.ItemResponse)
def update_item(item_id:int, item:schemas.ItemCreate, db: Session=Depends(get_db)):
    db_item = db.query(models.ItemModel).filter(models.ItemModel.id==item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item Not Found")
    db_item.name = item.name
    db_item.price = item.price
    db_item.is_available = item.is_available
    db.commit()
    db.refresh(db_item)
    return db_item

@router.delete("/{item_id}")
def delete_item(item_id:int, db:Session = Depends(get_db)):
    db_item = db.query(models.ItemModel).filter(models.ItemModel.id==item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404,detail="Item Not Found")
    db.delete(db_item)
    db.commit()
    return {"message": f"Item {item_id} deleted"}