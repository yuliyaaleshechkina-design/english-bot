from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database as db
from prompts import LEVELS

router = Router()


def main_menu_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="📚 Начать упражнение",      callback_data="choose_module")
    builder.button(text="🎯 Определить мой уровень", callback_data="start_level_test")
    builder.button(text="📋 История заданий",        callback_data="history")
    builder.button(text="⚙️ Мой уровень",            callback_data="set_level")
    builder.button(text="🌐 Язык объяснений",        callback_data="set_lang")
    builder.button(text="📊 Мой прогресс",           callback_data="profile")
    builder.adjust(1)
    return builder.as_markup()


@router.message(CommandStart())
async def cmd_start(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user:
        await db.create_user(message.from_user.id, message.from_user.username or "")

    await message.answer(
        "👋 Привет! Я бот для изучения английского языка.\n\n"
        "🎯 Пройди тест чтобы определить свой уровень, или сразу начинай упражнения!\n",
        reply_markup=main_menu_kb(),
    )


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    await message.answer("📋 Главное меню:", reply_markup=main_menu_kb())


@router.callback_query(F.data == "set_level")
async def cb_set_level(callback: CallbackQuery):
    builder = InlineKeyboardBuilder()
    for lvl in LEVELS:
        builder.button(text=lvl, callback_data=f"level_{lvl}")
    builder.button(text="⬅️ Назад", callback_data="back_main")
    builder.adjust(2)
    await callback.message.edit_text("🎯 Выбери свой уровень:", reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("level_"))
async def cb_level_chosen(callback: CallbackQuery):
    level = callback.data.split("_")[1]
    await db.update_user_level(callback.from_user.id, level)
    await callback.message.edit_text(
        f"Уровень установлен: {level}\n\nМожешь начинать упражнения!",
        reply_markup=main_menu_kb(),
    )


@router.callback_query(F.data == "set_lang")
async def cb_set_lang(callback: CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="🇷🇺 Русский", callback_data="lang_ru")
    builder.button(text="🇬🇧 English", callback_data="lang_en")
    builder.button(text="⬅️ Назад",    callback_data="back_main")
    builder.adjust(2)
    await callback.message.edit_text(
        "🌐 На каком языке давать объяснения?",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data.startswith("lang_"))
async def cb_lang_chosen(callback: CallbackQuery):
    lang = callback.data.split("_")[1]
    await db.update_user_lang(callback.from_user.id, lang)
    label = "Русский 🇷🇺" if lang == "ru" else "English 🇬🇧"
    await callback.message.edit_text(
        f"Язык объяснений: {label}",
        reply_markup=main_menu_kb(),
    )


@router.callback_query(F.data == "back_main")
async def cb_back_main(callback: CallbackQuery):
    await callback.message.edit_text("📋 Главное меню:", reply_markup=main_menu_kb())
