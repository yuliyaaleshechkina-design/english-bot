import re
from groq import AsyncGroq
from config import GROQ_API_KEY

client = AsyncGroq(api_key=GROQ_API_KEY)


def remove_answer_from_text(text: str) -> str:
    """Убирает строку ПРАВИЛЬНЫЙ_ОТВЕТ и подсказки из текста задания."""
    lines = text.split("\n")
    clean_lines = []
    for line in lines:
        # Пропускаем строки с правильным ответом
        if re.search(r"ПРАВИЛЬНЫЙ.?ОТВЕТ", line, re.IGNORECASE):
            continue
        # Пропускаем строки типа "Correct answer: B" или "Answer: B"
        if re.search(r"(correct\s*answer|answer\s*key)\s*[:=]", line, re.IGNORECASE):
            continue
        # Убираем пометки типа "(правильно)" "(верно)" "(correct)" рядом с вариантами
        line = re.sub(r"\s*[\(\[]?(правильно|верно|correct|right)[\)\]]?", "", line, flags=re.IGNORECASE)
        clean_lines.append(line)
    return "\n".join(clean_lines).strip()


async def generate_exercise(prompt: str) -> str:
    """Отправляет промпт в Groq и возвращает текст упражнения."""
    try:
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ Ошибка генерации: {e}"


def extract_correct_answer(text: str) -> str:
    """Извлекает правильный ответ из текста упражнения (A/B/C/D)."""
    match = re.search(r"ПРАВИЛЬНЫЙ.?ОТВЕТ:\s*([ABCD])", text, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    match = re.search(r"(correct\s*answer|answer)\s*[:=]\s*([ABCD])", text, re.IGNORECASE)
    if match:
        return match.group(2).upper()
    return "A"


def extract_check_result(text: str) -> bool:
    """Возвращает True если ответ правильный."""
    return bool(re.search(r"РЕЗУЛЬТАТ:\s*ПРАВИЛЬНО", text, re.IGNORECASE))
