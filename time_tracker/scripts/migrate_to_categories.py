#!/usr/bin/env python3
"""
Миграция для добавления категорий к существующим записям
"""

import os
import sys

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.engine import get_session, create_tables
from database.models import TimeEntry, ActivityCategory

# Маппинг активностей к категориям
ACTIVITY_CATEGORY_MAPPING = {
    # Работа
    "программирование": ActivityCategory.WORK,
    "код-ревью": ActivityCategory.WORK,
    "встречи": ActivityCategory.WORK,
    "планирование": ActivityCategory.WORK,
    "отладка": ActivityCategory.WORK,
    "тестирование": ActivityCategory.WORK,
    "работа с базой данных": ActivityCategory.WORK,
    "оптимизация": ActivityCategory.WORK,
    "работа с api": ActivityCategory.WORK,
    "настройка": ActivityCategory.WORK,
    "документирование": ActivityCategory.WORK,
    "git": ActivityCategory.WORK,
    "deployment": ActivityCategory.WORK,
    "code review": ActivityCategory.WORK,
    "meetings": ActivityCategory.WORK,
    "debugging": ActivityCategory.WORK,
    "testing": ActivityCategory.WORK,
    "database": ActivityCategory.WORK,
    "optimization": ActivityCategory.WORK,
    "api": ActivityCategory.WORK,
    "setup": ActivityCategory.WORK,
    "documentation": ActivityCategory.WORK,
    
    # Учеба
    "изучение": ActivityCategory.STUDY,
    "чтение": ActivityCategory.STUDY,
    "английский": ActivityCategory.STUDY,
    "видео": ActivityCategory.STUDY,
    "алгоритмы": ActivityCategory.STUDY,
    "фреймворки": ActivityCategory.STUDY,
    "технологии": ActivityCategory.STUDY,
    "документация": ActivityCategory.STUDY,
    "курсы": ActivityCategory.STUDY,
    "learning": ActivityCategory.STUDY,
    "reading": ActivityCategory.STUDY,
    "english": ActivityCategory.STUDY,
    "video": ActivityCategory.STUDY,
    "algorithms": ActivityCategory.STUDY,
    "frameworks": ActivityCategory.STUDY,
    "technologies": ActivityCategory.STUDY,
    "courses": ActivityCategory.STUDY,
    
    # Отдых
    "упражнения": ActivityCategory.REST,
    "медитация": ActivityCategory.REST,
    "прогулки": ActivityCategory.REST,
    "хобби": ActivityCategory.REST,
    "отдых": ActivityCategory.REST,
    "книги": ActivityCategory.REST,
    "физические": ActivityCategory.REST,
    "exercise": ActivityCategory.REST,
    "meditation": ActivityCategory.REST,
    "walking": ActivityCategory.REST,
    "hobby": ActivityCategory.REST,
    "rest": ActivityCategory.REST,
    "books": ActivityCategory.REST,
    "physical": ActivityCategory.REST
}

def get_category_for_activity(activity_name):
    """Определяет категорию для активности по названию"""
    activity_lower = activity_name.lower()
    
    for keyword, category in ACTIVITY_CATEGORY_MAPPING.items():
        if keyword in activity_lower:
            return category
    
    # По умолчанию считаем работой
    return ActivityCategory.WORK

def migrate_to_categories():
    """Мигрирует существующие записи, добавляя категории"""
    
    print("🔄 Начинаем миграцию для добавления категорий...")
    
    # Создаем таблицы (если нужно)
    create_tables()
    
    session = get_session()
    
    try:
        # Получаем все записи без категорий
        entries_without_category = session.query(TimeEntry).filter(
            TimeEntry.category.is_(None)
        ).all()
        
        if not entries_without_category:
            print("✅ Все записи уже имеют категории")
            return
        
        print(f"📝 Найдено {len(entries_without_category)} записей без категорий")
        
        # Статистика по категориям
        category_stats = {
            ActivityCategory.WORK: 0,
            ActivityCategory.STUDY: 0,
            ActivityCategory.REST: 0
        }
        
        # Обновляем записи
        for entry in entries_without_category:
            category = get_category_for_activity(entry.activity_name)
            entry.category = category
            category_stats[category] += 1
        
        session.commit()
        
        print("✅ Миграция завершена успешно!")
        print("\n📊 Статистика распределения по категориям:")
        print(f"💼 Работа: {category_stats[ActivityCategory.WORK]} записей")
        print(f"📚 Учеба: {category_stats[ActivityCategory.STUDY]} записей")
        print(f"😴 Отдых: {category_stats[ActivityCategory.REST]} записей")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Ошибка при миграции: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    migrate_to_categories() 