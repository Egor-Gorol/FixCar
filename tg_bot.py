import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
import os
from dotenv import load_dotenv
from aiogram.filters import Command
from sqlalchemy import select
from models import User, Users_in_telegram
from settings import async_session

load_dotenv()


token = os.getenv("BOT_TOKEN")

bot = Bot(token=token)  # type: ignore
dp: Dispatcher = Dispatcher()


async def send_msg(user_site_id, message):
    async with async_session() as session:
        user_tg_info = await session.execute(select(Users_in_telegram).filter_by(user_in_site=user_site_id))
        user_tg_info = user_tg_info.scalars().one_or_none()
        if user_tg_info and user_tg_info.user_tg_id:
            await bot.send_message(chat_id=user_tg_info.user_tg_id, text=message)


@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer("Вітаю! Це бот служби підтримки. Будь ласка, введіть ваш унікальний код для авторизації.")


@dp.message()
async def get_code(message: types.Message):
    user_code = message.text.strip() if message.text else ""
    user_tg_id = message.chat.id

    async with async_session() as session:
        stmt = select(Users_in_telegram).where(Users_in_telegram.tg_code == user_code)
        user_check = await session.execute(stmt)
        user_check = user_check.scalar_one_or_none()

        if user_check:
            user_check.user_tg_id = str(user_tg_id)
            session.add(user_check)
            await session.commit()
            await message.answer("Ви успішно додані до бота! Будемо інформувати вас про статус ваших заявок.")
        else:
            await message.answer("Невірний код. Будь ласка, перевірте та спробуйте ще раз.")

# ---------------- /services ----------------

SERVICES = {
    "Покраска": {
        "price": 2500,
        "time": "2 години",
        "description": "Покраска кузова автомобіля будь-якого кольору"
    },
    "Техосмотр": {
        "price": 1000,
        "time": "30 хвилин",
        "description": "Проведення технічного огляду автомобіля"
    }
}

def services_keyboard():
    keyboard = [
        [KeyboardButton(text=service)]
        for service in SERVICES.keys()
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )

# ---------------- /services ----------------

@dp.message(Command("services"))
async def services_command(message: types.Message):
    await message.answer(
        "Виберіть послугу:",
        reply_markup=services_keyboard()
    )

# ---------------- ВИБІР ПОСЛУГИ ----------------
@dp.message()
async def service_info(message: types.Message):
    text = message.text.strip() if message.text else ""

    if text not in SERVICES:
        return

    service = SERVICES[text]

    await message.answer(
        f" {text}\n\n"
        f" Ціна: {service['price']}\n"
        f" Час: {service['time']}\n"
        f" {service['description']}"
    )

async def start_bot():
    print("--> start bot")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(start_bot())
