import asyncio
import logging
import os
from io import BytesIO
from urllib.parse import urlparse

import httpx
from aiogram import Bot, Dispatcher, F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    MenuButtonWebApp,
    Message,
    ReplyKeyboardMarkup,
    WebAppInfo,
)

BOT_TOKEN = os.environ["BOT_TOKEN"]
WEBAPP_URL = os.environ["WEBAPP_URL"]  # публичный HTTPS-адрес Next.js
API_URL = os.environ.get("API_URL", "http://backend:8000")
BACKEND_ENABLED = os.environ.get("BACKEND_ENABLED", "true").lower() == "true"
API_SECRET = os.environ.get("BOT_API_SECRET", "")
ADMIN_IDS = {int(x) for x in os.environ.get("ADMIN_IDS", "").split(",") if x.strip()}

if urlparse(WEBAPP_URL).scheme != "https" or not urlparse(WEBAPP_URL).hostname:
    raise ValueError("WEBAPP_URL must be a public HTTPS URL")

GREETING = "Welcome to the catalog!"
log = logging.getLogger("bot")

catalog_kb = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="Open catalog", web_app=WebAppInfo(url=WEBAPP_URL))]]
)
admin_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Create product")]], resize_keyboard=True)


class CreateProduct(StatesGroup):
    waiting = State()


# --- админ: фильтр на уровне роутера, остальные пользователи сюда не попадают ---
admin = Router()
admin.message.filter(F.from_user.id.in_(ADMIN_IDS))


@admin.message(CommandStart())
async def admin_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(GREETING, reply_markup=catalog_kb)
    if BACKEND_ENABLED:
        await message.answer("Admin menu. Use Create product or /create.", reply_markup=admin_kb)


@admin.message(Command("create"))
@admin.message(F.text == "Create product")
async def create_start(message: Message, state: FSMContext):
    if not BACKEND_ENABLED:
        await state.clear()
        await message.answer("Product creation requires the backend. You can browse the demo catalog.", reply_markup=catalog_kb)
        return
    await state.set_state(CreateProduct.waiting)
    await message.answer(
        "Send a photo with a product title in the caption. Cancel: /cancel"
    )


@admin.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Admin menu. Use Create product or /create.", reply_markup=admin_kb)


@admin.message(CreateProduct.waiting, F.photo, F.caption)
async def create_submit(message: Message, bot: Bot, state: FSMContext):
    title = message.caption.strip()
    if not title or len(title) > 255:
        await message.answer("Название длиннее 255 символов. Сократите и отправьте снова.")
        return

    buf = BytesIO()
    try:
        await bot.download(message.photo[-1], destination=buf)
        async with httpx.AsyncClient(timeout=30) as http:
            r = await http.post(
                f"{API_URL}/api/products",
                headers={"X-Bot-Secret": API_SECRET},
                data={"title": title},
                files={"image": ("photo.jpg", buf.getvalue(), "image/jpeg")},
            )
            r.raise_for_status()
    except (httpx.HTTPError, TelegramAPIError):
        log.exception("Failed to save product")
        await message.answer("Не удалось сохранить товар. Попробуйте ещё раз.")
        return

    await state.clear()
    await message.answer(f"Product created: {title}", reply_markup=catalog_kb)


@admin.message(CreateProduct.waiting)
async def create_invalid(message: Message):
    await message.answer("Нужно одно сообщение: фото + подпись с названием.\nОтмена: /cancel")


# --- все остальные (и админ вне сценария создания) ---
user = Router()


@user.message()
async def greet(message: Message):
    await message.answer(GREETING, reply_markup=catalog_kb)


async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())  # при нескольких инстансах: RedisStorage
    dp.include_routers(admin, user)

    await bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(text="Catalog", web_app=WebAppInfo(url=WEBAPP_URL))
    )
    await bot.delete_webhook()
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
