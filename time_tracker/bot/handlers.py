from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from .states import Form
from database.models import TimeEntry
from database.engine import get_session, close_session
import os
from dotenv import load_dotenv

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
        "/add - Добавить новую запись о потраченном времени\n"
        "/cancel - Отменить текущую операцию"
    )

@router.message(Command("add"))
async def cmd_add(message: Message, state: FSMContext):
    """Обработчик команды /add"""
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет доступа к этому боту.")
        return
    
    await state.set_state(Form.waiting_for_activity_name)
    await message.answer("На какую задачу ты потратил(а) время?")

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
    
    # Сохраняем запись в базу данных
    session = get_session()
    try:
        time_entry = TimeEntry(
            user_id=message.from_user.id,
            activity_name=activity_name,
            duration_minutes=duration
        )
        session.add(time_entry)
        session.commit()
        
        await message.answer(
            f"✅ Запись добавлена!\n\n"
            f"Задача: {activity_name}\n"
            f"Время: {duration} минут"
        )
    except Exception as e:
        session.rollback()
        await message.answer("❌ Произошла ошибка при сохранении записи.")
        print(f"Error saving time entry: {e}")
    finally:
        close_session(session)
    
    # Очищаем состояние
    await state.clear() 