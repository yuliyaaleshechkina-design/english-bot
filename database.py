import aiosqlite
from config import DB_PATH


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id     INTEGER PRIMARY KEY,
                username    TEXT,
                level       TEXT DEFAULT 'A1',
                lang        TEXT DEFAULT 'ru',
                xp          INTEGER DEFAULT 0,
                correct     INTEGER DEFAULT 0,
                wrong       INTEGER DEFAULT 0,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id         INTEGER,
                module          TEXT,
                topic           TEXT,
                level           TEXT,
                exercise_text   TEXT,
                correct_answer  TEXT,
                user_answer     TEXT,
                feedback        TEXT,
                is_correct      INTEGER,
                xp_earned       INTEGER DEFAULT 0,
                created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Добавляем колонки если их нет (для старых баз)
        try:
            await db.execute("ALTER TABLE sessions ADD COLUMN exercise_text TEXT")
        except:
            pass
        try:
            await db.execute("ALTER TABLE sessions ADD COLUMN feedback TEXT")
        except:
            pass
        await db.commit()


async def get_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ) as cursor:
            return await cursor.fetchone()


async def create_user(user_id: int, username: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
            (user_id, username),
        )
        await db.commit()


async def update_user_level(user_id: int, level: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET level = ? WHERE user_id = ?", (level, user_id)
        )
        await db.commit()


async def update_user_lang(user_id: int, lang: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET lang = ? WHERE user_id = ?", (lang, user_id)
        )
        await db.commit()


async def add_xp(user_id: int, xp: int, is_correct: bool):
    async with aiosqlite.connect(DB_PATH) as db:
        if is_correct:
            await db.execute(
                "UPDATE users SET xp = xp + ?, correct = correct + 1 WHERE user_id = ?",
                (xp, user_id),
            )
        else:
            await db.execute(
                "UPDATE users SET wrong = wrong + 1 WHERE user_id = ?", (user_id,)
            )
        await db.commit()


async def save_session(user_id, module, topic, level, exercise_text,
                       correct_answer, user_answer, feedback, is_correct, xp):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO sessions
               (user_id, module, topic, level, exercise_text, correct_answer,
                user_answer, feedback, is_correct, xp_earned)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, module, topic, level, exercise_text, correct_answer,
             user_answer, feedback, int(is_correct), xp),
        )
        await db.commit()


async def get_stats(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT xp, correct, wrong FROM users WHERE user_id = ?", (user_id,)
        ) as cursor:
            return await cursor.fetchone()


async def get_history(user_id: int, limit: int = 10):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT id, module, topic, level, exercise_text, correct_answer,
                      user_answer, feedback, is_correct, created_at
               FROM sessions WHERE user_id = ?
               ORDER BY created_at DESC LIMIT ?""",
            (user_id, limit),
        ) as cursor:
            return await cursor.fetchall()


async def get_session_by_id(session_id: int, user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM sessions WHERE id = ? AND user_id = ?",
            (session_id, user_id),
        ) as cursor:
            return await cursor.fetchone()
