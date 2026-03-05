import os
import asyncio
import logging
from collections import defaultdict

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from ai_handler import get_ai_response
from knowledge_base import FAQ, KNOWLEDGE_BASE

# ══════════════════════════════════════════════════════════
# НАСТРОЙКА
# ══════════════════════════════════════════════════════════

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не задан! Добавьте его в переменные окружения.")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Хранилище истории чатов (в памяти, сбрасывается при перезапуске)
chat_histories: dict[int, list[dict]] = defaultdict(list)
MAX_HISTORY = 10  # Максимум сообщений в истории


# ══════════════════════════════════════════════════════════
# КОМАНДЫ
# ══════════════════════════════════════════════════════════

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Приветствие при первом запуске."""
    chat_histories[message.chat.id].clear()

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❓ Частые вопросы", callback_data="faq")],
        [InlineKeyboardButton(text="📚 База знаний", callback_data="kb")],
        [InlineKeyboardButton(text="🔄 Начать сначала", callback_data="reset")],
    ])

    await message.answer(
        "Привет! 👋 Я бот-помощник для новых сотрудников.\n\n"
        "Могу ответить на вопросы об онбординге, помочь найти нужную "
        "информацию или подсказать, к кому обратиться.\n\n"
        "Просто напишите свой вопрос, или выберите раздел:",
        reply_markup=keyboard,
    )


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Справка по командам."""
    await message.answer(
        "🤖 Что я умею:\n\n"
        "💬 Просто напишите вопрос — я найду ответ в базе знаний\n"
        "/faq — показать частые вопросы\n"
        "/kb — показать разделы базы знаний\n"
        "/reset — очистить историю диалога\n"
        "/help — эта справка\n\n"
        "Если я не смогу помочь — подскажу, к кому обратиться 🤝"
    )


@dp.message(Command("faq"))
async def cmd_faq(message: types.Message):
    """Показать FAQ."""
    buttons = []
    for i, item in enumerate(FAQ):
        buttons.append([InlineKeyboardButton(
            text=f"❓ {item['q']}",
            callback_data=f"faq_{i}",
        )])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("Частые вопросы новых сотрудников:", reply_markup=keyboard)


@dp.message(Command("kb"))
async def cmd_kb(message: types.Message):
    """Показать разделы базы знаний."""
    buttons = []
    for i, cat in enumerate(KNOWLEDGE_BASE["categories"]):
        buttons.append([InlineKeyboardButton(
            text=f"{cat['icon']} {cat['title']}",
            callback_data=f"kb_{i}",
        )])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("📚 Разделы базы знаний:", reply_markup=keyboard)


@dp.message(Command("reset"))
async def cmd_reset(message: types.Message):
    """Очистить историю диалога."""
    chat_histories[message.chat.id].clear()
    await message.answer("🔄 История диалога очищена. Задайте новый вопрос!")


# ══════════════════════════════════════════════════════════
# КНОПКИ (CALLBACKS)
# ══════════════════════════════════════════════════════════

@dp.callback_query(lambda c: c.data == "faq")
async def cb_faq(callback: types.CallbackQuery):
    """Показать FAQ по кнопке."""
    buttons = []
    for i, item in enumerate(FAQ):
        buttons.append([InlineKeyboardButton(
            text=f"❓ {item['q']}",
            callback_data=f"faq_{i}",
        )])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer("Частые вопросы:", reply_markup=keyboard)
    await callback.answer()


@dp.callback_query(lambda c: c.data and c.data.startswith("faq_"))
async def cb_faq_item(callback: types.CallbackQuery):
    """Показать ответ на конкретный FAQ."""
    idx = int(callback.data.split("_")[1])
    if 0 <= idx < len(FAQ):
        item = FAQ[idx]
        await callback.message.answer(f"❓ {item['q']}\n\n{item['a']}")
    await callback.answer()


@dp.callback_query(lambda c: c.data == "kb")
async def cb_kb(callback: types.CallbackQuery):
    """Показать базу знаний по кнопке."""
    buttons = []
    for i, cat in enumerate(KNOWLEDGE_BASE["categories"]):
        buttons.append([InlineKeyboardButton(
            text=f"{cat['icon']} {cat['title']}",
            callback_data=f"kb_{i}",
        )])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer("📚 Разделы:", reply_markup=keyboard)
    await callback.answer()


@dp.callback_query(lambda c: c.data and c.data.startswith("kb_"))
async def cb_kb_category(callback: types.CallbackQuery):
    """Показать статьи категории."""
    idx = int(callback.data.split("_")[1])
    categories = KNOWLEDGE_BASE["categories"]
    if 0 <= idx < len(categories):
        cat = categories[idx]
        buttons = []
        for j, article in enumerate(cat["articles"]):
            buttons.append([InlineKeyboardButton(
                text=article["title"],
                callback_data=f"article_{idx}_{j}",
            )])
        buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="kb")])

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await callback.message.answer(
            f"{cat['icon']} {cat['title']}:",
            reply_markup=keyboard,
        )
    await callback.answer()


@dp.callback_query(lambda c: c.data and c.data.startswith("article_"))
async def cb_article(callback: types.CallbackQuery):
    """Показать содержимое статьи."""
    parts = callback.data.split("_")
    cat_idx, art_idx = int(parts[1]), int(parts[2])
    categories = KNOWLEDGE_BASE["categories"]
    if 0 <= cat_idx < len(categories):
        cat = categories[cat_idx]
        if 0 <= art_idx < len(cat["articles"]):
            article = cat["articles"][art_idx]
            await callback.message.answer(
                f"{cat['icon']} {article['title']}\n\n{article['content']}"
            )
    await callback.answer()


@dp.callback_query(lambda c: c.data == "reset")
async def cb_reset(callback: types.CallbackQuery):
    """Очистить историю по кнопке."""
    chat_histories[callback.message.chat.id].clear()
    await callback.message.answer("🔄 История очищена. Задайте новый вопрос!")
    await callback.answer()


# ══════════════════════════════════════════════════════════
# ОБРАБОТКА СООБЩЕНИЙ
# ══════════════════════════════════════════════════════════

@dp.message()
async def handle_message(message: types.Message):
    """Обработка обычных текстовых сообщений."""
    if not message.text:
        await message.answer("Пока я умею работать только с текстовыми сообщениями 📝")
        return

    user_text = message.text.strip()
    if not user_text:
        return

    # Показываем индикатор "печатает..."
    await bot.send_chat_action(message.chat.id, "typing")

    # Получаем историю чата
    history = chat_histories[message.chat.id]

    # Генерируем ответ через Claude AI
    response = get_ai_response(user_text, history)

    # Сохраняем в историю
    history.append({"role": "user", "content": user_text})
    history.append({"role": "assistant", "content": response})

    # Обрезаем историю если слишком длинная
    if len(history) > MAX_HISTORY * 2:
        chat_histories[message.chat.id] = history[-(MAX_HISTORY * 2):]

    # Отправляем ответ
    await message.answer(response)


# ══════════════════════════════════════════════════════════
# ЗАПУСК
# ══════════════════════════════════════════════════════════

async def main():
    logger.info("🚀 Бот запускается...")
    # Удаляем старые вебхуки если были
    await bot.delete_webhook(drop_pending_updates=True)
    # Запускаем polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
