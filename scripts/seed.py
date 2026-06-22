import asyncio
from datetime import datetime, timezone

from sqlalchemy import select

from app.infrastructure.db.database import AsyncSessionLocal
from app.infrastructure.db.models import Board, BoardColumn, Card, User
from app.infrastructure.db.models.board_member import BoardMember, BoardRole
from app.infrastructure.db.models.user import UserRole
from app.modules.auth.security import PasswordService

PASSWORD = "password123"


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        existing_user = await db.scalar(select(User.id).limit(1))

        if existing_user is not None:
            print("Seed skipped: database already contains data")
            return

        password_hash = PasswordService.hash_password(PASSWORD)
        now = datetime.now(timezone.utc)

        admin = User(
            username="admin",
            email="admin@example.com",
            first_name="Admin",
            last_name="User",
            role=UserRole.ADMIN,
            hashed_password=password_hash,
            email_verified_at=now,
        )

        owner = User(
            username="owner",
            email="owner@example.com",
            first_name="Alex",
            last_name="Owner",
            role=UserRole.USER,
            hashed_password=password_hash,
            email_verified_at=now,
        )

        editor = User(
            username="editor",
            email="editor@example.com",
            first_name="Emma",
            last_name="Editor",
            role=UserRole.USER,
            hashed_password=password_hash,
            email_verified_at=now,
        )

        viewer = User(
            username="viewer",
            email="viewer@example.com",
            first_name="Victor",
            last_name="Viewer",
            role=UserRole.USER,
            hashed_password=password_hash,
            email_verified_at=now,
        )

        unverified = User(
            username="unverified",
            email="unverified@example.com",
            first_name="Una",
            last_name="Verified",
            role=UserRole.USER,
            hashed_password=password_hash,
        )

        db.add_all([admin, owner, editor, viewer, unverified])
        await db.flush()

        board_data = [
            {
                "title": "TeamBoard Development",
                "description": "Разработка и улучшение TeamBoard",
                "owner_id": owner.id,
                "columns": {
                    "Backlog": ["Добавить теги для карточек", "Настроить CI/CD"],
                    "To Do": ["Написать README", "Добавить тестовые данные"],
                    "In Progress": ["Реализовать уведомления"],
                    "Review": ["Проверить RBAC"],
                    "Done": ["Настроить Docker", "Добавить JWT"],
                },
            },
            {
                "title": "Frontend Improvements",
                "description": "Задачи по улучшению интерфейса",
                "owner_id": owner.id,
                "columns": {
                    "Ideas": ["Добавить dark mode", "Улучшить mobile layout"],
                    "To Do": ["Сделать страницу настроек"],
                    "In Progress": ["Улучшить drag and drop"],
                    "Done": ["Добавить страницу профиля"],
                },
            },
            {
                "title": "Marketing Campaign",
                "description": "Подготовка маркетинговой кампании",
                "owner_id": editor.id,
                "columns": {
                    "Ideas": ["Идеи для постов", "Список блогеров"],
                    "Planned": ["Подготовить контент-план"],
                    "In Progress": ["Написать пост о запуске"],
                    "Published": ["Создать страницу проекта"],
                },
            },
            {
                "title": "Roadmap 2026",
                "description": "Планы развития продукта",
                "owner_id": owner.id,
                "columns": {
                    "Planned": ["WebSocket обновления", "Файловые вложения"],
                    "In Progress": ["Система уведомлений"],
                    "Completed": ["Управление сессиями", "Email verification"],
                },
            },
            {
                "title": "Personal Tasks",
                "description": "Личные задачи владельца",
                "owner_id": owner.id,
                "columns": {
                    "To Do": ["Прочитать документацию FastAPI", "Обновить резюме"],
                    "Doing": ["Подготовить GitHub проект"],
                    "Done": ["Настроить PostgreSQL"],
                },
            },
            {
                "title": "Release Preparation",
                "description": "Подготовка первого релиза",
                "owner_id": admin.id,
                "columns": {
                    "Checklist": ["Проверить миграции", "Добавить seed script"],
                    "Testing": ["Проверить регистрацию", "Проверить reset password"],
                    "Ready": ["Настроить Docker Compose"],
                },
            },
        ]

        for board_info in board_data:
            board = Board(
                owner_id=board_info["owner_id"],
                title=board_info["title"],
                description=board_info["description"],
            )
            db.add(board)
            await db.flush()

            for user, role in [
                (editor, BoardRole.EDITOR),
                (viewer, BoardRole.VIEWER),
            ]:
                if user.id != board.owner_id:
                    db.add(
                        BoardMember(
                            board_id=board.id,
                            user_id=user.id,
                            role=role,
                        )
                    )

            for column_position, (column_title, cards) in enumerate(board_info["columns"].items()):
                column = BoardColumn(
                    board_id=board.id,
                    title=column_title,
                    position=column_position,
                )
                db.add(column)
                await db.flush()

                for card_position, card_title in enumerate(cards):
                    db.add(
                        Card(
                            column_id=column.id,
                            title=card_title,
                            description=f"Демо-задача: {card_title}",
                            position=card_position,
                        )
                    )

        await db.commit()

    print("Seed completed successfully")
    print()
    print("Test users:")
    print("admin@example.com      | password123 | admin")
    print("owner@example.com      | password123 | verified user")
    print("editor@example.com     | password123 | verified user")
    print("viewer@example.com     | password123 | verified user")
    print("unverified@example.com | password123 | unverified user")


if __name__ == "__main__":
    asyncio.run(seed())
