# Tarot Telegram Bot

Телеграм-бот для гаданий на старших арканах Таро. Используется `aiogram` и PostgreSQL через `SQLAlchemy`.

## Возможности
- До 10 предсказаний в сутки на пользователя.
- Индивидуальные тексты для мужчин и женщин (по 4 на каждый из 22 старших арканов).
- Обращение к пользователю по Telegram-имени, при его отсутствии — "незнакомец"/"незнакомка" в зависимости от пола.

## Настройка окружения
1. Подготовьте переменные окружения:
   - `BOT_TOKEN` — токен бота от BotFather (обязателен).
   - `DATABASE_URL` — строка подключения к базе. По умолчанию: `postgresql+asyncpg://postgres:postgres@localhost:5432/tarobot`.
   - `DEBUG` — установите в `true`, чтобы включить детализированное логирование.
2. (Локально) установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

## Запуск
### Локально
```bash
python -m app.bot
```
Бот создаст необходимые таблицы автоматически.

### Через Docker Compose
1. Создайте файл `.env` рядом с `docker-compose.yml` и задайте хотя бы токен бота:
   ```env
   BOT_TOKEN=ваш_токен
   ```
   При желании можно переопределить `DATABASE_URL`, `DAYLIGHT_START_HOUR` и `DAYLIGHT_END_HOUR`.
2. Соберите и запустите контейнеры:
   ```bash
   docker-compose up -d --build
   ```
   Сервис базы данных доступен внутри сети Compose по адресу `db:5432` с пользователем/паролем `postgres/postgres` и базой `tarobot`.

## Обслуживание базы данных
- Очистка и реинициализация схемы (для дебага):
  ```bash
  python scripts/reset_db.py
  ```
  или из Docker Compose:
  ```bash
  docker-compose run --rm bot python scripts/reset_db.py
  ```
  Скрипт удаляет все таблицы и создаёт их заново.

- Бэкап базы данных (использует `pg_dump`, он установлен в Docker-образе бота):
  ```bash
  python scripts/backup_db.py
  ```
  Можно указать путь сохранения: `python scripts/backup_db.py -o backups/custom.dump`. В среде Docker Compose запускайте через `docker-compose run --rm bot python scripts/backup_db.py`. По умолчанию дампы складываются в каталог `backups/` и игнорируются Git.

## Основные команды
- `/start` — регистрация и выбор пола. После выбора пола предсказания запрашиваются через инлайн-кнопку.
