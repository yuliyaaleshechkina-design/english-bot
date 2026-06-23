# 🤖 English Learning Bot

Telegram бот для изучения английского языка с AI-генерацией упражнений (Google Gemini).

---

## 📁 Структура проекта

```
english_bot/
├── bot.py              — запуск бота
├── config.py           — 🔑 СЮДА ВСТАВЛЯЕШЬ КЛЮЧИ
├── database.py         — база данных (SQLite)
├── ai_generator.py     — работа с Gemini API
├── prompts.py          — промпты для генерации упражнений
├── requirements.txt    — зависимости
└── handlers/
    ├── start.py        — главное меню, настройки
    ├── exercise.py     — выбор модуля/темы, ответы
    └── profile.py      — профиль и статистика
```

---

## 🚀 Установка и запуск

### Шаг 1 — Получи токены

1. **Telegram Bot Token** → напиши @BotFather в Telegram → `/newbot`
2. **Gemini API Key** → зайди на https://aistudio.google.com → Get API Key

### Шаг 2 — Вставь ключи

Открой файл `config.py` и замени:
```python
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"    # ← вставь токен бота
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"   # ← вставь ключ Gemini
```

### Шаг 3 — Установи зависимости

```bash
pip install -r requirements.txt
```

### Шаг 4 — Запусти бота

```bash
python bot.py
```

---

## ☁️ Деплой на Railway

1. Загрузи папку на GitHub
2. Зайди на https://railway.app
3. New Project → Deploy from GitHub
4. Выбери репозиторий
5. В настройках добавь переменные среды:
   - `BOT_TOKEN` = твой токен
   - `GEMINI_API_KEY` = твой ключ
6. Готово! Бот работает 24/7 ✅

> **Важно:** Если деплоишь на Railway, в `config.py` замени значения на:
> ```python
> import os
> BOT_TOKEN = os.getenv("BOT_TOKEN")
> GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
> ```

---

## 🎮 Функции бота

- 9 модулей обучения (диалоги, грамматика, перевод и др.)
- 4 уровня сложности (A1–B2)
- 40+ тем
- Система XP и прогресса
- Язык объяснений: русский или английский
- AI генерирует уникальные упражнения каждый раз
