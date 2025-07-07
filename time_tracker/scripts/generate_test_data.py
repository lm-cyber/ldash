#!/usr/bin/env python3
"""
Скрипт для генерации синтетических данных для тестирования дашборда
Создает разнообразные записи о времени с разными паттернами активности
"""

import os
import sys
import random
from datetime import datetime, timedelta
from faker import Faker

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.engine import get_session, create_tables
from database.models import TimeEntry, ActivityCategory

# Инициализируем Faker для генерации данных
fake = Faker('ru_RU')

# Список типичных задач/активностей с категориями
ACTIVITIES_WITH_CATEGORIES = {
    "work": [
        "Программирование",
        "Код-ревью",
        "Встречи с командой",
        "Планирование задач",
        "Отладка кода",
        "Написание тестов",
        "Работа с базой данных",
        "Оптимизация производительности",
        "Работа с API",
        "Настройка окружения",
        "Документирование кода",
        "Работа с Git"
    ],
    "study": [
        "Изучение новых технологий",
        "Чтение документации",
        "Изучение английского",
        "Просмотр обучающих видео",
        "Изучение алгоритмов",
        "Изучение фреймворков"
    ],
    "rest": [
        "Физические упражнения",
        "Чтение книг",
        "Медитация",
        "Прогулки",
        "Хобби",
        "Отдых"
    ]
}

def generate_synthetic_data(days_back=30, user_id=123456789):
    """
    Генерирует синтетические данные о времени
    
    Args:
        days_back (int): Количество дней назад для генерации данных
        user_id (int): ID пользователя Telegram
    """
    
    print(f"🎯 Генерация синтетических данных за последние {days_back} дней...")
    
    # Создаем таблицы, если их нет
    create_tables()
    
    session = get_session()
    
    try:
        # Проверяем, есть ли уже данные
        existing_count = session.query(TimeEntry).count()
        if existing_count > 0:
            print(f"⚠️  В базе уже есть {existing_count} записей")
            response = input("Хотите добавить новые записи? (y/n): ")
            if response.lower() != 'y':
                print("❌ Генерация отменена")
                return
        
        # Генерируем данные
        entries_created = 0
        start_date = datetime.now() - timedelta(days=days_back)
        
        current_date = start_date
        while current_date <= datetime.now():
            
            # Определяем количество записей на день (1-5)
            daily_entries = random.randint(1, 5)
            
            for _ in range(daily_entries):
                # Генерируем время записи в течение дня
                hour = random.randint(6, 23)  # 6:00 - 23:00
                minute = random.randint(0, 59)
                
                entry_time = current_date.replace(
                    hour=hour, 
                    minute=minute, 
                    second=random.randint(0, 59)
                )
                
                # Выбираем категорию с весами
                category = random.choices(
                    ['work', 'study', 'rest'],
                    weights=[0.5, 0.3, 0.2]  # Больше работы, меньше отдыха
                )[0]
                
                # Выбираем активность из выбранной категории
                activity = random.choice(ACTIVITIES_WITH_CATEGORIES[category])
                
                # Генерируем продолжительность (15-180 минут)
                duration = random.choices(
                    [15, 30, 45, 60, 90, 120, 150, 180],
                    weights=[0.2, 0.25, 0.2, 0.15, 0.1, 0.05, 0.03, 0.02]
                )[0]
                
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
        
        # Сохраняем все записи
        session.commit()
        
        print(f"✅ Создано {entries_created} записей")
        print(f"📅 Период: {start_date.strftime('%d.%m.%Y')} - {datetime.now().strftime('%d.%m.%Y')}")
        
        # Показываем статистику
        show_statistics(session)
        
    except Exception as e:
        session.rollback()
        print(f"❌ Ошибка при создании данных: {e}")
    finally:
        session.close()

def show_statistics(session):
    """Показывает статистику созданных данных"""
    
    print("\n📊 Статистика созданных данных:")
    
    # Общая статистика
    total_entries = session.query(TimeEntry).count()
    total_time = session.query(TimeEntry).with_entities(
        func.sum(TimeEntry.duration_minutes)
    ).scalar() or 0
    
    print(f"   📝 Всего записей: {total_entries}")
    print(f"   ⏰ Общее время: {total_time//60}ч {total_time%60}мин")
    
    # Статистика по задачам
    activities = session.query(
        TimeEntry.activity_name,
        func.count(TimeEntry.id).label('count'),
        func.sum(TimeEntry.duration_minutes).label('total_time')
    ).group_by(TimeEntry.activity_name).order_by(
        func.sum(TimeEntry.duration_minutes).desc()
    ).limit(5).all()
    
    print(f"   🏆 Топ-5 задач:")
    for activity, count, time in activities:
        hours = time // 60
        minutes = time % 60
        time_str = f"{hours}ч {minutes}мин" if hours > 0 else f"{minutes}мин"
        print(f"      • {activity}: {time_str} ({count} записей)")
    
    # Статистика по дням
    days_with_data = session.query(
        func.date(TimeEntry.entry_date)
    ).distinct().count()
    
    print(f"   📅 Дней с данными: {days_with_data}")

def clear_all_data():
    """Очищает все данные из базы"""
    
    print("🗑️  Очистка всех данных...")
    
    session = get_session()
    try:
        count = session.query(TimeEntry).count()
        session.query(TimeEntry).delete()
        session.commit()
        print(f"✅ Удалено {count} записей")
    except Exception as e:
        session.rollback()
        print(f"❌ Ошибка при удалении данных: {e}")
    finally:
        session.close()

def main():
    """Основная функция"""
    
    print("🎲 Генератор синтетических данных для Time Tracker")
    print("=" * 50)
    
    # Параметры генерации
    days_back = input("Введите количество дней для генерации (по умолчанию 30): ").strip()
    days_back = int(days_back) if days_back.isdigit() else 30
    
    user_id = input("Введите Telegram ID пользователя (по умолчанию 123456789): ").strip()
    user_id = int(user_id) if user_id.isdigit() else 123456789
    
    print(f"\n📋 Параметры генерации:")
    print(f"   📅 Дней назад: {days_back}")
    print(f"   👤 User ID: {user_id}")
    
    # Меню действий
    print(f"\n🔧 Выберите действие:")
    print("1. Создать новые данные")
    print("2. Очистить все данные")
    print("3. Показать статистику")
    print("4. Выход")
    
    choice = input("\nВаш выбор (1-4): ").strip()
    
    if choice == "1":
        generate_synthetic_data(days_back, user_id)
    elif choice == "2":
        clear_all_data()
    elif choice == "3":
        session = get_session()
        show_statistics(session)
        session.close()
    elif choice == "4":
        print("👋 До свидания!")
    else:
        print("❌ Неверный выбор")

if __name__ == "__main__":
    # Импортируем func для SQL запросов
    from sqlalchemy import func
    main() 