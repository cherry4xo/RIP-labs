import asyncio
from decimal import Decimal
from sqlalchemy import select

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_db_session
from app.models import Service, ServiceStatus, ServiceAssessmentType, User


# --- Данные, которые мы хотим добавить ---
SERVICES_DATA = [
    {
        'title': 'Сканирование сетевого периметра',
        'description': 'Автоматизированный поиск открытых портов, известных уязвимостей и ошибок конфигурации на ваших внешних IP-адресах.',
        'price': Decimal('15000.00'),
        'assessment_type': ServiceAssessmentType.NETWORK_SCAN,
        'status': ServiceStatus.AVAILABLE,
        'image_url': '/static/images/services/network.png'
    },
    {
        'title': 'Пентест веб-приложения (базовый)',
        'description': 'Анализ вашего сайта на наличие уязвимостей из списка OWASP Top 10, включая SQL-инъекции, XSS и CSRF.',
        'price': Decimal('35000.00'),
        'assessment_type': ServiceAssessmentType.WEB_APP_PENTEST,
        'status': ServiceStatus.AVAILABLE,
        'image_url': '/static/images/services/pentest.png'
    },
    {
        'title': 'Аудит IT-инфраструктуры',
        'description': 'Комплексная проверка конфигурации серверов, сетевого оборудования и политик безопасности на соответствие лучшим практикам.',
        'price': Decimal('50000.00'),
        'assessment_type': ServiceAssessmentType.INFRASTRUCTURE_AUDIT,
        'status': ServiceStatus.AVAILABLE,
        'image_url': '/static/images/services/audit.png'
    },
    {
        'title': 'Анализ на фишинг (устаревшая)',
        'description': 'Эта услуга больше не предоставляется.',
        'price': Decimal('10000.00'),
        'assessment_type': ServiceAssessmentType.WEB_APP_PENTEST,
        'status': ServiceStatus.DELETED,
        'image_url': '/static/images/services/phishing.png'
    }
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


async def main():
    # Главная функция для запуска
    # await seed_services()
    # Сюда можно будет добавить seed_users(), seed_orders() и т.д.
    await seed_users()


if __name__ == "__main__":
    # Запускаем асинхронную функцию main
    asyncio.run(main())