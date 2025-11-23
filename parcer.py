import asyncio
from os import getenv
import logging
import re
from typing import List, Tuple, Optional

from aiohttp import ClientSession
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.utils.markdown import hbold
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = getenv('BOT_TOKEN')
OPENROUTER_API_KEY = getenv('OPENROUTER_API_KEY')
MODEL = "gpt-4o-mini-1"

URL = "https://freelance.ru/project/search?q=&a=0&a=1&v=0&v=1&c=&c%5B%5D=724&c%5B%5D=4"
HEADERS = {"User-Agent": "Mozilla/5.0"}

DEBUG_MODE = False  # Включить для отладки ИИ-ответов в чат
seen_ids = set()

# ----------------- Инициализация бота -----------------
logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


# ----------------- Парсер страницы -----------------
async def fetch_projects(session: ClientSession) -> List[Tuple[str, str, str, str]]:
    """
    Получает список проектов с сайта freelance.ru.

    Args:
        session (ClientSession): Сессия aiohttp для запроса страницы.

    Returns:
        List[Tuple[str, str, str, str]]:
        Список проектов (id, название, ссылка, описание).
    """
    async with session.get(URL, headers=HEADERS) as resp:
        text = await resp.text()

    soup = BeautifulSoup(text, "html.parser")
    cards = soup.find_all("div", class_="project-item-default-card")
    results = []

    for card in cards:
        title_tag = card.find("h2", class_="title")
        if not title_tag:
            continue
        link_tag = title_tag.find("a")
        if not link_tag:
            continue

        link = "https://freelance.ru" + link_tag.get("href", "")
        title = link_tag.get_text(strip=True)
        proj_id = link.split("-")[-1].replace(".html", "")

        desc_tag = card.find("a", class_="description")
        desc = desc_tag.get_text(strip=True) if desc_tag else ""

        results.append((proj_id, title, link, desc))

    return results


# ----------------- Фильтр ключевых слов -----------------
GOOD_KEYWORDS = [
    "телеграм",
    "telegram",
    "бот",
    "бота",
    "чат-бот",
    "чатбот",
    "tg bot",
    "ботов",
]

BAD_KEYWORDS = [
    "ботинки",
    "ботаник",
    "ботва",
    "ботинок",
]


def matches_keywords(title: str, desc: str) -> bool:
    """
    Проверяет, содержат ли текст заголовка и описания "хорошие" ключевые слова
    и не содержат "плохие".

    Args:
        title (str): Заголовок проекта.
        desc (str): Описание проекта.

    Returns:
        bool: True, если проект релевантен, иначе False.
    """
    text = (title + " " + desc).lower()
    words = re.findall(r"\w+", text)

    if any(bad in words for bad in BAD_KEYWORDS):
        return False

    return any(good in words for good in GOOD_KEYWORDS)


# ----------------- Проверка через ИИ -----------------
async def check_with_ai(
    session: ClientSession,
    title: str,
    desc: str,
    chat_id: Optional[int] = None,
) -> bool:
    """
    Проверяет релевантность проекта через AI.

    Args:
        session (ClientSession): Сессия aiohttp для запроса к OpenRouter API.
        title (str): Заголовок проекта.
        desc (str): Описание проекта.
        chat_id (Optional[int]): ID чата для отправки отладочной информации.

    Returns:
        bool: True, если AI определил проект как релевантный, иначе False.
    """
    prompt = (
        "Определи, относится ли проект к разработке Telegram-ботов. "
        "Учитывай только задачи по написанию, настройке,"
        "запуску или правке Telegram-ботов. "
        "Игнорируй любые работы, не связанные с Telegram.\n"
        "Ответь строго одним словом: да или нет.\n\n"
        f"Название: {title}\nОписание: {desc}"
    )

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": 5,
    }

    try:
        async with session.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
        ) as resp:
            raw = await resp.text()
            if DEBUG_MODE and chat_id:
                await bot.send_message(chat_id, f"DEBUG AI RAW:\n{raw[:800]}")

            data = await resp.json()
            try:
                answer = data[
                    "choices"
                    ""][0]["message"]["content"].strip().lower()
            except Exception as e:
                if DEBUG_MODE and chat_id:
                    await bot.send_message(chat_id, f"DEBUG PARSE ERROR:\n{e}")
                return False

            clean = "".join(c for c in answer if c.isalpha())
            return clean == "да"

    except Exception as e:
        if DEBUG_MODE and chat_id:
            await bot.send_message(chat_id, f"DEBUG AI ERROR:\n{e}")
        return False


# ----------------- Отправка вакансий -----------------
async def send_all_projects(chat_id: int):
    """
    Отправляет все текущие вакансии пользователю в чат.

    Args:
        chat_id (int): ID чата пользователя.
    """
    async with ClientSession() as session:
        items = await fetch_projects(session)
        if not items:
            await bot.send_message(chat_id, "На данный момент вакансий нет.")
            return

        sent_any = False
        for pid, title, link, desc in items:
            if pid in seen_ids:
                continue

            if matches_keywords(title, desc):
                seen_ids.add(pid)
                await bot.send_message(chat_id, f"📌 {hbold(title)}\n🔗 {link}")
                sent_any = True
                continue

            is_relevant = await check_with_ai(
                session, title, desc, chat_id if DEBUG_MODE else None
            )
            if is_relevant:
                seen_ids.add(pid)
                await bot.send_message(chat_id, f"📌 {hbold(title)}\n🔗 {link}")
                sent_any = True

        if not sent_any:
            await bot.send_message(chat_id,
                                   "На данный момент подходящих вакансий нет.")


# ----------------- Фоновая проверка -----------------
async def check_new_projects(chat_id: int):
    """
    Фоновая задача для проверки новых вакансий каждый час.

    Args:
        chat_id (int): ID чата пользователя.
    """
    while True:
        async with ClientSession() as session:
            items = await fetch_projects(session)
            for pid, title, link, desc in items:
                if pid in seen_ids:
                    continue

                if matches_keywords(title, desc):
                    seen_ids.add(pid)
                    await bot.send_message(chat_id,
                                           f"🆕 {hbold(title)}\n🔗 {link}")
                    continue

                is_relevant = await check_with_ai(
                    session, title, desc, chat_id if DEBUG_MODE else None
                )
                if is_relevant:
                    seen_ids.add(pid)
                    await bot.send_message(chat_id,
                                           f"🆕 {hbold(title)}\n🔗 {link}")

        await asyncio.sleep(3600)


# ----------------- Хэндлер /start -----------------
@dp.message(CommandStart())
async def start(message: types.Message):
    """
    Хэндлер для команды /start.
    Запускает проверку текущих вакансий и фоновый мониторинг.

    Args:
        message (types.Message): Сообщение пользователя.
    """
    chat_id = message.chat.id
    await message.answer("🚀 Парсер запущен! Проверяю текущие вакансии...")
    await send_all_projects(chat_id)
    asyncio.create_task(check_new_projects(chat_id))
    await message.answer(
        "Мониторинг включён. Каждый час буду отправлять новые вакансии."
    )


# ----------------- Запуск -----------------
async def main():
    """Запуск бота."""
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
