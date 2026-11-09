from sqlalchemy import Column, Integer, String, Float, Boolean
from database import Base

class ItemModel(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index = True)
    name = Column(String, index=True)
    price = Column(Float)
    is_available = Column(Boolean, default=True)

class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
