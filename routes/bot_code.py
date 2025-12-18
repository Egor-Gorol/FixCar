from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


from models import Users_in_telegram
from routes.auth import get_current_user
from settings import get_db
import random
import string

router = APIRouter()


def generate_code():
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


@router.get("/generate_code", status_code=status.HTTP_200_OK)
async def generate_tg_code(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):

    user_id = current_user["sub"]

    # Генерація унікального коду
    code = generate_code()

    check_user = await db.scalar(select(Users_in_telegram).filter_by(user_in_site=int(current_user["sub"])))

    if check_user:
        check_user.tg_code = code
        check_user.user_tg_id = None  # type: ignore

    else:
        check_user = Users_in_telegram(tg_code=code, user_tg_id=None, user_in_site=int(user_id))

    db.add(check_user)
    await db.commit()
    await db.refresh(check_user)

    return {"tg_code": code, "message": "Збережіть цей код для авторизації в Telegram боті."}
