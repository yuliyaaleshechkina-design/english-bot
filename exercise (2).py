from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
import html

import database as db
from prompts import MODULES, TOPICS, SPOILER_MODULES, build_exercise_prompt, build_check_prompt
from ai_generator import generate_exercise, extract_correct_answer, extract_check_result, remove_answer_from_text

router = Router()

class ExerciseState(StatesGroup):
    choosing_module = State()
    choosing_topic  = State()
    waiting_answer  = State()
    asking_question = State()


def answer_kb():
    builder = InlineKeyboardBuilder()
    for letter in ["A", "B", "C", "D"]:
        builder.button(text=letter, callback_data=f"answer_{letter}")
    builder.button(text="🔄 Другое упражнение", callback_data="next_exercise")
    builder.button(text="🏠 Главное меню",       callback_data="back_main")
    builder.adjust(4, 1, 1)
    return builder.as_markup()


def spoiler_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="❓ Задать вопрос",      callback_data="ask_question")
    builder.button(text="➡️ Следующее задание", callback_data="next_exercise")
    builder.button(text="📋 История заданий",   callback_data="history")
    builder.button(text="🏠 Главное меню",      callback_data="back_main")
    builder.adjust(1)
    return builder.as_markup()


def after_answer_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="❓ Задать вопрос",      callback_data="ask_question")
    builder.button(text="➡️ Следующее задание", callback_data="next_exercise")
    builder.button(text="📋 История заданий",   callback_data="history")
    builder.button(text="🏠 Главное меню",      callback_data="back_main")
    builder.adjust(1)
    return builder.as_markup()


def after_question_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="❓ Ещё вопрос",         callback_data="ask_question")
    builder.button(text="➡️ Следующее задание", callback_data="next_exercise")
    builder.button(text="🏠 Главное меню",      callback_data="back_main")
    builder.adjust(1)
    return builder.as_markup()


def make_spoiler_text(text: str) -> str:
    clean = text.replace("**", "").replace("__", "")
    markers = ["👇 Показать ответы", "Показать ответы", "Ответы:", "Answers:"]
    split_idx = -1
    found_marker = ""
    for marker in markers:
        idx = clean.find(marker)
        if idx != -1:
            split_idx = idx
            found_marker = marker
            break
    if split_idx != -1:
        before  = clean[:split_idx + len(found_marker)]
        answers = clean[split_idx + len(found_marker):]
        return html.escape(before) + "\n<tg-spoiler>" + html.escape(answers.strip()) + "</tg-spoiler>"
    paragraphs = clean.strip().rsplit("\n\n", 1)
    if len(paragraphs) == 2:
        return html.escape(paragraphs[0]) + "\n\n<tg-spoiler>" + html.escape(paragraphs[1]) + "</tg-spoiler>"
    return "<tg-spoiler>" + html.escape(clean) + "</tg-spoiler>"


