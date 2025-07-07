#!/bin/bash

# Скрипт для первоначальной настройки Time Tracker

set -e

echo "🔧 Настройка Time Tracker..."

# Создаем директорию для данных
echo "📁 Создание директории для данных..."
mkdir -p data

# Проверяем наличие .env файла
if [ ! -f .env ]; then
    echo "📝 Создание .env файла..."
    cp env_example.txt .env
    echo "⚠️  ВНИМАНИЕ: Отредактируйте файл .env и добавьте:"
    echo "   - BOT_TOKEN=ваш_токен_бота"
    echo "   - ADMIN_USER_ID=ваш_telegram_id"
    echo ""
    echo "💡 Как получить токен: @BotFather в Telegram"
    echo "💡 Как получить ID: @userinfobot в Telegram"
else
    echo "✅ Файл .env уже существует"
fi

# Проверяем права на директорию data
if [ ! -w data ]; then
    echo "🔐 Исправление прав доступа к директории data..."
    chmod 755 data
fi

echo "✅ Настройка завершена!"
echo ""
echo "🚀 Теперь вы можете запустить проект:"
echo "   python -m bot.main          # Запуск бота"
echo "   streamlit run dashboard.py  # Запуск дашборда"
echo "   ./scripts/start.sh          # Запуск с Docker" 