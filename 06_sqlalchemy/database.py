from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./items.db" #db의 주소, postgresql:// -> PostgreSQL, mysql:// -> MySQL

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False} #"check_same_thread": False -> SQLite를 사용할 떄만 쓰는 옵션
) #python과 실제 db파일 사이를 연결해주는 통로, sql명령을 실제로 주고받음

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) #세션을 만들어주는 공장

Base = declarative_base() #모든 테이블 클래스가 상속받는 부모 클래스, 상속 받은 클래스가 이건 db 테이블이다라고 인식함