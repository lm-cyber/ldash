#!/bin/bash

# Скрипт для запуска Time Tracker в Docker

set -e

echo "🚀 Запуск Time Tracker..."

# Проверяем наличие .env файла
if [ ! -f .env ]; then
    echo "❌ Файл .env не найден!"
    echo "📝 Запустите первоначальную настройку:"
    echo "   ./scripts/setup.sh"
    exit 1
fi

# Создаем директорию для данных
mkdir -p data

# Собираем и запускаем контейнеры
echo "🔨 Сборка Docker образов..."
docker-compose build

echo "📊 Запуск сервисов..."
docker-compose up -d

echo "✅ Time Tracker запущен!"
echo ""
echo "📱 Telegram бот: запущен в фоне"
echo "🌐 Дашборд: http://localhost:8501"
echo ""
echo "📋 Полезные команды:"
echo "   docker-compose logs -f bot      # Логи бота"
echo "   docker-compose logs -f dashboard # Логи дашборда"
echo "   docker-compose down             # Остановить все сервисы"
echo "   docker-compose restart          # Перезапустить сервисы" 