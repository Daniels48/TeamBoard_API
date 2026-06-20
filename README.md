# TeamBoard 📋

TeamBoard — веб-приложение для управления задачами и командной работы в стиле Kanban.

## Возможности

- Регистрация и аутентификация пользователей
- JWT-аутентификация (Access и Refresh токены)
- Управление пользовательскими сессиями
- Подтверждение электронной почты
- Восстановление пароля
- Создание и управление досками
- Создание колонок и карточек задач
- Перемещение карточек между колонками (Drag & Drop)
- RBAC (Admin / Owner / Editor / Viewer)
- Хранение активных сессий в Redis
- Структурированное логирование

## Технологии

- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Redis
- JWT
- Docker
- HTML / CSS / JavaScript

## 🚀 Запуск проекта

### 1️⃣ Клонировать репозиторий

```bash
git clone https://github.com/Daniels48/TeamBoard_API.git
```
```bash
cd TeamBoard_API
```


### 2️⃣ Создать файл `.env`

Скопируйте `.env.example` и переименуйте его в `.env`:

```bash
cp .env.example .env
```

После этого при необходимости измените значения переменных в файле `.env`.

### 3️⃣ Запустить контейнеры

**Linux / macOS:**

```bash
make up
```

**Windows:**
```bash
docker compose up -d --build
```

### 4️⃣ Применить миграции

**Linux / macOS:**

```bash
make upgrade
```

**Windows :**

```bash
docker compose exec api alembic -c app/infrastructure/db/alembic.ini upgrade head
```

### 5️⃣ Загрузить тестовые данные

**Linux / macOS:**

```bash
make seed
```

**Windows:**

```bash
docker compose exec api python -m scripts.seed
```

### 6️⃣ Открыть приложение

```text
http://localhost:8000
```

### 7️⃣ API документация

```text
http://localhost:8000/docs
```

## Тестовые пользователи

Пароль для всех пользователей:

```text
password123
```

| Email | Роль | Статус |
|---|---|---|
| `admin@example.com` | Admin | Подтверждён |
| `owner@example.com` | Владелец досок | Подтверждён |
| `editor@example.com` | Editor | Подтверждён |
| `viewer@example.com` | Viewer | Подтверждён |
| `unverified@example.com` | User | Не подтверждён |