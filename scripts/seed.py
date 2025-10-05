import asyncio
from decimal import Decimal
from sqlalchemy import select

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.auth.security import get_password_hash
from app.core.database import get_db_session
from app.models import Service, ServiceStatus, ServiceAssessmentType, User


# --- Данные, которые мы хотим добавить ---
SERVICES_DATA = [
    {
        'title': 'Аудит IT-Инфраструктуры',
        'short_description': 'Проверка конфигурации серверов, сети.',
        'description': 'Комплексная проверка конфигурации серверов, сетевого оборудования и политик безопасности на соответствие лучшим практикам.',
        'price': Decimal('50000.00'),
        'assessment_type': ServiceAssessmentType.INFRASTRUCTURE_AUDIT,
        'status': ServiceStatus.AVAILABLE,
        'image_url': 'http://localhost:9000/main/audit.png',
        'impact_level': 3 # Критический ущерб
    },
    {
        'title': 'Пентест веб-приложения',
        'short_description': 'Анализ на OWASP Top 10.',
        'description': 'Анализ вашего сайта на наличие уязвимостей из списка OWASP Top 10, включая SQL-инъекции, XSS и CSRF.',
        'price': Decimal('35000.00'),
        'assessment_type': ServiceAssessmentType.WEB_APP_PENTEST,
        'status': ServiceStatus.AVAILABLE,
        'image_url': 'http://localhost:9000/main/pentest.png',
        'impact_level': 3 # Критический ущерб
    },
    {
        'title': 'Сканирование сетевого периметра',
        'short_description': 'Поиск открытых портов, уязвимостей.',
        'description': 'Комплексная проверка конфигурации серверов, сетевого оборудования и политик безопасности на соответствие лучшим практикам.',
        'price': Decimal('15000.00'),
        'assessment_type': ServiceAssessmentType.NETWORK_SCAN,
        'status': ServiceStatus.AVAILABLE,
        'image_url': 'http://localhost:9000/main/network.png',
        'impact_level': 2 # Средний ущерб
    },
    {
        'title': 'DDoS-атака (симуляция)',
        'description': 'Тестирование на отказ в обслуживании.', # Краткое описание
        'price': Decimal('25000.00'),
        'assessment_type': ServiceAssessmentType.NETWORK_SCAN,
        'status': ServiceStatus.AVAILABLE,
        'image_url': 'http://localhost:9000/main/ddos.png',
        'impact_level': 2 # Средний ущерб (влияет на доступность, но не на данные)
    },
    {
        'title': 'Аудит на Cross-Site Scripting (XSS)',
        'description': 'Проверка на внедрение вредоносных скриптов.', # Краткое описание
        'price': Decimal('18000.00'),
        'assessment_type': ServiceAssessmentType.WEB_APP_PENTEST,
        'status': ServiceStatus.AVAILABLE,
        'image_url': 'http://localhost:9000/main/xss.png',
        'impact_level': 2 # Средний ущерб (может вести к краже сессий пользователей)
    },
]


def simple_hash(password: str) -> str:
    """Это не безопасно! Только для демонстрации."""
    return f"hashed_{password}_salt"


async def seed_services():
    print("Starting to seed services...")
    # Используем генератор сессий из вашего приложения
    async for session in get_db_session():
        for service_data in SERVICES_DATA:
            # Проверяем, существует ли уже услуга с таким названием
            stmt = select(Service).where(Service.title == service_data["title"])
            result = await session.execute(stmt)
            existing_service = result.scalars().first()

            if existing_service:
                print(f"Service '{service_data['title']}' already exists, skipping.")
            else:
                # Если не существует, создаем и добавляем
                new_service = Service(**service_data)
                session.add(new_service)
                print(f"Adding service '{service_data['title']}'...")
        
        await session.commit()
        print("Services seeding finished successfully.")


async def seed_users():
    print("Starting to seed users...")
    async for session in get_db_session():
        # Проверяем, существует ли пользователь с логином 'user'
        stmt = select(User).where(User.login == 'user')
        existing_user = await session.scalar(stmt)

        if existing_user:
            print("Default user 'user' already exists, skipping.")
        else:
            # Создаем нового пользователя
            # Важно: ID будет присвоен автоматически базой данных (serial),
            # и он будет равен 1, если это первая запись в таблице.
            new_user = User(
                login='user',
                password_hash=simple_hash('password'),
                is_moderator=False
            )
            session.add(new_user)
            await session.commit() # Коммитим сразу, чтобы получить ID
            print(f"Added default user 'user' with ID={new_user.id} and password='password'.")

    print("Users seeding finished.")


async def seed_admin():
    print("Starting to seed admins...")
    async for session in get_db_session():
        # Проверяем, существует ли пользователь с логином 'user'
        stmt = select(User).where(User.login == 'admin')
        existing_user = await session.scalar(stmt)

        if existing_user:
            print("Default user 'admin' already exists, skipping.")
        else:
            # Создаем нового пользователя
            # Важно: ID будет присвоен автоматически базой данных (serial),
            # и он будет равен 1, если это первая запись в таблице.
            new_user = User(
                login='admin',
                password_hash=get_password_hash("password"),
                is_moderator=True
            )
            session.add(new_user)
            await session.commit() # Коммитим сразу, чтобы получить ID
            print(f"Added default admin 'admin' with ID={new_user.id} and password='password'.")

    print("Admins seeding finished.")


async def main():
    # Главная функция для запуска
    # await seed_services()
    # await seed_users()
    await seed_admin()


if __name__ == "__main__":
    # Запускаем асинхронную функцию main
    asyncio.run(main())