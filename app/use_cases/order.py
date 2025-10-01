# app/use_cases/order.py

from datetime import datetime, timezone
from typing import List, Optional

from app.interfaces import AbstractDatabaseRepo, AbstractFileStorage, ServiceNotFoundError, OrderNotFoundError
from app import domains, models


async def add_service_to_cart(repo: AbstractDatabaseRepo, user_id: int, service_id: int) -> domains.OrderDetails:
    service = await repo.get_service_by_id(service_id)
    if not service:
        raise ServiceNotFoundError("Service not found")
    
    draft_order = await repo.get_draft_order_by_user_id(user_id)
    if not draft_order:
        draft_order = await repo.create_draft_order(user_id)
    
    is_present = any(item.service.id == service_id for item in draft_order.services)
    
    if not is_present:
        await repo.add_service_to_order(draft_order.id, service_id, service.price)
        return await repo.get_full_order_details(draft_order.id)

    return draft_order


async def remove_service_from_cart(repo: AbstractDatabaseRepo, user_id: int, service_id: int) -> domains.OrderDetails:
    """
    Удаляет услугу из корзины пользователя.
    Возвращает актуальное состояние корзины.
    """
    draft_order = await repo.get_draft_order_by_user_id(user_id)
    if not draft_order:
        raise OrderNotFoundError("Cart not found")
    
    deleted = await repo.delete_service_from_order(draft_order.id, service_id)
    if not deleted:
        raise ServiceNotFoundError("Service not found in cart")
    
    return await repo.get_full_order_details(draft_order.id)


async def update_cart_item_details(repo: AbstractDatabaseRepo, user_id: int, service_id: int, item_data: domains.CartItemUpdate) -> domains.OrderDetails:
    """
    Обновляет детали (уровень защиты, комментарий) для услуги в корзине.
    Возвращает актуальное состояние корзины.
    """
    draft_order = await repo.get_draft_order_by_user_id(user_id)
    if not draft_order:
        raise OrderNotFoundError("Cart not found")
        
    await repo.update_association(draft_order.id, service_id, **item_data.model_dump())
    return await repo.get_full_order_details(draft_order.id)


async def form_order(repo: AbstractDatabaseRepo, order_id: int, user_id: int, payload: domains.OrderFormPayload):
    order = await repo.get_full_order_details(order_id)
    if not order or order.created_by != user_id or order.status != models.OrderStatus.DRAFT:
        raise OrderNotFoundError("Draft order not found for this user")

    for item in payload.services:
        await repo.update_association(
            order_id=order.id,
            service_id=item.service_id,
            protection_level=item.protection_level,
            comment=item.comment
        )
    
    await repo.update_order(
        order_id=order.id,
        target_system_info=payload.target_system_info,
        status=models.OrderStatus.FORMED,
        formation_date=datetime.now(timezone.utc)
    )


async def complete_order(repo: AbstractDatabaseRepo, order_id: int, moderator_id: int):
    order_details = await repo.get_full_order_details(order_id)
    if not order_details or order_details.status != models.OrderStatus.FORMED:
        raise OrderNotFoundError("A 'formed' order is required to complete")

    protection_to_likelihood = {"none": 3, "basic": 2, "full": 1}
    max_risk_score = 0
    
    for item in order_details.services:
        likelihood = protection_to_likelihood.get(item.protection_level.value, 3)
        impact = item.service.impact_level
        risk_score = likelihood * impact
        if risk_score > max_risk_score:
            max_risk_score = risk_score
    
    await repo.update_order(
        order_id=order_details.id,
        status=models.OrderStatus.COMPLETED,
        completion_date=datetime.now(timezone.utc),
        moderated_by=moderator_id,
        risk_score=max_risk_score
    )


async def cancel_order(repo: AbstractDatabaseRepo, order_id: int, moderator_id: int):
    order = await repo.get_full_order_details(order_id)
    if not order or order.status != models.OrderStatus.FORMED:
        raise OrderNotFoundError("A 'formed' order is required to cancel")

    await repo.update_order(
        order_id=order.id,
        status=models.OrderStatus.CANCELLED,
        completion_date=datetime.now(timezone.utc),
        moderated_by=moderator_id
    )


async def delete_draft_order(repo: AbstractDatabaseRepo, order_id: int, user_id: int):
    order = await repo.get_full_order_details(order_id)
    if not order or order.created_by != user_id or order.status != models.OrderStatus.DRAFT:
        raise OrderNotFoundError("Draft order not found for this user")
    
    await repo.update_order(order_id=order.id, status=models.OrderStatus.DELETED)


async def update_order_info(repo: AbstractDatabaseRepo, order_id: int, user_id: int, order_data: domains.OrderUpdate):
    order = await repo.get_full_order_details(order_id)
    if not order or order.created_by != user_id:
        raise OrderNotFoundError("Order not found")
    
    await repo.update_order(order_id=order.id, target_system_info=order_data.target_system_info)