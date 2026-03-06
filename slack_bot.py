import os
import logging
from collections import defaultdict

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from ai_handler import get_ai_response
from knowledge_base import FAQ, KNOWLEDGE_BASE

# ══════════════════════════════════════════════════════════
# НАСТРОЙКА
# ══════════════════════════════════════════════════════════

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = App(token=os.environ["SLACK_BOT_TOKEN"])

# Хранилище истории чатов (в памяти)
chat_histories: dict[str, list[dict]] = defaultdict(list)
MAX_HISTORY = 10


# ══════════════════════════════════════════════════════════
# КОМАНДА /onboarding — главное меню
# ══════════════════════════════════════════════════════════

@app.command("/hrbot")
def handle_onboarding_command(ack, say):
    ack()
    say(
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Привет! :wave: Я бот-помощник для новых сотрудников Humbleteam.\n\nЗадай вопрос в личные сообщения или выбери раздел:"
                },
            },
            {
                "type": "actions",
                "elements": [
                    {"type": "button", "text": {"type": "plain_text", "text": ":question: FAQ"}, "action_id": "show_faq", "value": "faq"},
                    {"type": "button", "text": {"type": "plain_text", "text": ":books: База знаний"}, "action_id": "show_kb", "value": "kb"},
                    {"type": "button", "text": {"type": "plain_text", "text": ":arrows_counterclockwise: Сбросить историю"}, "action_id": "reset_history", "value": "reset"},
                ],
            },
        ],
        text="Привет! Я бот-помощник для онбординга.",
    )


# ══════════════════════════════════════════════════════════
# КНОПКА FAQ
# ══════════════════════════════════════════════════════════

@app.action("show_faq")
def handle_show_faq(ack, say):
    ack()
    blocks = [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": ":question: *Частые вопросы новых сотрудников*"},
        }
    ]
    for i, item in enumerate(FAQ):
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*{item['q']}*"},
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": "Ответ"},
                "action_id": f"faq_{i}",
                "value": str(i),
            },
        })
    say(blocks=blocks, text="FAQ")


@app.action({"action_id": "faq_0"})
@app.action({"action_id": "faq_1"})
@app.action({"action_id": "faq_2"})
@app.action({"action_id": "faq_3"})
@app.action({"action_id": "faq_4"})
@app.action({"action_id": "faq_5"})
@app.action({"action_id": "faq_6"})
@app.action({"action_id": "faq_7"})
@app.action({"action_id": "faq_8"})
@app.action({"action_id": "faq_9"})
@app.action({"action_id": "faq_10"})
@app.action({"action_id": "faq_11"})
@app.action({"action_id": "faq_12"})
@app.action({"action_id": "faq_13"})
@app.action({"action_id": "faq_14"})
def handle_faq_item(ack, action, say):
    ack()
    idx = int(action["value"])
    if 0 <= idx < len(FAQ):
        item = FAQ[idx]
        say(f":question: *{item['q']}*\n\n{item['a']}")


# ══════════════════════════════════════════════════════════
# КНОПКА БАЗА ЗНАНИЙ
# ══════════════════════════════════════════════════════════

@app.action("show_kb")
def handle_show_kb(ack, say):
    ack()
    blocks = [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": ":books: *База знаний — выбери раздел:*"},
        }
    ]
    for i, cat in enumerate(KNOWLEDGE_BASE["categories"]):
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"{cat['icon']} *{cat['title']}*"},
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": "Открыть"},
                "action_id": f"kb_{i}",
                "value": str(i),
            },
        })
    say(blocks=blocks, text="База знаний")


# Обработчики для категорий базы знаний
import re

@app.action(re.compile(r"^kb_\d+$"))
def handle_kb_category(ack, action, say):
    ack()
    idx = int(action["value"])
    categories = KNOWLEDGE_BASE["categories"]
    if 0 <= idx < len(categories):
        cat = categories[idx]
        blocks = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"{cat['icon']} *{cat['title']}*"},
            }
        ]
        for j, article in enumerate(cat["articles"]):
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*{article['title']}*"},
                "accessory": {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Читать"},
                    "action_id": f"article_{idx}_{j}",
                    "value": f"{idx}_{j}",
                },
            })
        say(blocks=blocks, text=cat["title"])


@app.action(re.compile(r"^article_\d+_\d+$"))
def handle_article(ack, action, say):
    ack()
    parts = action["value"].split("_")
    cat_idx, art_idx = int(parts[0]), int(parts[1])
    categories = KNOWLEDGE_BASE["categories"]
    if 0 <= cat_idx < len(categories):
        cat = categories[cat_idx]
        if 0 <= art_idx < len(cat["articles"]):
            article = cat["articles"][art_idx]
            say(f"{cat['icon']} *{article['title']}*\n\n{article['content']}")


# ══════════════════════════════════════════════════════════
# СБРОС ИСТОРИИ
# ══════════════════════════════════════════════════════════

@app.action("reset_history")
def handle_reset(ack, say, body):
    ack()
    user_id = body["user"]["id"]
    chat_histories[user_id].clear()
    say(":arrows_counterclockwise: История диалога очищена. Задай новый вопрос!")


# ══════════════════════════════════════════════════════════
# ОБРАБОТКА СООБЩЕНИЙ (DM)
# ══════════════════════════════════════════════════════════

@app.event("message")
def handle_message(event, say):
    """Обработка личных сообщений боту."""
    # Игнорируем сообщения от ботов
    if event.get("bot_id") or event.get("subtype"):
        return

    user_text = event.get("text", "").strip()
    if not user_text:
        return

    user_id = event.get("user", "unknown")

    # Получаем историю
    history = chat_histories[user_id]

    # Генерируем ответ через Claude AI
    response = get_ai_response(user_text, history)

    # Сохраняем в историю
    history.append({"role": "user", "content": user_text})
    history.append({"role": "assistant", "content": response})

    # Обрезаем если слишком длинная
    if len(history) > MAX_HISTORY * 2:
        chat_histories[user_id] = history[-(MAX_HISTORY * 2):]

    say(response)


# ══════════════════════════════════════════════════════════
# App Home — приветствие при открытии бота
# ══════════════════════════════════════════════════════════

@app.event("app_home_opened")
def update_home_tab(client, event):
    """Показывает приветствие на вкладке Home бота."""
    client.views_publish(
        user_id=event["user"],
        view={
            "type": "home",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": ":wave: *Добро пожаловать в Humbleteam!*\n\nЯ бот-помощник для новых сотрудников. Напиши мне в личные сообщения — помогу с любым вопросом об онбординге."
                    },
                },
                {"type": "divider"},
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            ":speech_balloon: *Что я умею:*\n\n"
                            ":clock1: Рабочее время и график\n"
                            ":palm_tree: Отпуск и больничный\n"
                            ":key: Доступы и инструменты (Google, Slack, Figma, Clockify, 1Password)\n"
                            ":stopwatch: Трекинг времени в Clockify\n"
                            ":moneybag: Оплата и инвойсы\n"
                            ":calendar: Праздники Чехии\n\n"
                            "Просто напиши вопрос — я найду ответ!"
                        ),
                    },
                },
                {"type": "divider"},
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": "Если я не смогу помочь — обратись к HR-менеджеру Кате Миловой (@kate.m) :handshake:"
                        }
                    ],
                },
            ],
        },
    )


# ══════════════════════════════════════════════════════════
# ЗАПУСК
# ══════════════════════════════════════════════════════════

if __name__ == "__main__":
    logger.info(":rocket: Slack-бот запускается...")
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
