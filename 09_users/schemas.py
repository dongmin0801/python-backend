from pydantic import BaseModel, Field, field_validator, EmailStr, ConfigDict

class ItemCreate(BaseModel):
    name:str = Field(min_length = 1, max_length=50)
    price: float = Field(gt=0)
    is_available: bool=True

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v:str) -> str:
        v=v.strip()
        if not v:
            raise ValueError("이름은 공백일 수 없습니다")
        return v

class ItemResponse(ItemCreate):
    id: int

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    email: EmailStr
    password: str=Field(min_length=8, max_length=128)

class UserResponse(BaseModel):
    id: int
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)