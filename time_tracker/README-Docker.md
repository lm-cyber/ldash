# Time Tracker - Docker инструкции

## Быстрый запуск с Docker

### Предварительные требования

1. **Установите Docker и Docker Compose:**
   - [Docker Desktop](https://www.docker.com/products/docker-desktop) (включает Docker Compose)
   - Или отдельно: [Docker](https://docs.docker.com/get-docker/) + [Docker Compose](https://docs.docker.com/compose/install/)

2. **Настройте переменные окружения:**
   ```bash
   cp env_example.txt .env
   # Отредактируйте .env файл, добавив ваш токен бота и Telegram ID
   ```

### Запуск

#### Вариант 1: Автоматический запуск
```bash
./scripts/start.sh
```

#### Вариант 2: Ручной запуск
```bash
# Создайте директорию для данных
mkdir -p data

# Соберите и запустите контейнеры
docker-compose up -d

# Проверьте статус
docker-compose ps
```

### Доступ к сервисам

- **🌐 Дашборд:** http://localhost:8501
- **📱 Telegram бот:** Работает в фоне

### Управление контейнерами

```bash
# Просмотр логов
docker-compose logs -f bot        # Логи бота
docker-compose logs -f dashboard  # Логи дашборда

# Остановка
docker-compose down

# Перезапуск
docker-compose restart

# Обновление (после изменений в коде)
docker-compose up -d --build

# Просмотр статуса
docker-compose ps
```

## Структура Docker

### Сервисы

1. **bot** - Telegram бот
   - Контейнер: `time-tracker-bot`
   - Команда: `python -m bot.main`
   - Автоперезапуск: `unless-stopped`

2. **dashboard** - Streamlit дашборд
   - Контейнер: `time-tracker-dashboard`
   - Команда: `streamlit run dashboard.py`
   - Порт: `8501:8501`
   - Зависит от: `bot`

### Тома (Volumes)

- `./data:/app/data` - База данных SQLite
- `./.env:/app/.env:ro` - Переменные окружения (только чтение)

### Сети

- `time-tracker-network` - Изолированная сеть для сервисов

## Разработка с Docker

### Режим разработки

Для разработки с автоматической перезагрузкой кода:

```bash
# Активируйте режим разработки
cp docker-compose.override.yml.example docker-compose.override.yml

# Запустите с монтированием кода
docker-compose up -d
```

### Отладка

```bash
# Подключение к контейнеру бота
docker-compose exec bot bash

# Подключение к контейнеру дашборда
docker-compose exec dashboard bash

# Просмотр логов в реальном времени
docker-compose logs -f
```

### Тестирование изменений

```bash
# Пересборка после изменений в коде
docker-compose up -d --build

# Или перезапуск конкретного сервиса
docker-compose restart bot
docker-compose restart dashboard
```

## Безопасность

### Переменные окружения

- Файл `.env` монтируется как read-only
- Чувствительные данные не попадают в Docker образ
- Токен бота и Telegram ID хранятся в `.env`

### Пользователь в контейнере

- Приложение запускается от пользователя `appuser` (UID 1000)
- Не root пользователь для безопасности

### Сетевая изоляция

- Сервисы изолированы в отдельной сети
- Только дашборд доступен извне (порт 8501)

## Резервное копирование

### База данных

```bash
# Создание резервной копии
docker-compose exec dashboard sqlite3 /app/data/tracker.db ".backup /app/data/backup_$(date +%Y%m%d_%H%M%S).db"

# Восстановление из резервной копии
docker-compose exec dashboard sqlite3 /app/data/tracker.db ".restore /app/data/backup_YYYYMMDD_HHMMSS.db"
```

### Полное резервное копирование

```bash
# Архивирование всей директории data
tar -czf backup_$(date +%Y%m%d_%H%M%S).tar.gz data/
```

## Мониторинг

### Логи

```bash
# Все логи
docker-compose logs

# Логи с временными метками
docker-compose logs -t

# Логи в реальном времени
docker-compose logs -f

# Логи за последние 100 строк
docker-compose logs --tail=100
```

### Статистика контейнеров

```bash
# Использование ресурсов
docker stats

# Информация о контейнерах
docker-compose ps
```

## Устранение неполадок

### Проблемы с запуском

1. **Порт 8501 занят:**
   ```bash
   # Измените порт в docker-compose.yml
   ports:
     - "8502:8501"  # Используйте порт 8502
   ```

2. **Ошибки с правами доступа:**
   ```bash
   # Исправьте права на директорию data
   sudo chown -R $USER:$USER data/
   ```

3. **Проблемы с .env файлом:**
   ```bash
   # Проверьте синтаксис
   cat .env
   # Убедитесь, что нет лишних пробелов
   ```

### Очистка

```bash
# Удаление всех контейнеров и образов
docker-compose down --rmi all --volumes

# Очистка неиспользуемых ресурсов
docker system prune -a
```

## Производительность

### Оптимизация

- Используется Python 3.11-slim образ для меньшего размера
- Многоэтапная сборка для кэширования слоев
- Кэширование данных в Streamlit (`@st.cache_data`)

### Масштабирование

Для продакшена рекомендуется:
- Использовать внешнюю базу данных (PostgreSQL/MySQL)
- Настроить reverse proxy (nginx)
- Добавить мониторинг (Prometheus/Grafana)
- Настроить логирование в файлы 