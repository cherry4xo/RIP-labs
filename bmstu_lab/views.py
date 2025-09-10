from datetime import date

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from starlette import status

from bmstu.settings import templates

router = APIRouter()


mock_orders = [
        {
            "id": 1,
            "status": "В обработке",
            "start_date": "02.09.2025",
            "end_date": "07.09.2025",
            "created_date": "01.09.2025"
        },
        {
            "id": 2,
            "status": "Выполнено",
            "start_date": "03.09.2025",
            "end_date": "09.09.2025",
            "created_date": "02.09.2025"
        }
    ]


ANALYSIS_DATA = {
    "sql-injection": {
        "slug": "sql-injection",
        "title": "SQL Injection",
        "description": "Поиск уязвимостей, связанных с базами данных",
        "breadcrumbs": "Анализ/SQL Injection",
        "params": [
            {"label": "Критичность", "value": "Высокая"},
            {"label": "Время сканирования", "value": "~15 минут"},
            {"label": "Тип сканирования", "value": "Автоматизированный"},
            {"label": "Глубина проверки", "value": "Базовая"},
            {"label": "Соответствие", "value": "OWASP Top 10"},
        ]
    },
    "cross-site-scripting": {
        "slug": "cross-site-scripting",
        "title": "Cross-site Scripting",
        "description": "Анализ на инъекции вредоносного кода в страницы",
        "breadcrumbs": "Анализ/Cross-site Scripting",
        "params": [
            {"label": "Критичность", "value": "Высокая"},
            {"label": "Время сканирования", "value": "~10 минут"},
            {"label": "Тип сканирования", "value": "Автоматизированный"},
            {"label": "Глубина проверки", "value": "Стандартная"},
            {"label": "Соответствие", "value": "OWASP Top 10"},
        ]
    },
    "csrf": {
        "slug": "csrf",
        "title": "CSRF",
        "description": "Проверка на подделку межсайтовых запросов",
        "breadcrumbs": "Анализ/CSRF",
        "params": [
            {"label": "Критичность", "value": "Средняя"},
            {"label": "Время сканирования", "value": "~5 минут"},
            {"label": "Тип сканирования", "value": "Автоматизированный"},
            {"label": "Глубина проверки", "value": "Базовая"},
            {"label": "Соответствие", "value": "OWASP Top 10"},
        ]
    }
}


@router.get("/", name="home", status_code=status.HTTP_200_OK)
async def get_home_page(request: Request):
    """Renders app home page

    Args:
        request (Request): FastAPI user's request

    Returns:
        TemplateResponse: HTML page render
    """
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/analysis", name="analysis_list", status_code=status.HTTP_200_OK)
async def get_analysis_list(request: Request):
    """Get all analysis methods list page

    Args:
        request (Request): FastAPI user's request

    Returns:
        TemplateResponse: HTML page render
    """
    return templates.TemplateResponse(
        "analysis_list.html",
        {
            "request": request,
            "analyses": list(ANALYSIS_DATA.values())
        }
    )


@router.get("/cart", name="cart", status_code=status.HTTP_200_OK)
async def get_cart(request: Request):
    """
    Рендерит страницу корзины с товарами.
    В реальном приложении данные о составе корзины будут браться из сессии пользователя или БД.
    """
    cart_slugs = {
        "sql-injection": {"quantity": 1},
        "cross-site-scripting": {"quantity": 2},
    }

    mock_cart_items = []
    for slug, data in cart_slugs.items():
        analysis_data = ANALYSIS_DATA.get(slug)
        if analysis_data:
            mock_cart_items.append({
                "analysis": analysis_data,
                "quantity": data["quantity"]
            })
    
    if not mock_cart_items:
        return templates.TemplateResponse("cart_empty.html", {"request": request})

    return templates.TemplateResponse(
        "cart.html",
        {
            "request": request,
            "cart_items": mock_cart_items
        }
    )


@router.get("/analysis/{analysis_slug}", name="analysis_detail", status_code=status.HTTP_200_OK)
async def get_analysis_detail(request: Request, analysis_slug: str):
    """Get page with single analysis method description in details

    Args:
        request (Request): FastAPI user's request
        analysis_slug (str): Analysis method slug name

    Raises:
        HTTPException: 404 status code if analysis method with slug name does not exists

    Returns:
        TemplateResponse: HTML page render
    """
    analysis = ANALYSIS_DATA.get(analysis_slug)

    if not analysis:
        raise HTTPException(status_code=404, detail="Анализ не найден")

    return templates.TemplateResponse(
        "analysis_detail.html",
        {
            "request": request,
            "analysis": analysis
        }
    )


@router.get("/cart", name="cart")
async def get_cart(request: Request):
    """Get empty card page

    Args:
        request (Request): FastAPI user's request

    Returns:
        TemplateResponse: HTML page render
    """
    return templates.TemplateResponse("cart_empty.html", {"request": request})