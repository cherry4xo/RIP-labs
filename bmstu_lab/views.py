from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from starlette import status

from bmstu.settings import templates

router = APIRouter()


SERVICES_DATA = [
    {
        "id": "1",
        "slug": "audit",
        "name": "Аудит IT-Инфраструктуры",
        "short_description": "Поиск уязвимостей, связанных с базами данных.",
        "full_description": "Полный автоматизированный анализ вашего приложения на предмет уязвимостей к SQL-инъекциям. Мы проверяем все входные точки данных, чтобы гарантировать безопасность вашей базы данных от несанкционированного доступа и манипуляций.",
        "price": "15 000 руб.",
        "image_key": "http://localhost:9000/main-lab-1/audit.png"
    },
    {
        "id": "2",
        "slug": "pentest",
        "name": "Пентест веб-приложения",
        "short_description": "Анализ на инъекции вредоносного кода в страницы.",
        "full_description": "Тестирование на XSS-уязвимости для предотвращения атак, которые могут скомпрометировать данные ваших пользователей. Анализ включает проверку как хранимых, так и отраженных XSS-атак.",
        "price": "12 500 руб.",
        "image_key": "http://localhost:9000/main-lab-1/pentest.png"
    },
    {
        "id": "3",
        "slug": "network",
        "name": "Сканирование сетевого периметра",
        "short_description": "Проверка на подделку межсайтовых запросов.",
        "full_description": "Аудит безопасности для защиты от атак типа 'Межсайтовая подделка запроса' (CSRF), которые заставляют пользователей выполнять нежелательные действия в приложении, в котором они аутентифицированы.",
        "price": "10 000 руб.",
        "image_key": "http://localhost:9000/main-lab-1/network.png"
    }
]


ORDER_DATA = {
    "id": "1",
    "status": "В обработке",
    "services": [
        {"id": "1", "slug": "audit", "comment": "Проверить в первую очередь"},
        {"id": "2", "slug": "pentest", "comment": "Базовый уровень проверки"}
    ],
    "total_price": "27 500 руб." # Поле результата вычислений
}


def find_service(service_id: str):
    for service in SERVICES_DATA:
        if service["id"] == service_id:
            return service
    return None


@router.get("/", name="services_list", status_code=status.HTTP_200_OK)
async def get_services_list(request: Request, query: Optional[str] = None):
    """Get services list HTML page

    Args:
        request (Request): user's FastAPI request
        query (Optional[str], optional): Search query. Defaults to None.

    Returns:
        TemplateResponse: HTML page render
    """
    services = SERVICES_DATA

    if query:
        services = [
            s for s in services
            if query.lower() in s["name"].lower()
        ]

    cart_item_count = len(ORDER_DATA["services"])

    return templates.TemplateResponse(
        "services_list.html", {
            "request": request,
            "services": services,
            "cart_item_count": cart_item_count,
            "search_query": query or ""
        }
    )


@router.get("/service/{service_id}", name="service_detail", status_code=status.HTTP_200_OK)
async def get_servie_detail(request: Request, service_id: str):
    """Get service detail HTML page

    Args:
        request (Request): user's FastAPI request
        service_slug (str): service plug name

    Raises:
        HTTPException: 404 if service plug does not exist

    Returns:
        TemplateResponse: HTML page render
    """
    service = find_service(service_id=service_id)
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    
    cart_item_count = len(ORDER_DATA["services"])

    return templates.TemplateResponse(
        "service_detail.html", {
            "request": request,
            "service": service,
            "cart_item_count": cart_item_count
        }
    )


@router.get("/order/{order_id}", name="order_detail", status_code=status.HTTP_200_OK)
async def get_order_detail(request: Request, order_id: str):
    """Get order detail HTML page

    Args:
        request (Request): user's FastAPI request
        order_id (str): order to render id

    Raises:
        HTTPException: 404 if order does not exist

    Returns:
        TemplateResponse: HTML page render
    """
    if order_id != ORDER_DATA["id"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    
    order_services = []
    for item in ORDER_DATA["services"]:
        service_data = find_service(item["id"])
        if service_data:
            order_services.append({
                "details": service_data,
                "comment": item["comment"],
            })

    cart_item_count = len(ORDER_DATA["services"])

    return templates.TemplateResponse(
        "order_detail.html", {
            "request": request,
            "order": ORDER_DATA,
            "order_services": order_services,
            "cart_item_count": cart_item_count
        }
    )