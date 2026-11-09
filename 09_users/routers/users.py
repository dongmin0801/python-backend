from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from database import get_db
from security import hash_password
import models
import schemas

router = APIRouter(prefix="/users", tags=["user"])

@router.post("", response_model=schemas.UserResponse, status_code=201)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.UserModel).filter(models.UserModel.email==user.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    db_user = models.UserModel(
        email = user.email,
        hashed_password = hash_password(user.password),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.get("/{user_id}", response_model=schemas.UserResponse)
def read_user(user_id:int, db:Session=Depends(get_db)):
    db_user = db.query(models.UserModel).filter(models.UserModel.id==user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not Found")
    return db_user

