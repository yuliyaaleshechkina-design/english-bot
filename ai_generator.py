import re
from groq import AsyncGroq
from config import GROQ_API_KEY

client = AsyncGroq(api_key=GROQ_API_KEY)


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
    match = re.search(r"ПРАВИЛЬНЫЙ_ОТВЕТ:\s*([ABCD])", text, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    match = re.search(r"ПРАВИЛЬНЫЙ ОТВЕТ[:\s]+([ABCD])", text, re.IGNORECASE)
    return match.group(1).upper() if match else "A"


def extract_check_result(text: str) -> bool:
    """Возвращает True если ответ правильный."""
    return bool(re.search(r"РЕЗУЛЬТАТ:\s*ПРАВИЛЬНО", text, re.IGNORECASE))
