from datetime import date
from typing import Annotated, Optional

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette import status

from app import use_cases
from app.core.settings import templates
from app.core.database import AsyncSession, get_db_session
from app.repository import SqlAlchemyDatabaseRepo


DBSessionDep = Annotated[AsyncSession, Depends(get_db_session)]

def get_current_user_id() -> int:
    return 1

UserIdDep = Annotated[int, Depends(get_current_user_id)]

async def get_cart_count_for_template(db: DBSessionDep, user_id: UserIdDep) -> int:
    repo = SqlAlchemyDatabaseRepo(db)
    return await use_cases.get_current_cart_item_count(repo, user_id=user_id)

CartCountDep = Annotated[int, Depends(get_cart_count_for_template)]

async def get_current_cart_id(db: DBSessionDep, user_id: UserIdDep) -> Optional[int]:
    repo = SqlAlchemyDatabaseRepo(db)
    cart = await use_cases.view_user_cart(repo, user_id=user_id)
    return cart.id if cart else None

CartIdDep = Annotated[Optional[int], Depends(get_current_cart_id)]

router = APIRouter()


@router.get("/", name="services_list", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def services_list_view(
    request: Request,
    db: DBSessionDep,
    cart_item_count: CartCountDep,
    cart_id: CartIdDep,
    query: Optional[str] = None
):
    """Get services list HTML page

    Args:
        request (Request): user's FastAPI request
        db: DB repo DIP
        cart_item_count: current user cart item count DIP
        query (Optional[str], optional): Search query. Defaults to None.

    Returns:
        TemplateResponse: HTML page render
    """
    repo = SqlAlchemyDatabaseRepo(db)
    services = await use_cases.view_services_list(repo, query=query)
    
    return templates.TemplateResponse(
        "services_list.html", {
            "request": request,
            "services": services,
            "cart_item_count": cart_item_count,
            "cart_id": cart_id,
            "search_query": query or ""
        }
    )


@router.get("/order/{order_id}", name="order_detail", response_class=HTMLResponse)
async def order_detail_view(
    request: Request,
    order_id: int,
    db: DBSessionDep,
    user_id: UserIdDep,
    cart_item_count: CartCountDep,
):
    repo = SqlAlchemyDatabaseRepo(db)
    order = await repo.get_order_details(order_id)

    if not order or order.created_by != user_id:
        raise HTTPException(status_code=404, detail="Order not found")

    return templates.TemplateResponse(
        "order_detail.html", {
            "request": request,
            "order": order,
            "cart_item_count": cart_item_count,
            "cart_id": order.id
        }
    )


@router.get("/service/{service_id}", name="service_detail", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def service_detail_view(
    request: Request,
    service_id: int,
    db: DBSessionDep,
    cart_item_count: CartCountDep
):
    """Get service details HTML page render

    Args:
        request (Request): user's FastAPI request
        service_id (int): service to get description id
        db (DBSessionDep): DB repo DIP
        cart_item_count (CartCountDep): current user cart item count DIP

    Raises:
        HTTPException: 404 status code if service does not exists

    Returns:
        TemplateResponse: HTML page render
    """
    repo = SqlAlchemyDatabaseRepo(db)
    service = await use_cases.view_service_details(repo, service_id=service_id)
    
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    
    return templates.TemplateResponse(
        "service_detail.html", {
            "request": request,
            "service": service,
            "cart_item_count": cart_item_count
        }
    )


@router.get("/cart", name="cart_detail", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
async def cart_detail_view(
    request: Request,
    db: DBSessionDep,
    user_id: UserIdDep,
    cart_item_count: CartCountDep,
):
    """Get current draft cart view HTML page

    Args:
        request (Request): user's FastAPI request
        db (DBSessionDep): DB repo DIP
        user_id (UserIdDep): current user DIP
        cart_item_count (CartCountDep): current user cart item count DIP

    Returns:
        TemplateResponse: HTML page render
    """
    repo = SqlAlchemyDatabaseRepo(db)
    cart = await use_cases.view_user_cart(repo, user_id=user_id)
    
    return templates.TemplateResponse(
        "order_detail.html", {
            "request": request,
            "order": cart,
            "cart_item_count": cart_item_count
        }
    )


@router.post("/cart/add/{service_id}", name="add_to_cart", status_code=status.HTTP_200_OK)
async def add_to_cart_view(
    service_id: int,
    db: DBSessionDep,
    user_id: UserIdDep
):
    """HTTP add service to cart method

    Args:
        service_id (int): service to add id
        db (DBSessionDep): DB repo DIP
        user_id (UserIdDep): current user DIP

    Raises:
        HTTPException: 404 status code if service does not exist

    Returns:
        RedirectResponse: redirect to main page
    """
    repo = SqlAlchemyDatabaseRepo(db)
    try:
        await use_cases.add_service_to_cart(
            repo=repo, user_id=user_id, service_id=service_id
        )
    except use_cases.ServiceUnavailableError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    
    return RedirectResponse(
        url=router.url_path_for("services_list"),
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.post("/cart/delete", name="delete_cart")
async def delete_cart_view(
    db: DBSessionDep,
    user_id: UserIdDep
):
    """HTTP метод (POST): Логическое удаление корзины."""
    repo = SqlAlchemyDatabaseRepo(db)
    await use_cases.delete_user_cart(repo=repo, user_id=user_id)
    
    return RedirectResponse(
        url=router.url_path_for("services_list"),
        status_code=status.HTTP_303_SEE_OTHER
    )
