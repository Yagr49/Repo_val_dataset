# MedForce Rework

Веб‑приложение для работы с медицинскими изображениями: загрузка кейсов, просмотр и модерация «посылок» (payloads) и, при необходимости, отправка принятых кейсов в CVAT для разметки.  
Используются Keycloak (аутентификация), Streamlit (frontend), PostgreSQL (база данных) и MinIO или S3‑совместимое хранилище для файлов.

## Требования

- Docker и Docker Compose
- (опционально) существующий Keycloak‑realm или использование готовых dev/prod‑realm из репозитория

## Быстрый старт

1. **Клонирование и настройка окружения**

   ```bash
   cd mf/medforce_rework
   cp .env.example .env
   ```

   Отредактируйте `.env`: как минимум задайте значения для `POSTGRES_PASSWORD`, `MINIO_ROOT_PASSWORD`, `KEYCLOAK_ADMIN_PASSWORD`.  
   Для локальной разработки остальные значения по умолчанию обычно подходят.

2. **Запуск стека**

   ```bash
   docker compose up --build
   ```

3. **Открытие приложения**

   - Frontend: http://localhost:9999 (или значение `FRONTEND_OUTER_PORT` из `.env`)
   - Keycloak: http://localhost:8080 (или `KC_OUTER_PORT`)

4. **Keycloak**

   При старте импортируется realm из `keycloak/dev/` (см. `compose.yml`).  
   Через Keycloak‑консоль создайте пользователей и назначьте им роли (например, `doctor_clinic1`, `doctor_clinic2`, `admin`).

## Переменные окружения

| Переменная | Описание |
|-----------|----------|
| **MinIO** | |
| `MINIO_HOST`, `MINIO_PORT` | Хост и порт MinIO (по умолчанию `minio`, `9000`) |
| `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD` | Администратор MinIO |
| **PostgreSQL** | |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | Пользователь, пароль и имя БД |
| `POSTGRES_HOST`, `POSTGRES_PORT` | Параметры подключения для сервиса‑listener (по умолчанию `127.0.0.1`, `5432`) |
| **Keycloak** | |
| `KC_OUTER_PORT`, `KC_INNER_PORT` | Порты Keycloak (наружный/внутренний) |
| `KEYCLOAK_ADMIN`, `KEYCLOAK_ADMIN_PASSWORD` | Учётная запись администратора Keycloak |
| `KEYCLOAK_REALM`, `KEYCLOAK_FRONTEND_CLIENT` | Имя realm и ID клиента для фронтенда |
| `KEYCLOAK_DIVIDED_STAGES_ROLE`, `KEYCLOAK_WITHOUT_SPLITTING_ROLE`, `KEYCLOAK_ADMIN_ROLE` | Названия ролей, которые использует приложение |
| **Frontend** | |
| `KEYCLOAK_URL` | Базовый URL Keycloak (например, `http://localhost:8080`) |
| `MINIO_URL` | URL MinIO для фронтенда (например, `http://minio:9000`) |
| `FRONTEND_OUTER_PORT`, `FRONTEND_INNER_PORT` | Внешний и внутренний порты фронтенда |
| `FRONTEND_FILE_ACCEPT` | Разрешённые расширения изображений (например, `png,jpg,jpeg`) |
| `DEV_MODE` | При установленном значении (например, `true`) используется MinIO; иначе используется S3‑адаптер |
| **S3 (когда `DEV_MODE` не задан)** | |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | Доступ к S3 |
| `AWS_ENDPOINT_URL` | Endpoint S3 |
| `S3_BUCKET`, `EXPORT_S3_BUCKET` | Бакеты для загрузок и экспортов |
| `SSE_CUSTOM_KEY`, `SSE_CUSTOM_ALGORITHM` | Необязательные параметры шифрования на стороне сервера (например, AES256) |
| **CVAT (опционально)** | |
| `CVAT_HOST`, `CVAT_USER`, `CVAT_PASSWORD` | Адрес и учётные данные CVAT для пайплайна разметки |
| **Email (опционально)** | |
| `EMAIL_ADDRESS`, `EMAIL_PASSWORD` | Учётные данные SMTP для уведомлений |
| `APP_BASE_URL` | Базовый URL приложения для ссылок в письмах (например, `http://localhost:9999`) |

## Структура проекта

- `frontend/` – приложение Streamlit (загрузка, верификация, архив, статистика и т.д.)
- `backend/` – сервисный слой и доступ к БД; используется фронтенд‑контейнером
- `database/` – `init.sql` PostgreSQL (схема и триггер для уведомлений CVAT)
- `keycloak/dev/`, `keycloak/prod/` – JSON‑дампы realm для Keycloak
- `s3_adapters/` – адаптеры для MinIO и VK Cloud S3
- `cvat_adapter/` – интеграция с API CVAT для задач разметки
- `schemas/` – общие Pydantic‑схемы

## Продакшн и свой Keycloak

- Можно использовать `keycloak/prod/` или собственный realm.  
  Для клиента, который использует фронтенд, настройте **Redirect URIs** и **Web origins** на реальный URL фронтенда (и, при необходимости, добавьте localhost для отладки).
- Не коммитьте `.env` и любые файлы с реальными секретами.  
  В репозитории лежит только `.env.example`, а `.env` добавлен в `.gitignore`.
