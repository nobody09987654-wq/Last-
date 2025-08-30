# filepath: models.py
import os
from sqlalchemy import create_engine, Column, Integer, String, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# .env fayldan ma'lumotlarni yuklash
load_dotenv()

# DATABASE_URL ni olish (masalan: postgresql://user:password@host:port/dbname)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL topilmadi. Iltimos .env faylni tekshiring!")

# SQLAlchemy engine yaratish
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Session yaratish
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Baza uchun asosiy model klassi
Base = declarative_base()

# Registratsiya modeli
class Registration(Base):
    __tablename__ = "registrations"

    id = Column(Integer, primary_key=True, index=True)
    tg_user_id = Column(BigInteger, unique=True, nullable=False)  # Telegram foydalanuvchi ID
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    full_name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    phone = Column(String, nullable=False)
    course = Column(String, nullable=False)
    level = Column(String, nullable=False)
    section = Column(String, nullable=False)


# Jadval(lar)ni yaratish
def init_db():
    Base.metadata.create_all(bind=engine)
