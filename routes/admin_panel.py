from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import User
from models.models import RepairRequest, RequestStatus
from routes.auth import get_current_user, require_admin
from settings import get_db
from tg_bot import send_msg

router = APIRouter()


class StatusUpdateRequest(BaseModel):
    status: RequestStatus


@router.get("/user/admin/me")
async def only_for_admin(current_user: User = Depends(require_admin)):
    return {"is admin": current_user}


@router.get("/admin/repairs")
async def admin_get_repairs(
    new: int | None = None,
    current_user_admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
  
    stmt = select(RepairRequest)
    if new == 1:
        stmt = stmt.where(RepairRequest.status == RequestStatus.NEW)

    repairs = await db.scalars(stmt)
    return repairs.all()


@router.delete("/admin/repairs/{repair_id}")
async def delete_repair_request(
    repair_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin)
):
    repair = await db.scalar(select(RepairRequest).filter(RepairRequest.id == repair_id))
    if not repair:
        raise HTTPException(status_code=404, detail="Заявку не знайдено")

    db.delete(repair)
    await db.commit()
    return {"message": "Заявку на ремонт видалено"}


@router.get("/admin/repairs")
async def get_all_repairs(
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin)
):
    repairs = await db.scalars(select(RepairRequest))
    repairs = repairs.all()

    statistics = {
        "new": db.query(RepairRequest).filter_by(status="new").count(),
        "in_progress": db.query(RepairRequest).filter_by(status="in_progress").count(),
        "completed": db.query(RepairRequest).filter_by(status="completed").count(),
        "canceled": db.query(RepairRequest).filter_by(status="canceled").count(),
        "total": db.query(RepairRequest).count()
    }

    return {
        "repairs": repairs,
        "statistics": statistics
    }


# Зміна статусу заявки та відправлення повідомлення у телеграм


@router.patch("/requests/{request_id}/status")
async def update_request_status(

    request_id: int,
    body: StatusUpdateRequest,
    current_user_admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
 

    new_status = body.status

    req = await db.scalar(select(RepairRequest).filter_by(id=request_id))
    if req is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заявка не знайдена")

    # Обновляємо статус
    req.status = new_status
    db.add(req)
    await db.commit()
    await db.refresh(req)

    # Формуємо текст повідомлення
    message_text = (
        f"Статус вашої заявки #{req.id} було змінено на: {new_status.value}.\n"
        f"Деталі: {req.description}\n"
        f"Для деталей відкрийте ваш особистий кабінет."
    )

    # Відправляємо повідомлення у телеграм
    try:
        await send_msg(req.user_id, message_text)
        message_sent = True
    except Exception as e:
        print(f"Помилка при відправці повідомлення у телеграм: {e}")
        message_sent = False
    return {"request_id": req.id, "status": req.status, "message_sent": message_sent}
