from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from .states import Form
from database.models import TimeEntry, ActivityCategory
from database.engine import get_session, close_session
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import asyncio

# Загружаем переменные окружения
load_dotenv()

router = Router()

# Получаем ID администратора из переменных окружения
ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID'))

def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором"""
    return user_id == ADMIN_USER_ID

@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет доступа к этому боту.")
        return
    
    await message.answer(
        "Привет! Я бот для учета времени.\n\n"
        "Доступные команды:\n"
        "📝 /add - Добавить новую запись о потраченном времени\n"
        "📊 /stats - Статистика за сегодня\n"
        "🔔 /remind - Управление напоминаниями\n"
        "❌ /cancel - Отменить текущую операцию\n\n"
        "Категории активности:\n"
        "💼 Работа - профессиональная деятельность\n"
        "📚 Учеба - изучение и развитие\n"
        "😴 Отдых - личное время и восстановление"
    )

def get_category_keyboard():
    """Создает клавиатуру для выбора категории"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💼 Работа", callback_data="category_work"),
            InlineKeyboardButton(text="📚 Учеба", callback_data="category_study")
        ],
        [
            InlineKeyboardButton(text="😴 Отдых", callback_data="category_rest")
        ]
    ])
    return keyboard

@router.message(Command("add"))
async def cmd_add(message: Message, state: FSMContext):
    """Обработчик команды /add"""
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет доступа к этому боту.")
        return
    
    await state.set_state(Form.waiting_for_category)
    await message.answer(
        "Выберите категорию активности:",
        reply_markup=get_category_keyboard()
    )

@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """Обработчик команды /cancel"""
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет доступа к этому боту.")
        return
    
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нет активной операции для отмены.")
        return
    
    await state.clear()
    await message.answer("Операция отменена.")

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Обработчик команды /stats - показывает статистику за сегодня"""
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет доступа к этому боту.")
        return
    
    session = get_session()
    try:
        today = datetime.now().date()
        
        # Получаем записи за сегодня
        today_entries = session.query(TimeEntry).filter(
            TimeEntry.user_id == message.from_user.id,
            TimeEntry.entry_date >= today,
            TimeEntry.entry_date < today + timedelta(days=1)
        ).all()
        
        if not today_entries:
            await message.answer("📊 Сегодня еще нет записей о времени.")
            return
        
        # Группируем по категориям
        category_stats = {}
        total_time = 0
        
        for entry in today_entries:
            category = entry.category.value
            if category not in category_stats:
                category_stats[category] = {'time': 0, 'count': 0}
            category_stats[category]['time'] += entry.duration_minutes
            category_stats[category]['count'] += 1
            total_time += entry.duration_minutes
        
        # Формируем сообщение
        stats_text = f"📊 Статистика за сегодня ({today.strftime('%d.%m.%Y')}):\n\n"
        stats_text += f"⏰ Общее время: {total_time//60}ч {total_time%60}мин\n"
        stats_text += f"📝 Записей: {len(today_entries)}\n\n"
        
        category_emoji = {
            'work': '💼',
            'study': '📚', 
            'rest': '😴'
        }
        
        for category, stats in category_stats.items():
            emoji = category_emoji.get(category, '📊')
            time_str = f"{stats['time']//60}ч {stats['time']%60}мин" if stats['time'] >= 60 else f"{stats['time']}мин"
            stats_text += f"{emoji} {category.upper()}: {time_str} ({stats['count']} записей)\n"
        
        await message.answer(stats_text)
        
    except Exception as e:
        await message.answer("❌ Ошибка при получении статистики.")
        print(f"Error getting stats: {e}")
    finally:
        close_session(session)

@router.message(Command("remind"))
async def cmd_remind(message: Message):
    """Обработчик команды /remind - включает/выключает напоминания"""
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет доступа к этому боту.")
        return
    
    # Здесь можно добавить логику для управления напоминаниями
    await message.answer(
        "🔔 Управление напоминаниями:\n\n"
        "Напоминания будут приходить каждый день в 21:00\n"
        "для ввода данных о потраченном времени.\n\n"
        "Используйте /add для добавления записей."
    )

@router.callback_query(lambda c: c.data.startswith('category_'))
async def process_category_selection(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора категории"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет доступа к этому боту.")
        await state.clear()
        return
    
    # Извлекаем категорию из callback_data
    category_str = callback.data.split('_')[1]
    category_mapping = {
        'work': ActivityCategory.WORK,
        'study': ActivityCategory.STUDY,
        'rest': ActivityCategory.REST
    }
    
    category = category_mapping.get(category_str)
    if not category:
        await callback.answer("Неверная категория!")
        return
    
    # Сохраняем категорию
    await state.update_data(category=category)
    
    # Переходим к следующему состоянию
    await state.set_state(Form.waiting_for_activity_name)
    
    # Показываем примеры активностей для выбранной категории
    examples = {
        ActivityCategory.WORK: "💼 Примеры: Программирование, Встречи, Код-ревью, Планирование",
        ActivityCategory.STUDY: "📚 Примеры: Изучение технологий, Чтение документации, Курсы, Изучение английского",
        ActivityCategory.REST: "😴 Примеры: Физические упражнения, Чтение книг, Медитация, Хобби"
    }
    
    await callback.message.edit_text(
        f"Выбрана категория: {category.value.upper()}\n\n"
        f"{examples[category]}\n\n"
        f"На какую задачу ты потратил(а) время?"
    )

@router.message(Form.waiting_for_activity_name)
async def process_activity_name(message: Message, state: FSMContext):
    """Обработчик ввода названия активности"""
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет доступа к этому боту.")
        await state.clear()
        return
    
    # Сохраняем название активности
    await state.update_data(activity_name=message.text)
    
    # Переходим к следующему состоянию
    await state.set_state(Form.waiting_for_duration)
    await message.answer("Сколько минут это заняло?")

@router.message(Form.waiting_for_duration)
async def process_duration(message: Message, state: FSMContext):
    """Обработчик ввода продолжительности"""
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет доступа к этому боту.")
        await state.clear()
        return
    
    try:
        duration = int(message.text)
        if duration <= 0:
            await message.answer("Продолжительность должна быть положительным числом. Попробуйте еще раз.")
            return
    except ValueError:
        await message.answer("Пожалуйста, введите число минут. Попробуйте еще раз.")
        return
    
    # Получаем данные из состояния
    data = await state.get_data()
    activity_name = data.get('activity_name')
    category = data.get('category')
    
    # Сохраняем запись в базу данных
    session = get_session()
    try:
        time_entry = TimeEntry(
            user_id=message.from_user.id,
            activity_name=activity_name,
            category=category,
            duration_minutes=duration
        )
        session.add(time_entry)
        session.commit()
        
        category_emoji = {
            ActivityCategory.WORK: "💼",
            ActivityCategory.STUDY: "📚",
            ActivityCategory.REST: "😴"
        }
        
        await message.answer(
            f"✅ Запись добавлена!\n\n"
            f"{category_emoji[category]} Категория: {category.value.upper()}\n"
            f"📝 Задача: {activity_name}\n"
            f"⏰ Время: {duration} минут"
        )
    except Exception as e:
        session.rollback()
        await message.answer("❌ Произошла ошибка при сохранении записи.")
        print(f"Error saving time entry: {e}")
    finally:
        close_session(session)
    
    # Очищаем состояние
    await state.clear() 