from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .models import Base
import os

# Путь к файлу базы данных
DATABASE_URL = "sqlite:///data/tracker.db"

# Создание движка базы данных
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Необходимо для SQLite в многопоточных приложениях
)

# Создание фабрики сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Создает все таблицы в базе данных"""
    import os
    
    # Создаем директорию data, если её нет
    data_dir = os.path.join(os.getcwd(), 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"✅ Создана директория: {data_dir}")
    
    Base.metadata.create_all(bind=engine)

def get_session() -> Session:
    """Возвращает сессию базы данных"""
    return SessionLocal()

def close_session(session: Session):
    """Закрывает сессию базы данных"""
    session.close() 