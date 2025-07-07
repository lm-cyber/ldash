#!/usr/bin/env python3
"""
Быстрая генерация тестовых данных для дашборда
Создает небольшой набор данных для быстрого тестирования
"""

import os
import sys
import random
from datetime import datetime, timedelta

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.engine import get_session, create_tables
from database.models import TimeEntry, ActivityCategory

# Простые активности для тестирования с категориями
ACTIVITIES_WITH_CATEGORIES = {
    "work": ["Программирование", "Встречи", "Отладка", "Тестирование", "Документирование", "Планирование"],
    "study": ["Изучение", "Чтение"],
    "rest": ["Отдых", "Упражнения"]
}

def quick_generate(days=7, user_id=123456789):
    """Быстрая генерация данных за указанное количество дней"""
    
    print(f"⚡ Быстрая генерация данных за {days} дней...")
    
    # Создаем таблицы
    create_tables()
    
    session = get_session()
    
    try:
        # Очищаем старые данные
        session.query(TimeEntry).delete()
        session.commit()
        print("🗑️  Старые данные очищены")
        
        entries_created = 0
        start_date = datetime.now() - timedelta(days=days)
        
        current_date = start_date
        while current_date <= datetime.now():
            
            # 1-3 записи в день
            daily_entries = random.randint(1, 3)
            
            for i in range(daily_entries):
                # Время в течение дня
                hour = random.randint(9, 21)
                minute = random.randint(0, 59)
                
                entry_time = current_date.replace(
                    hour=hour, 
                    minute=minute, 
                    second=random.randint(0, 59)
                )
                
                # Выбираем категорию и активность
                category = random.choice(['work', 'study', 'rest'])
                activity = random.choice(ACTIVITIES_WITH_CATEGORIES[category])
                
                # Продолжительность 30-120 минут
                duration = random.choice([30, 45, 60, 90, 120])
                
                # Определяем категорию для активности
                category_enum = ActivityCategory(category)
                
                # Создаем запись
                time_entry = TimeEntry(
                    user_id=user_id,
                    activity_name=activity,
                    category=category_enum,
                    duration_minutes=duration,
                    entry_date=entry_time
                )
                
                session.add(time_entry)
                entries_created += 1
            
            current_date += timedelta(days=1)
        
        session.commit()
        
        print(f"✅ Создано {entries_created} записей")
        print(f"📅 Период: {start_date.strftime('%d.%m.%Y')} - {datetime.now().strftime('%d.%m.%Y')}")
        
        # Быстрая статистика
        total_time = sum([entry.duration_minutes for entry in session.query(TimeEntry).all()])
        print(f"⏰ Общее время: {total_time//60}ч {total_time%60}мин")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Ошибка: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Быстрая генерация тестовых данных")
    parser.add_argument("--days", type=int, default=7, help="Количество дней (по умолчанию 7)")
    parser.add_argument("--user-id", type=int, default=123456789, help="Telegram User ID")
    
    args = parser.parse_args()
    
    quick_generate(args.days, args.user_id) 