Telegram Freelance Bot / Телеграм Фриланс Бот
English
Description

This Telegram bot monitors freelance.ru for new projects related to Telegram bot development. It filters projects using keywords and AI to determine relevance, then sends notifications to users via Telegram.

Features

Fetches current projects from freelance.ru

Filters projects based on good/bad keywords

Uses AI (OpenRouter API) for more accurate filtering

Sends relevant projects to Telegram users

Background monitoring every hour

Requirements

Python 3.10+

Aiogram

Aiohttp

BeautifulSoup4

Installation
git clone https://github.com/yourusername/telegram-freelance-bot.git
cd telegram-freelance-bot
pip install -r requirements.txt

Configuration

Edit the following constants in the script:

API_TOKEN = "YOUR_TELEGRAM_BOT_API_TOKEN"
OPENROUTER_API_KEY = "YOUR_OPENROUTER_API_KEY"
DEBUG_MODE = False  # Set True to enable AI debug messages

Usage

Run the bot:

python bot.py


Then, start the bot in Telegram using /start. It will:

Send all relevant current projects.

Monitor new projects every hour and notify you.

Русский
Описание

Этот Telegram-бот мониторит сайт freelance.ru на предмет новых проектов, связанных с разработкой Telegram-ботов.
Он фильтрует проекты с помощью ключевых слов и ИИ, чтобы определить их релевантность, и отправляет уведомления пользователям через Telegram.

Возможности

Получение текущих проектов с freelance.ru

Фильтрация проектов по "хорошим" и "плохим" ключевым словам

Проверка проектов через ИИ (OpenRouter API)

Отправка релевантных проектов пользователям в Telegram

Фоновый мониторинг каждый час

Требования

Python 3.10+

Aiogram

Aiohttp

BeautifulSoup4

Установка
git clone https://github.com/yourusername/telegram-freelance-bot.git
cd telegram-freelance-bot
pip install -r requirements.txt

Настройка

Установите следующие константы в коде:

API_TOKEN = "ВАШ_TELEGRAM_BOT_API_TOKEN"
OPENROUTER_API_KEY = "ВАШ_OPENROUTER_API_KEY"
DEBUG_MODE = False  # Включить True для отладки ИИ

Использование

Запустите бота:

python bot.py


Затем отправьте команду /start в Telegram. Бот:

Отправит все текущие релевантные проекты.

Будет проверять новые проекты каждый час и уведомлять вас.