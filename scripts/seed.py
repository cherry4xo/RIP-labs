import asyncio
from decimal import Decimal
from sqlalchemy import select
from datetime import datetime

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.auth.security import get_password_hash
from app.core.database import get_db_session
from app.models import VulnerabilityAssessment, AssessmentStatus, VulnerabilityAssessmentType, User, AssessmentReport, ReportStatus


# --- Данные, которые мы хотим добавить ---
SERVICES_DATA = [
    {
        'title': 'Аудит IT-Инфраструктуры',
        'short_description': 'Проверка конфигурации серверов, сети.',
        'description': 'Комплексная проверка конфигурации серверов, сетевого оборудования и политик безопасности на соответствие лучшим практикам.',
        'price': Decimal('50000.00'),
        'assessment_type': VulnerabilityAssessmentType.INFRASTRUCTURE_AUDIT,
        'status': AssessmentStatus.AVAILABLE,
        'image_url': 'http://localhost:9000/main/audit.png',
        'impact_level': 3 # Критический ущерб
    },
    {
        'title': 'Пентест веб-приложения',
        'short_description': 'Анализ на OWASP Top 10.',
        'description': 'Анализ вашего сайта на наличие уязвимостей из списка OWASP Top 10, включая SQL-инъекции, XSS и CSRF.',
        'price': Decimal('35000.00'),
        'assessment_type': VulnerabilityAssessmentType.WEB_APP_PENTEST,
        'status': AssessmentStatus.AVAILABLE,
        'image_url': 'http://localhost:9000/main/pentest.png',
        'impact_level': 3 # Критический ущерб
    },
    {
        'title': 'Сканирование сетевого периметра',
        'short_description': 'Поиск открытых портов, уязвимостей.',
        'description': 'Комплексная проверка конфигурации серверов, сетевого оборудования и политик безопасности на соответствие лучшим практикам.',
        'price': Decimal('15000.00'),
        'assessment_type': VulnerabilityAssessmentType.NETWORK_SCAN,
        'status': AssessmentStatus.AVAILABLE,
        'image_url': 'http://localhost:9000/main/network.png',
        'impact_level': 2 # Средний ущерб
    },
    {
        'title': 'DDoS-атака (симуляция)',
        'description': 'Тестирование на отказ в обслуживании.', # Краткое описание
        'price': Decimal('25000.00'),
        'assessment_type': VulnerabilityAssessmentType.NETWORK_SCAN,
        'status': AssessmentStatus.AVAILABLE,
        'image_url': 'http://localhost:9000/main/ddos.png',
        'impact_level': 2 # Средний ущерб (влияет на доступность, но не на данные)
    },
    {
        'title': 'Аудит на Cross-Site Scripting (XSS)',
        'description': 'Проверка на внедрение вредоносных скриптов.', # Краткое описание
        'price': Decimal('18000.00'),
        'assessment_type': VulnerabilityAssessmentType.WEB_APP_PENTEST,
        'status': AssessmentStatus.AVAILABLE,
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
            # Проверяем, существует ли уже оценка уязвимости с таким названием
            stmt = select(VulnerabilityAssessment).where(VulnerabilityAssessment.title == service_data["title"])
            result = await session.execute(stmt)
            existing_service = result.scalars().first()

            if existing_service:
                print(f"Vulnerability assessment '{service_data['title']}' already exists, skipping.")
            else:
                # Если не существует, создаем и добавляем
                new_service = VulnerabilityAssessment(**service_data)
                session.add(new_service)
                print(f"Adding vulnerability assessment '{service_data['title']}'...")
        
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


async def seed_orders():
    print("Starting to seed orders...")
    async for session in get_db_session():
        # Получаем пользователя 'user'
        user_stmt = select(User).where(User.login == 'user')
        user = await session.scalar(user_stmt)
        
        if not user:
            print("User 'user' not found, skipping orders seeding.")
            return

        # Получаем все доступные услуги
        services_stmt = select(VulnerabilityAssessment).where(
            VulnerabilityAssessment.status == AssessmentStatus.AVAILABLE
        )
        services_result = await session.execute(services_stmt)
        services = services_result.scalars().all()
        
        if not services:
            print("No available services found, skipping orders seeding.")
            return

        # Создаем 3 заявки в разных статусах (кроме draft и deleted)
        orders_data = [
            {
                'status': ReportStatus.FORMED,
                'created_at': datetime.now(),
                'created_by': user.id,
                'target_system_info': 'Тестовая система 1',
                'risk_score': 7  # Исправлено на диапазон 1-9
            },
            {
                'status': ReportStatus.COMPLETED,
                'created_at': datetime.now(),
                'created_by': user.id,
                'formation_date': datetime.now(),
                'completion_date': datetime.now(),
                'target_system_info': 'Тестовая система 2',
                'risk_score': 9  # Исправлено на диапазон 1-9
            },
            {
                'status': ReportStatus.CANCELLED,
                'created_at': datetime.now(),
                'created_by': user.id,
                'target_system_info': 'Тестовая система 3',
                'risk_score': 3  # Исправлено на диапазон 1-9
            }
        ]

        from app.models import AssessmentComponents
        from random import sample, randint
        
        for i, order_data in enumerate(orders_data):
            # Проверяем, существует ли уже заявка с таким статусом для пользователя
            stmt = select(AssessmentReport).where(
                AssessmentReport.created_by == user.id,
                AssessmentReport.status == order_data["status"]
            )
            result = await session.execute(stmt)
            existing_order = result.scalars().first()

            if existing_order:
                print(f"Order with status '{order_data['status']}' for user 'user' already exists, skipping.")
            else:
                # Если не существует, создаем и добавляем
                new_order = AssessmentReport(**order_data)
                session.add(new_order)
                # Фиксируем изменения, чтобы получить ID новой заявки
                await session.flush()
                
                # Добавляем услуги к заявке (1-3 случайные услуги)
                num_services = randint(1, min(3, len(services)))
                selected_services = sample(services, num_services)
                
                for service in selected_services:
                    # Создаем запись AssessmentComponents
                    component = AssessmentComponents(
                        vulnerability_id=service.id,
                        report_id=new_order.id,
                        price_at_order_time=service.price
                    )
                    session.add(component)
                    
                print(f"Adding order with status '{order_data['status']}' for user 'user' with {num_services} services...")

        await session.commit()
        print("Orders seeding finished successfully.")


async def main():
    # Главная функция для запуска
    await seed_services()
    await seed_users()
    await seed_admin()
    await seed_orders()


if __name__ == "__main__":
    # Запускаем асинхронную функцию main
    asyncio.run(main())
