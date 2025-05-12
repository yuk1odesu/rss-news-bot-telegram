import os
import feedparser
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import CallbackQuery
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Настройки RSS-каналов
RSS_FEEDS = {
    "general": os.getenv("RSS_GENERAL"),
    "technology": os.getenv("RSS_TECHNOLOGY"),
    "sports": os.getenv("RSS_SPORTS"),
    "health": os.getenv("RSS_HEALTH"),
    "entertainment": os.getenv("RSS_ENTERTAINMENT")
}

# Бот
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Категории новостей
CATEGORIES = {
    "general": "🌍 World news",
    "technology": "🧩 Technology",
    "sports": "⚽ Sports",
    "health": "🩺 Health",
    "entertainment": "🎬 Gaming"
}

# Функция получения новостей
def get_rss_news(category="general"):
    rss_url = RSS_FEEDS.get(category)
    if not rss_url:
        print(f"[Ошибка] Отсутствует URL для категории {category}")
        return []

    print(f"[DEBUG] Запрос к RSS: {rss_url}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36"
    }

    try:
        response = requests.get(rss_url, headers=headers, timeout=10)
        print(f"[DEBUG] Статус ответа: {response.status_code}")

        if response.status_code != 200:
            return []

        feed = feedparser.parse(response.content)
        entries = feed.entries[:5]

        if not entries:
            print("[Ошибка] Нет новостей в RSS-канале")
            return []

        print(f"[DEBUG] Получено {len(entries)} новостей")

        return [
            {
                "title": entry.title,
                "url": entry.link,
                "published": entry.published if hasattr(entry, "published") else "Неизвестно"
            }
            for entry in entries
        ]

    except Exception as e:
        print("[Ошибка при парсинге RSS]:", str(e))
        return []


# Функция создания клавиатуры с кнопками "Обновить" и "Выбрать другую категорию"
def get_news_keyboard(category):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Update feed", callback_data=f"rss_{category}")],
        [InlineKeyboardButton(text="⬅️ Choose another subreddit", callback_data="back_to_categories")]
    ])


# Команда /start
@dp.message(Command(commands=["start"]))
async def start(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=name, callback_data=f"rss_{topic}")]
        for topic, name in CATEGORIES.items()
    ])
    await message.answer("📰 Hello there! Choose the subreddit:", reply_markup=keyboard)

# Обработка нажатий на категории
@dp.callback_query(F.data.startswith("rss_"))
async def send_news(callback: CallbackQuery):
    category = callback.data.replace("rss_", "")
    news_list = get_rss_news(category)

    if not news_list:
        await callback.message.answer("❌ Unable to load the news.")
        return

    result = f"🗞 Новости по теме «{CATEGORIES[category]}»:\n\n"
    for i, news in enumerate(news_list, start=1):
        result += f"{i}. {news['title']}\nДата: {news['published']}\n🔗 {news['url']}\n\n"

    # Отправляем новости с кнопками
    await callback.message.edit_text(result, reply_markup=get_news_keyboard(category))


# Обработка кнопки "⬅️ Выбрать другую категорию"
@dp.callback_query(F.data == "back_to_categories")
async def back_to_categories(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=name, callback_data=f"rss_{topic}")]
        for topic, name in CATEGORIES.items()
    ])
    await callback.message.edit_text("📰 Choose your subreddit:", reply_markup=keyboard)


# Запуск бота
if __name__ == "__main__":
    import asyncio
    import requests

    print("Бот запущен...")
    dp.run_polling(bot)