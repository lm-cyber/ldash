import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
import os

from .handlers import router
from database.engine import create_tables

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)

async def main():
    """Основная функция запуска бота"""
    # Получаем токен бота из переменных окружения
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        print("❌ Ошибка: BOT_TOKEN не найден в переменных окружения")
        return
    
    # Создаем экземпляры бота и диспетчера
    bot = Bot(token=bot_token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Регистрируем роутер с обработчиками
    dp.include_router(router)
    
    # Создаем таблицы в базе данных
    try:
        create_tables()
        print("✅ База данных инициализирована")
    except Exception as e:
        print(f"❌ Ошибка при инициализации базы данных: {e}")
        print("💡 Убедитесь, что у вас есть права на создание директории 'data'")
        return
    
    print("🚀 Бот запускается...")
    
    try:
        # Запускаем бота
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Ошибка при запуске бота: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main()) 