@router.callback_query(F.data == "choose_module")
async def cb_choose_module(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    for key, name in MODULES.items():
        builder.button(text=name, callback_data=f"module_{key}")
    builder.button(text="⬅️ Назад", callback_data="back_main")
    builder.adjust(1)
    await state.set_state(ExerciseState.choosing_module)
    await callback.message.edit_text("📚 Выбери модуль:", reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("module_"))
async def cb_module_chosen(callback: CallbackQuery, state: FSMContext):
    module = callback.data.removeprefix("module_")
    await state.update_data(module=module)
    builder = InlineKeyboardBuilder()
    for i, topic in enumerate(TOPICS):
        builder.button(text=topic, callback_data=f"topic_{i}")
    builder.button(text="⬅️ Назад", callback_data="choose_module")
    builder.adjust(2)
    await state.set_state(ExerciseState.choosing_topic)
    await callback.message.edit_text("🗂 Выбери тему:", reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("topic_"))
async def cb_topic_chosen(callback: CallbackQuery, state: FSMContext):
    idx    = int(callback.data.removeprefix("topic_"))
    topic  = TOPICS[idx]
    await state.update_data(topic=topic)

    user   = await db.get_user(callback.from_user.id)
    level  = user["level"] if user else "A1"
    lang   = user["lang"]  if user else "ru"
    data   = await state.get_data()
    module = data["module"]

    await state.update_data(level=level, lang=lang)
    await state.set_state(ExerciseState.waiting_answer)
    await callback.message.edit_text("⏳ Генерирую упражнение…")

    prompt   = build_exercise_prompt(module, level, topic, lang)
    exercise = await generate_exercise(prompt)
    correct  = extract_correct_answer(exercise)

    await state.update_data(exercise=exercise, correct=correct)

    if module in SPOILER_MODULES:
        html_text = make_spoiler_text(exercise)
        await callback.message.edit_text(
            html_text, reply_markup=spoiler_kb(), parse_mode="HTML",
        )
        await db.save_session(
            callback.from_user.id, module, topic, level,
            exercise, correct, "spoiler", "", True, 5
        )
        await db.add_xp(callback.from_user.id, 5, True)
        await state.clear()
    else:
        clean = remove_answer_from_text(exercise)
        await callback.message.edit_text(clean, reply_markup=answer_kb())


@router.callback_query(F.data.startswith("answer_"), ExerciseState.waiting_answer)
async def cb_answer(callback: CallbackQuery, state: FSMContext):
    user_answer = callback.data.removeprefix("answer_")
    data        = await state.get_data()

    module   = data.get("module",   "")
    topic    = data.get("topic",    "")
    level    = data.get("level",    "A1")
    lang     = data.get("lang",     "ru")
    exercise = data.get("exercise", "")
    correct  = data.get("correct",  "A")

    await callback.message.edit_text("🔍 Проверяю ответ…")

    check_prompt = build_check_prompt(module, level, topic, exercise, user_answer, correct, lang)
    feedback     = await generate_exercise(check_prompt)
    is_correct   = extract_check_result(feedback)
    xp           = 10 if is_correct else 0

    await db.add_xp(callback.from_user.id, xp, is_correct)
    await db.save_session(
        callback.from_user.id, module, topic, level,
        exercise, correct, user_answer, feedback, is_correct, xp
    )

    result_line   = f"\n\n{'✅ +10 XP' if is_correct else '❌ 0 XP'}"
    safe_feedback = feedback.replace("**", "").replace("__", "")

    await state.update_data(last_exercise=exercise, last_feedback=safe_feedback)

    await callback.message.edit_text(
        safe_feedback + result_line,
        reply_markup=after_answer_kb(),
    )
    await state.clear()


# ── Вопрос по заданию ────────────────────────────────────────

@router.callback_query(F.data == "ask_question")
async def cb_ask_question(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    # Сохраняем контекст задания
    await state.update_data(
        last_exercise=data.get("last_exercise", ""),
        last_feedback=data.get("last_feedback", ""),
    )
    await state.set_state(ExerciseState.asking_question)

    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="cancel_question")
    await callback.message.answer(
        "❓ Напиши свой вопрос по этому заданию — я отвечу!",
        reply_markup=builder.as_markup(),
    )


@router.message(ExerciseState.asking_question)
async def cb_receive_question(message: Message, state: FSMContext):
    data     = await state.get_data()
    exercise = data.get("last_exercise", "")
    feedback = data.get("last_feedback", "")
    question = message.text

    await message.answer("⏳ Думаю над ответом…")

    prompt = f"""Ты преподаватель английского языка. Студент выполнял упражнение и задаёт вопрос.

УПРАЖНЕНИЕ:
{exercise}

ОБЪЯСНЕНИЕ КОТОРОЕ УЖЕ БЫЛО ДАНО:
{feedback}

ВОПРОС СТУДЕНТА:
{question}

Ответь на вопрос студента на русском языке. Будь понятным и дружелюбным.
НЕ используй символы * и _ для форматирования.
"""
    answer = await generate_exercise(prompt)
    safe_answer = answer.replace("**", "").replace("__", "")

    await state.clear()
    await message.answer(safe_answer, reply_markup=after_question_kb())


@router.callback_query(F.data == "cancel_question")
async def cb_cancel_question(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    from handlers.start import main_menu_kb
    await callback.message.edit_text("📋 Главное меню:", reply_markup=main_menu_kb())


@router.callback_query(F.data == "next_exercise")
async def cb_next_exercise(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    from handlers.start import main_menu_kb
    await callback.message.edit_text("📋 Главное меню:", reply_markup=main_menu_kb())
