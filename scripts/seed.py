import asyncio
from decimal import Decimal
from sqlalchemy import select

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_db_session
from app.models import Service, ServiceStatus, ServiceAssessmentType


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


async def main():
    # Главная функция для запуска
    await seed_services()
    # Сюда можно будет добавить seed_users(), seed_orders() и т.д.


if __name__ == "__main__":
    # Запускаем асинхронную функцию main
    asyncio.run(main())