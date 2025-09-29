# app/api/orders.py

from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from app import domains
from app.use_cases import order as order_use_cases
from app.auth.dependencies import CurrentUserDep, ModeratorDep
from app.core.database import DBSessionDep
from app.repository import SqlAlchemyDatabaseRepo
from app.interfaces import OrderNotFoundError

router = APIRouter(tags=["Orders & Cart"])

@router.get("/cart/info", response_model=domains.CartInfo)
async def get_cart_info(user: CurrentUserDep, db: DBSessionDep):
    """Получение ID и количества услуг в корзине текущего пользователя."""
    repo = SqlAlchemyDatabaseRepo(db)
    draft_order = await repo.get_draft_order_by_user_id(user.id)
    if not draft_order:
        return domains.CartInfo(order_id=-1, item_count=0)
    count = await repo.get_cart_item_count(user.id)
    return domains.CartInfo(order_id=draft_order.id, item_count=count)

@router.post("/cart/services", response_model=domains.OrderDetails)
async def add_to_cart(item: domains.CartItemAdd, user: CurrentUserDep, db: DBSessionDep):
    """Добавление услуги в корзину (создает корзину, если ее нет)."""
    repo = SqlAlchemyDatabaseRepo(db)
    await order_use_cases.add_service_to_cart(repo, user.id, item.service_id)
    await db.commit()
    draft_order = await repo.get_draft_order_by_user_id(user.id)
    return await repo.get_full_order_details(draft_order.id)

@router.delete("/cart/services/{service_id}", response_model=domains.OrderDetails)
async def remove_from_cart(service_id: int, user: CurrentUserDep, db: DBSessionDep):
    """Удаление услуги из корзины."""
    repo = SqlAlchemyDatabaseRepo(db)
    draft_order = await repo.get_draft_order_by_user_id(user.id)
    if not draft_order:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    deleted = await repo.delete_service_from_order(draft_order.id, service_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Service not found in cart")
    
    await db.commit()
    return await repo.get_full_order_details(draft_order.id)

@router.put("/cart/services/{service_id}", response_model=domains.OrderDetails)
async def update_cart_item(service_id: int, item_data: domains.CartItemUpdate, user: CurrentUserDep, db: DBSessionDep):
    """Изменение полей м-м (уровня защиты, комментария) для услуги в корзине."""
    repo = SqlAlchemyDatabaseRepo(db)
    draft_order = await repo.get_draft_order_by_user_id(user.id)
    if not draft_order:
        raise HTTPException(status_code=404, detail="Cart not found")
        
    await repo.update_association(draft_order.id, service_id, **item_data.model_dump())
    await db.commit()
    return await repo.get_full_order_details(draft_order.id)

@router.get("/orders", response_model=List[domains.OrderSummary])
async def get_orders(
    db: DBSessionDep,
    status: Optional[domains.OrderStatus] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
):
    """Получение списка оформленных заявок с фильтрацией."""
    repo = SqlAlchemyDatabaseRepo(db)
    return await repo.get_orders_with_filters(status, date_from, date_to)

@router.get("/orders/{order_id}", response_model=domains.OrderDetails)
async def get_order(order_id: int, user: CurrentUserDep, db: DBSessionDep):
    """Получение детальной информации о заявке."""
    repo = SqlAlchemyDatabaseRepo(db)
    order = await repo.get_full_order_details(order_id)
    if not order or (order.creator_login != user.login and not user.is_moderator):
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@router.put("/orders/{order_id}", response_model=domains.OrderDetails)
async def update_order(order_id: int, order_data: domains.OrderUpdate, user: CurrentUserDep, db: DBSessionDep):
    """Изменение полей заявки (например, целевой системы)."""
    repo = SqlAlchemyDatabaseRepo(db)
    try:
        await order_use_cases.update_order_info(repo, order_id, user.id, order_data)
        await db.commit()
        return await repo.get_full_order_details(order_id)
    except OrderNotFoundError as e:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/orders/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(order_id: int, user: CurrentUserDep, db: DBSessionDep):
    """Удаление заявки-черновика (логическое)."""
    repo = SqlAlchemyDatabaseRepo(db)
    try:
        await order_use_cases.delete_draft_order(repo, order_id, user.id)
        await db.commit()
    except OrderNotFoundError as e:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(e))
    return None

@router.put("/orders/{order_id}/form", response_model=domains.OrderDetails)
async def form_order(order_id: int, payload: domains.OrderFormPayload, user: CurrentUserDep, db: DBSessionDep):
    """Сформировать заявку (создателем)."""
    repo = SqlAlchemyDatabaseRepo(db)
    try:
        await order_use_cases.form_order(repo, order_id, user.id, payload)
        await db.commit()
        return await repo.get_full_order_details(order_id)
    except OrderNotFoundError as e:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/orders/{order_id}/complete", response_model=domains.OrderDetails, dependencies=[ModeratorDep])
async def complete_order(order_id: int, moderator: CurrentUserDep, db: DBSessionDep):
    """Завершить заявку (модератором)."""
    repo = SqlAlchemyDatabaseRepo(db)
    try:
        await order_use_cases.complete_order(repo, order_id, moderator.id)
        await db.commit()
        return await repo.get_full_order_details(order_id)
    except OrderNotFoundError as e:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/orders/{order_id}/cancel", response_model=domains.OrderDetails, dependencies=[ModeratorDep])
async def cancel_order(order_id: int, moderator: CurrentUserDep, db: DBSessionDep):
    """Отклонить заявку (модератором)."""
    repo = SqlAlchemyDatabaseRepo(db)
    try:
        await order_use_cases.cancel_order(repo, order_id, moderator.id)
        await db.commit()
        return await repo.get_full_order_details(order_id)
    except OrderNotFoundError as e:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(e))