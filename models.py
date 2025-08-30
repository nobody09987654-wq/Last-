from sqlalchemy import Column, Integer, String, BigInteger, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()

class Registration(Base):
    __tablename__ = "registrations"

    id = Column(Integer, primary_key=True, index=True)
    tg_user_id = Column(BigInteger, unique=True, index=True)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    full_name = Column(String)
    age = Column(Integer)
    phone = Column(String)
    course = Column(String)
    level = Column(String)
    section = Column(String)


# Agar jadval bo‘lmasa, yaratib qo‘yadi
Base.metadata.create_all(bind=engine)
