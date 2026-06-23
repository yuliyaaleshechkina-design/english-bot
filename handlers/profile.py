from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database as db

router = Router()


@router.callback_query(F.data == "profile")
async def cb_profile(callback: CallbackQuery):
    user  = await db.get_user(callback.from_user.id)
    stats = await db.get_stats(callback.from_user.id)

    if not user or not stats:
        await callback.answer("Профиль не найден", show_alert=True)
        return

    xp      = stats["xp"]
    correct = stats["correct"]
    wrong   = stats["wrong"]
    total   = correct + wrong
    accuracy = round(correct / total * 100) if total > 0 else 0

    # Уровень мастерства по XP
    if xp < 100:
        mastery = "🌱 Новичок"
    elif xp < 300:
        mastery = "📘 Ученик"
    elif xp < 600:
        mastery = "⭐ Знаток"
    elif xp < 1000:
        mastery = "🔥 Продвинутый"
    else:
        mastery = "🏆 Мастер"

    text = (
        f"👤 *Твой профиль*\n\n"
        f"🎯 Уровень: *{user['level']}*\n"
        f"⚡ XP: *{xp}*\n"
        f"🏅 Статус: {mastery}\n\n"
        f"📊 *Статистика*\n"
        f"✅ Правильных: {correct}\n"
        f"❌ Неправильных: {wrong}\n"
        f"🎯 Точность: {accuracy}%"
    )

    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Назад", callback_data="back_main")

    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=builder.as_markup())
