from fastapi import FastAPI, Depends, HTTPException, RedirectResponse
from sqlalchemy.orm import Session
import random
import string

from database import Base, engine, SessionLocal
import database

# Создаём таблицы в БД
Base.metadata.create_all(bind=engine)

app = FastAPI()

# --- Вспомогательные функции ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def generate_short_url(length=6):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

# --- Модель URL ---
from sqlalchemy import Column, Integer, String
class URL(database.Base):
    __tablename__ = "urls"
    id = Column(Integer, primary_key=True)
    original_url = Column(String, index=True)
    short_url = Column(String, unique=True)

# --- Роуты ---
@app.post("/shorten")
async def shorten_url(original_url: str, db: Session = Depends(get_db)):
    existing = db.query(URL).filter(URL.original_url == original_url).first()
    if existing:
        return {"short_url": f"/{existing.short_url}"}

    short = generate_short_url()
    while db.query(URL).filter(URL.short_url == short).first():
        short = generate_short_url()

    db_url = URL(original_url=original_url, short_url=short)
    db.add(db_url)
    db.commit()
    db.refresh(db_url)

    return {"short_url": f"/{short}"}

@app.get("/{short_url}")
async def redirect_to_url(short_url: str, db: Session = Depends(get_db)):
    url = db.query(URL).filter(URL.short_url == short_url).first()
    if not url:
        raise HTTPException(status_code=404, detail="URL not found")
    return RedirectResponse(url.original_url)
