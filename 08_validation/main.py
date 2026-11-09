from fastapi import FastAPI
from database import engine, Base
from routers import items

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(items.router)

@app.get("/")
def read_root():
    return {"message": "Hello FastAPI"}
