"""
Модуль для управления автоматическими напоминаниями
"""

import asyncio
from datetime import datetime, timedelta
from aiogram import Bot
from database.engine import get_session, close_session
from database.models import TimeEntry
import os
from dotenv import load_dotenv

load_dotenv()

class ReminderManager:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.admin_user_id = int(os.getenv('ADMIN_USER_ID'))
        self.reminder_hour = 21  # Время напоминания (21:00)
        self.reminder_minute = 0
        
    async def start_reminder_loop(self):
        """Запускает цикл напоминаний"""
        while True:
            try:
                await self.check_and_send_reminder()
                # Проверяем каждую минуту
                await asyncio.sleep(60)
            except Exception as e:
                print(f"Ошибка в цикле напоминаний: {e}")
                await asyncio.sleep(300)  # Ждем 5 минут при ошибке
    
    async def check_and_send_reminder(self):
        """Проверяет, нужно ли отправить напоминание"""
        now = datetime.now()
        
        # Проверяем, что сейчас время напоминания
        if now.hour == self.reminder_hour and now.minute == self.reminder_minute:
            await self.send_daily_reminder()
    
    async def send_daily_reminder(self):
        """Отправляет ежедневное напоминание"""
        try:
            session = get_session()
            
            # Проверяем, есть ли записи за сегодня
            today = datetime.now().date()
            today_entries = session.query(TimeEntry).filter(
                TimeEntry.user_id == self.admin_user_id,
                TimeEntry.entry_date >= today,
                TimeEntry.entry_date < today + timedelta(days=1)
            ).all()
            
            reminder_text = "🔔 Ежедневное напоминание!\n\n"
            
            if today_entries:
                total_time = sum(entry.duration_minutes for entry in today_entries)
                reminder_text += f"📊 Сегодня вы уже добавили {len(today_entries)} записей\n"
                reminder_text += f"⏰ Общее время: {total_time//60}ч {total_time%60}мин\n\n"
            else:
                reminder_text += "📝 Сегодня еще нет записей о времени.\n\n"
            
            reminder_text += (
                "💡 Не забудьте добавить записи о времени:\n"
                "📝 /add - Добавить новую запись\n"
                "📊 /stats - Посмотреть статистику за сегодня\n\n"
                "Категории:\n"
                "💼 Работа - профессиональная деятельность\n"
                "📚 Учеба - изучение и развитие\n"
                "😴 Отдых - личное время"
            )
            
            await self.bot.send_message(self.admin_user_id, reminder_text)
            
        except Exception as e:
            print(f"Ошибка при отправке напоминания: {e}")
        finally:
            close_session(session)
    
    async def send_manual_reminder(self):
        """Отправляет ручное напоминание (для тестирования)"""
        await self.send_daily_reminder() 