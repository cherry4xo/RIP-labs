from datetime import datetime
from typing import List, Optional

from app.interfaces import AbstractDatabaseRepo, AbstractFileStorage, ServiceNotFoundError, OrderNotFoundError
from app import domains, models



async def add_service_to_cart(repo: AbstractDatabaseRepo, user_id: int, service_id: int):
    service = await repo.get_service_by_id(service_id)
    if not service:
        raise ServiceNotFoundError("Service not found")
    
    draft_order = await repo.get_draft_order_by_user_id(user_id)
    if not draft_order:
        draft_order = await repo.create_draft_order(user_id)
    
    is_present = await repo.get_association(draft_order.id, service_id)
    if not is_present:
        await repo.add_service_to_order(draft_order.id, service_id, service.price)


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
        formation_date=datetime.now()
    )


async def complete_order(repo: AbstractDatabaseRepo, order_id: int, moderator_id: int):
    order = await repo.get_full_order_details(order_id)
    if not order or order.status != models.OrderStatus.FORMED:
        raise OrderNotFoundError("A 'formed' order is required to complete")

    # --- Расчет риска (Матрица) ---
    protection_to_likelihood = {"none": 3, "basic": 2, "full": 1}
    max_risk_score = 0
    for assoc in order.service_associations:
        likelihood = protection_to_likelihood.get(assoc.protection_level.value, 3)
        impact = assoc.service.impact_level
        risk_score = likelihood * impact
        if risk_score > max_risk_score:
            max_risk_score = risk_score
    
    await repo.update_order(
        order_id=order.id,
        status=models.OrderStatus.COMPLETED,
        completion_date=datetime.now(),
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
        completion_date=datetime.now(),
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