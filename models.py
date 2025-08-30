# filepath: models.py
import os
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, Integer, String, create_engine

Base = declarative_base()

# Render PostgreSQL URL environmentdan olinadi
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


class Registration(Base):
    __tablename__ = "registrations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_user_id = Column(Integer, nullable=False)
    username = Column(String(64))
    first_name = Column(String(64))
    last_name = Column(String(64))
    full_name = Column(String(128), nullable=False)
    age = Column(Integer, nullable=False)
    phone = Column(String(20), nullable=False)
    course = Column(String(64), nullable=False)
    level = Column(String(32))
    section = Column(String(64), nullable=False)

    def __repr__(self):
        return f"<Registration(full_name={self.full_name}, course={self.course})>"


# Agar jadval bo‘lmasa – yaratib qo‘yadi
Base.metadata.create_all(engine)
