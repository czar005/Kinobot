import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    Message,
)

# ====== НАСТРОЙКИ ======
BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))  # ваш Telegram ID — сюда придёт выбор
# =======================

BASE = Path(__file__).parent
POSTERS = BASE
LOG_FILE = BASE / "choices.jsonl"

FILMS = {
    "f1": ("Битва моторов", "1_bitva_motorov.jpg"),
    "f2": ("Чудо-Юдо", "2_chudo_yudo.jpg"),
    "f3": ("Сказка о потерянном времени", "3_skazka_o_poteryannom_vremeni.jpg"),
    "f4": ("Морозко", "4_morozko.jpg"),
    "f5": ("Руки Вверх! 2", "5_ruki_vverh_2.jpg"),
    "f6": ("Как Иван в сказку попал", "6_kak_ivan_v_skazku_popal.jpg"),
    "f7": ("Приключения Мамонтёнка", "7_mamontenok.jpg"),
}

ANSWERS = {
    "yes": ("Iharke🥰", "jan arevs. De ntri"),
    "no": ("che🤡", "gluxt patines tve! Kino ntri"),
}

bot = Bot(BOT_TOKEN)
dp = Dispatcher()
first_answer: dict[int, str] = {}  # что пользователь ответил на первый вопрос


def start_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=ANSWERS["yes"][0], callback_data="ans:yes"),
        InlineKeyboardButton(text=ANSWERS["no"][0], callback_data="ans:no"),
    ]])


def films_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{i}. {title}", callback_data=f"film:{key}")]
        for i, (key, (title, _)) in enumerate(FILMS.items(), 1)
    ])


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("Equc galises hets kino?", reply_markup=start_kb())


@dp.callback_query(F.data.startswith("ans:"))
async def on_answer(cb: CallbackQuery):
    key = cb.data.split(":", 1)[1]
    first_answer[cb.from_user.id] = ANSWERS[key][0]
    await cb.answer()
    await cb.message.edit_reply_markup(reply_markup=None)
    await cb.message.answer(ANSWERS[key][1])

    album = [
        InputMediaPhoto(media=FSInputFile(POSTERS / file), caption=f"{i}. {title}")
        for i, (title, file) in enumerate(FILMS.values(), 1)
    ]
    await cb.message.answer_media_group(album)
    await cb.message.answer("Yntri filmy 👇", reply_markup=films_kb())


@dp.callback_query(F.data.startswith("film:"))
async def on_film(cb: CallbackQuery):
    title = FILMS[cb.data.split(":", 1)[1]][0]
    user = cb.from_user
    await cb.answer()
    await cb.message.edit_reply_markup(reply_markup=None)
    await cb.message.answer(f"🎬 {title} ❤️")

    record = {
        "time": datetime.now().isoformat(timespec="seconds"),
        "user_id": user.id,
        "username": user.username,
        "name": user.full_name,
        "first_answer": first_answer.get(user.id),
        "film": title,
    }
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    logging.info("Выбор: %s", record)

    if ADMIN_ID:
        uname = f"@{user.username}" if user.username else "без username"
        await bot.send_message(
            ADMIN_ID,
            f"🍿 Новый выбор!\n"
            f"Кто: {user.full_name} ({uname}, id {user.id})\n"
            f"Ответ на вопрос: {record['first_answer']}\n"
            f"Фильм: {title}",
        )


async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
