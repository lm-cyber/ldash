#!/usr/bin/env python3
"""
Генерация демонстрационных данных с различными паттернами активности
Создает данные, которые показывают разные возможности дашборда
"""

import os
import sys
import random
from datetime import datetime, timedelta

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.engine import get_session, create_tables
from database.models import TimeEntry, ActivityCategory

# Различные типы активностей для демонстрации
WORK_ACTIVITIES = [
    "Программирование",
    "Код-ревью", 
    "Встречи с командой",
    "Планирование задач",
    "Отладка кода",
    "Написание тестов",
    "Документирование",
    "Работа с API"
]

LEARNING_ACTIVITIES = [
    "Изучение новых технологий",
    "Чтение документации",
    "Просмотр обучающих видео",
    "Изучение алгоритмов",
    "Изучение фреймворков",
    "Изучение английского"
]

PERSONAL_ACTIVITIES = [
    "Физические упражнения",
    "Чтение книг",
    "Медитация",
    "Прогулки",
    "Хобби"
]

def create_demo_patterns(user_id=123456789):
    """Создает демонстрационные данные с различными паттернами"""
    
    print("🎭 Создание демонстрационных данных с паттернами...")
    
    create_tables()
    session = get_session()
    
    try:
        # Очищаем старые данные
        session.query(TimeEntry).delete()
        session.commit()
        
        entries_created = 0
        start_date = datetime.now() - timedelta(days=30)
        
        # Паттерн 1: Рабочие дни (пн-пт) - больше работы
        # Паттерн 2: Выходные - больше личного времени
        # Паттерн 3: Утренние часы - изучение
        # Паттерн 4: Дневные часы - работа
        # Паттерн 5: Вечерние часы - личное время
        
        current_date = start_date
        while current_date <= datetime.now():
            
            day_of_week = current_date.weekday()  # 0=пн, 6=вс
            
            # Определяем количество записей в зависимости от дня недели
            if day_of_week < 5:  # Рабочие дни
                daily_entries = random.randint(3, 6)
            else:  # Выходные
                daily_entries = random.randint(2, 4)
            
            for i in range(daily_entries):
                # Время в зависимости от типа активности
                if i == 0:  # Первая запись - утро (изучение)
                    hour = random.randint(7, 10)
                    activity = random.choice(LEARNING_ACTIVITIES)
                    duration = random.choice([30, 45, 60])
                elif i == 1 and day_of_week < 5:  # Вторая запись - работа
                    hour = random.randint(10, 17)
                    activity = random.choice(WORK_ACTIVITIES)
                    duration = random.choice([60, 90, 120])
                else:  # Остальные записи - смешанные
                    hour = random.randint(14, 22)
                    if day_of_week < 5:  # Рабочие дни
                        activity = random.choice(WORK_ACTIVITIES + LEARNING_ACTIVITIES)
                    else:  # Выходные
                        activity = random.choice(LEARNING_ACTIVITIES + PERSONAL_ACTIVITIES)
                    duration = random.choice([30, 45, 60, 90])
                
                minute = random.randint(0, 59)
                entry_time = current_date.replace(
                    hour=hour, 
                    minute=minute, 
                    second=random.randint(0, 59)
                )
                
                # Определяем категорию для активности
                if activity in WORK_ACTIVITIES:
                    category = ActivityCategory.WORK
                elif activity in LEARNING_ACTIVITIES:
                    category = ActivityCategory.STUDY
                else:
                    category = ActivityCategory.REST
                
                # Создаем запись
                time_entry = TimeEntry(
                    user_id=user_id,
                    activity_name=activity,
                    category=category,
                    duration_minutes=duration,
                    entry_date=entry_time
                )
                
                session.add(time_entry)
                entries_created += 1
            
            current_date += timedelta(days=1)
        
        session.commit()
        
        print(f"✅ Создано {entries_created} демонстрационных записей")
        print(f"📅 Период: {start_date.strftime('%d.%m.%Y')} - {datetime.now().strftime('%d.%m.%Y')}")
        
        # Показываем созданные паттерны
        show_demo_patterns(session)
        
    except Exception as e:
        session.rollback()
        print(f"❌ Ошибка: {e}")
    finally:
        session.close()

def show_demo_patterns(session):
    """Показывает созданные паттерны"""
    
    print("\n📊 Демонстрационные паттерны:")
    
    # Общая статистика
    total_entries = session.query(TimeEntry).count()
    total_time = sum([entry.duration_minutes for entry in session.query(TimeEntry).all()])
    
    print(f"   📝 Всего записей: {total_entries}")
    print(f"   ⏰ Общее время: {total_time//60}ч {total_time%60}мин")
    
    # Статистика по категориям
    work_time = sum([entry.duration_minutes for entry in session.query(TimeEntry).filter(
        TimeEntry.category == ActivityCategory.WORK
    ).all()])
    
    learning_time = sum([entry.duration_minutes for entry in session.query(TimeEntry).filter(
        TimeEntry.category == ActivityCategory.STUDY
    ).all()])
    
    personal_time = sum([entry.duration_minutes for entry in session.query(TimeEntry).filter(
        TimeEntry.category == ActivityCategory.REST
    ).all()])
    
    print(f"\n🏢 Рабочие активности: {work_time//60}ч {work_time%60}мин")
    print(f"📚 Изучение: {learning_time//60}ч {learning_time%60}мин")
    print(f"👤 Личное время: {personal_time//60}ч {personal_time%60}мин")
    
    # Топ активностей
    print(f"\n🏆 Топ-5 активностей:")
    activities = {}
    for entry in session.query(TimeEntry).all():
        activities[entry.activity_name] = activities.get(entry.activity_name, 0) + entry.duration_minutes
    
    sorted_activities = sorted(activities.items(), key=lambda x: x[1], reverse=True)[:5]
    for activity, time in sorted_activities:
        hours = time // 60
        minutes = time % 60
        time_str = f"{hours}ч {minutes}мин" if hours > 0 else f"{minutes}мин"
        print(f"   • {activity}: {time_str}")

if __name__ == "__main__":
    create_demo_patterns() 