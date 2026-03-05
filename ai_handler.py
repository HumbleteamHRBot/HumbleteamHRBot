import os
import anthropic
from knowledge_base import search_knowledge, search_faq


# Клиент Anthropic (ключ берётся из переменной окружения ANTHROPIC_API_KEY)
client = anthropic.Anthropic()

SYSTEM_PROMPT = """Ты — дружелюбный и профессиональный бот-помощник для онбординга новых сотрудников.

Правила:
- Отвечай кратко, тепло и по делу, на русском языке
- Используй информацию из базы знаний, предоставленной ниже
- Если информации нет в базе — честно скажи об этом и предложи обратиться к HR-менеджеру или buddy
- Используй нумерованные списки если нужно перечисление
- Добавляй уместные эмодзи для дружелюбности
- Не упоминай, что ты ИИ или бот — просто помогай
"""


def build_context(query: str) -> str:
    """Собирает контекст из базы знаний для запроса."""
    kb_results = search_knowledge(query)
    faq_results = search_faq(query)

    parts = []

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
