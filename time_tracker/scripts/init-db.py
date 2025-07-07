#!/usr/bin/env python3
"""
Скрипт для инициализации базы данных
Используется в Docker контейнерах для создания таблиц
"""

import os
import sys

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.engine import create_tables
from database.models import Base

def init_database():
    """Инициализирует базу данных"""
    try:
        # Создаем директорию для данных, если её нет
        os.makedirs('/app/data', exist_ok=True)
        
        # Создаем таблицы
        create_tables()
        print("✅ База данных успешно инициализирована")
        
    except Exception as e:
        print(f"❌ Ошибка при инициализации базы данных: {e}")
        sys.exit(1)

if __name__ == "__main__":
    init_database() 