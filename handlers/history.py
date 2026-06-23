from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database as db
from prompts import MODULES

router = Router()


@router.callback_query(F.data == "history")
async def cb_history(callback: CallbackQuery):
    sessions = await db.get_history(callback.from_user.id)

    if not sessions:
        builder = InlineKeyboardBuilder()
        builder.button(text="⬅️ Назад", callback_data="back_main")
        await callback.message.edit_text(
            "📋 История пуста — ещё нет выполненных заданий.",
            reply_markup=builder.as_markup(),
        )
        return

    builder = InlineKeyboardBuilder()
    for s in sessions:
        emoji   = "✅" if s["is_correct"] else "❌"
        module  = MODULES.get(s["module"], s["module"])
        topic   = s["topic"] or ""
        label   = f"{emoji} {module} — {topic}"[:40]
        builder.button(text=label, callback_data=f"history_item_{s['id']}")

    builder.button(text="⬅️ Назад", callback_data="back_main")
    builder.adjust(1)

    await callback.message.edit_text(
        "📋 Последние задания (нажми чтобы открыть):",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data.startswith("history_item_"))
async def cb_history_item(callback: CallbackQuery):
    session_id = int(callback.data.removeprefix("history_item_"))
    s = await db.get_session_by_id(session_id, callback.from_user.id)

    if not s:
        await callback.answer("Задание не найдено", show_alert=True)
        return

    emoji  = "✅ Правильно" if s["is_correct"] else "❌ Неправильно"
    module = MODULES.get(s["module"], s["module"])

    text = (
        f"📌 {module} | {s['level']} | {s['topic']}\n"
        f"{'─' * 30}\n"
        f"{s['exercise_text'] or ''}\n"
        f"{'─' * 30}\n"
        f"Твой ответ: {s['user_answer']} | {emoji}\n"
        f"Правильный: {s['correct_answer']}\n\n"
        f"{s['feedback'] or ''}"
    )

    # Обрезаем если слишком длинно для Telegram
    if len(text) > 4000:
        text = text[:4000] + "..."

    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ К истории", callback_data="history")
    builder.button(text="🏠 Главное меню", callback_data="back_main")
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
