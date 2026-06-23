from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database as db
from ai_generator import generate_exercise

router = Router()

TOTAL_QUESTIONS = 10

class LevelTestState(StatesGroup):
    testing = State()


def get_level_by_score(score: int) -> str:
    if score <= 3:
        return "A1"
    elif score <= 5:
        return "A2"
    elif score <= 7:
        return "B1"
    else:
        return "B2"


TEST_PROMPT = """Создай один вопрос для теста определения уровня английского языка.

Уровень вопроса: {level}
Номер вопроса: {num} из 10

ПРАВИЛА:
1. Вопрос на английском языке — грамматика или словарный запас.
2. Ровно 4 варианта ответа: A, B, C, D — все на английском.
3. НЕ пиши правильный ответ в тексте — только в конце.
4. НЕ используй символы * и _ для форматирования.
5. В самом конце одна строка: ПРАВИЛЬНЫЙ_ОТВЕТ: X

Пример формата:
Вопрос {num}/10 | Уровень: {level}

Choose the correct word:
"She ___ to school every day."

A) go
B) goes
C) going
D) gone

ПРАВИЛЬНЫЙ_ОТВЕТ: B
"""


async def send_next_question(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    num  = data.get("q_num", 1)

    # Определяем уровень вопроса
    if num <= 3:
        level = "A1"
    elif num <= 5:
        level = "A2"
    elif num <= 7:
        level = "B1"
    else:
        level = "B2"

    await callback.message.edit_text(f"⏳ Генерирую вопрос {num}/10…")

    prompt   = TEST_PROMPT.format(level=level, num=num)
    question = await generate_exercise(prompt)

    from ai_generator import extract_correct_answer
    correct = extract_correct_answer(question)

    await state.update_data(q_correct=correct, q_text=question)
    await state.set_state(LevelTestState.testing)

    builder = InlineKeyboardBuilder()
    for letter in ["A", "B", "C", "D"]:
        builder.button(text=letter, callback_data=f"test_answer_{letter}")
    builder.adjust(4)

    await callback.message.edit_text(question, reply_markup=builder.as_markup())


@router.callback_query(F.data == "start_level_test")
async def cb_start_test(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.update_data(q_num=1, score=0)
    await callback.message.edit_text(
        "🎯 Тест на определение уровня английского\n\n"
        "10 вопросов — грамматика и словарный запас.\n"
        "По результатам тебе автоматически присвоится уровень A1, A2, B1 или B2.\n\n"
        "Начинаем! 👇"
    )
    await send_next_question(callback, state)


@router.callback_query(F.data.startswith("test_answer_"), LevelTestState.testing)
async def cb_test_answer(callback: CallbackQuery, state: FSMContext):
    user_answer = callback.data.removeprefix("test_answer_")
    data        = await state.get_data()

    correct = data.get("q_correct", "A")
    score   = data.get("score", 0)
    num     = data.get("q_num", 1)

    is_correct = user_answer == correct
    if is_correct:
        score += 1

    # Показываем результат вопроса
    result_emoji = "✅" if is_correct else "❌"
    msg = f"{result_emoji} Твой ответ: {user_answer} | Правильный: {correct}\n\n"

    if num >= TOTAL_QUESTIONS:
        # Тест закончен
        level = get_level_by_score(score)
        await db.update_user_level(callback.from_user.id, level)

        level_desc = {
            "A1": "Начинающий — базовые слова и простые фразы",
            "A2": "Элементарный — простые предложения и диалоги",
            "B1": "Средний — уверенное общение на знакомые темы",
            "B2": "Выше среднего — сложные тексты и дискуссии",
        }

        from handlers.start import main_menu_kb
        await callback.message.edit_text(
            f"{msg}"
            f"🏁 Тест завершён!\n\n"
            f"Правильных ответов: {score} из {TOTAL_QUESTIONS}\n\n"
            f"🎯 Твой уровень: {level}\n"
            f"📝 {level_desc[level]}\n\n"
            f"Теперь все задания будут подобраны под твой уровень!",
            reply_markup=main_menu_kb(),
        )
        await state.clear()
    else:
        # Следующий вопрос
        await state.update_data(q_num=num + 1, score=score)

        builder = InlineKeyboardBuilder()
        builder.button(text="➡️ Следующий вопрос", callback_data="next_test_question")
        builder.adjust(1)

        await callback.message.edit_text(
            msg + f"Вопрос {num}/{TOTAL_QUESTIONS} | Счёт: {score}",
            reply_markup=builder.as_markup(),
        )


@router.callback_query(F.data == "next_test_question")
async def cb_next_question(callback: CallbackQuery, state: FSMContext):
    await send_next_question(callback, state)
