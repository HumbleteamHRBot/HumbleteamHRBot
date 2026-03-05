import os
from datetime import datetime, date
import anthropic
from knowledge_base import search_knowledge, search_faq


# Клиент Anthropic (ключ берётся из переменной окружения ANTHROPIC_API_KEY)
client = anthropic.Anthropic()

SYSTEM_PROMPT = """Ты — дружелюбный и профессиональный бот-помощник для онбординга новых сотрудников Humbleteam.

Правила:
- Отвечай кратко, тепло и по делу, на русском языке
- Используй информацию из базы знаний, предоставленной ниже
- Если информации нет в базе — честно скажи об этом и предложи обратиться к HR-менеджеру
- Используй нумерованные списки если нужно перечисление
- Добавляй уместные эмодзи для дружелюбности
- Не упоминай, что ты ИИ или бот — просто помогай
- НИКОГДА не используй markdown-форматирование: никаких **, __, ##, ``` и т.д.
- Для выделения используй ЗАГЛАВНЫЕ БУКВЫ или эмодзи, но не markdown
"""


# ══════════════════════════════════════════════════════════
# ПРАЗДНИКИ ЧЕХИИ — для определения ближайшего
# ══════════════════════════════════════════════════════════

CZECH_HOLIDAYS = [
    (2026, 1, 1, "Новый год / День восстановления независимости Чехии"),
    (2026, 4, 3, "Страстная пятница"),
    (2026, 4, 6, "Пасхальный понедельник"),
    (2026, 5, 1, "День труда"),
    (2026, 5, 8, "День Победы в Европе"),
    (2026, 7, 5, "День святых Кирилла и Мефодия"),
    (2026, 7, 6, "День Яна Гуса"),
    (2026, 9, 28, "День чешской государственности"),
    (2026, 10, 28, "День независимости Чехословакии"),
    (2026, 11, 17, "День борьбы за свободу и демократию"),
    (2026, 12, 24, "Сочельник"),
    (2026, 12, 25, "Рождество"),
    (2026, 12, 26, "День Св. Стефана"),
    # 2027 — чтобы бот работал и в конце 2026 года
    (2027, 1, 1, "Новый год / День восстановления независимости Чехии"),
    (2027, 3, 26, "Страстная пятница"),
    (2027, 3, 29, "Пасхальный понедельник"),
    (2027, 5, 1, "День труда"),
    (2027, 5, 8, "День Победы в Европе"),
    (2027, 7, 5, "День святых Кирилла и Мефодия"),
    (2027, 7, 6, "День Яна Гуса"),
    (2027, 9, 28, "День чешской государственности"),
    (2027, 10, 28, "День независимости Чехословакии"),
    (2027, 11, 17, "День борьбы за свободу и демократию"),
    (2027, 12, 24, "Сочельник"),
    (2027, 12, 25, "Рождество"),
    (2027, 12, 26, "День Св. Стефана"),
]

MONTHS_RU = {
    1: "января", 2: "февраля", 3: "марта", 4: "апреля",
    5: "мая", 6: "июня", 7: "июля", 8: "августа",
    9: "сентября", 10: "октября", 11: "ноября", 12: "декабря",
}

WEEKDAYS_RU = {
    0: "понедельник", 1: "вторник", 2: "среда", 3: "четверг",
    4: "пятница", 5: "суббота", 6: "воскресенье",
}


def get_next_holidays(count: int = 3) -> str:
    """Возвращает ближайшие праздники от сегодняшней даты."""
    today = date.today()
    upcoming = []

    for year, month, day, name in CZECH_HOLIDAYS:
        holiday_date = date(year, month, day)
        if holiday_date >= today:
            days_until = (holiday_date - today).days
            weekday = WEEKDAYS_RU[holiday_date.weekday()]
            date_str = f"{day} {MONTHS_RU[month]}"
            upcoming.append((days_until, date_str, weekday, name))

    upcoming.sort()
    lines = []
    for days_until, date_str, weekday, name in upcoming[:count]:
        if days_until == 0:
            lines.append(f"🎉 СЕГОДНЯ — {name} ({date_str}, {weekday})")
        elif days_until == 1:
            lines.append(f"🗓 ЗАВТРА — {name} ({date_str}, {weekday})")
        else:
            lines.append(f"🗓 {date_str} ({weekday}) — {name} (через {days_until} дн.)")

    return "\n".join(lines) if lines else "Информация о праздниках не найдена."


def build_context(query: str) -> str:
    """Собирает контекст из базы знаний для запроса."""
    kb_results = search_knowledge(query)
    faq_results = search_faq(query)

    parts = []

    # Если спрашивают про ближайший праздник — добавляем актуальную информацию
    q_lower = query.lower()
    holiday_keywords = ["ближайший праздник", "следующий праздник", "когда праздник",
                        "когда выходной", "ближайший выходной", "следующий выходной",
                        "когда не работаем", "когда отдыхаем"]
    if any(kw in q_lower for kw in holiday_keywords):
        next_holidays = get_next_holidays(3)
        parts.append(
            f"БЛИЖАЙШИЕ ПРАЗДНИКИ (от сегодня, {date.today().strftime('%d.%m.%Y')}):\n"
            f"{next_holidays}"
        )

    if kb_results:
        articles_text = "\n\n".join(
            f"[{a['category']}] {a['title']}:\n{a['content']}"
            for a in kb_results
        )
        parts.append(f"СТАТЬИ ИЗ БАЗЫ ЗНАНИЙ:\n{articles_text}")

    if faq_results:
        faq_text = "\n\n".join(
            f"Вопрос: {f['q']}\nОтвет: {f['a']}"
            for f in faq_results
        )
        parts.append(f"FAQ:\n{faq_text}")

    if parts:
        return "КОНТЕКСТ ИЗ БАЗЫ ЗНАНИЙ КОМПАНИИ:\n\n" + "\n\n".join(parts)
    else:
        return "По данному запросу ничего не найдено в базе знаний компании."


def get_ai_response(user_message: str, chat_history: list[dict] = None) -> str:
    """
    Генерирует ответ через Claude API.

    Args:
        user_message: Сообщение пользователя
        chat_history: История чата [{role: "user"/"assistant", content: "..."}]

    Returns:
        Текст ответа
    """
    context = build_context(user_message)
    system = SYSTEM_PROMPT + "\n\n" + context

    # Формируем историю сообщений (последние 8 для контекста)
    messages = []
    if chat_history:
        messages = chat_history[-8:]
    messages.append({"role": "user", "content": user_message})

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=system,
            messages=messages,
        )
        return response.content[0].text

    except anthropic.APIError as e:
        print(f"Claude API error: {e}")
        # Fallback — ответ из локальной базы
        kb = search_knowledge(user_message)
        faq = search_faq(user_message)
        if kb:
            return kb[0]["content"]
        elif faq:
            return faq[0]["a"]
        else:
            return (
                "Извините, сейчас не могу обработать ваш запрос. "
                "Пожалуйста, обратитесь к вашему buddy или HR-менеджеру — они точно помогут! 🤝"
            )
