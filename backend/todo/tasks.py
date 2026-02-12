import json
import logging
import os
from urllib import error, request

from celery import shared_task
from django.utils import timezone

from .models import Task


logger = logging.getLogger(__name__)


def _extract_chat_id_from_username(username: str) -> str | None:
    """Извлекает chat_id из username вида tg_<id>."""
    if not username.startswith("tg_"):
        return None
    chat_id = username.removeprefix("tg_").strip()
    return chat_id if chat_id.isdigit() else None


def _send_telegram_message(chat_id: str, text: str, reply_markup: dict | None = None) -> bool:
    """Отправляет сообщение через Telegram Bot API."""
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.warning("TELEGRAM_BOT_TOKEN не задан, отправка уведомлений пропущена.")
        return False

    payload_data = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload_data["reply_markup"] = reply_markup
    
    payload = json.dumps(payload_data).encode("utf-8")
    req = request.Request(
        url=f"https://api.telegram.org/bot{bot_token}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=10) as response:
            return 200 <= response.status < 300
    except (error.URLError, error.HTTPError) as exc:
        logger.warning("Не удалось отправить Telegram-уведомление: %s", exc)
        return False


@shared_task
def send_due_task_notifications() -> int:
    """Отправляет Telegram-уведомления по задачам с наступившим дедлайном."""
    now = timezone.now()
    due_tasks = Task.objects.select_related("user", "category").filter(
        due_date__isnull=False,
        due_date__lte=now,
        is_notified=False,
    )
    notified_count = 0
    for task in due_tasks:
        chat_id = _extract_chat_id_from_username(task.user.username)
        if not chat_id:
            logger.info(
                "Пропуск уведомления: у пользователя %s нет Telegram ID в username",
                task.user.username,
            )
            continue

        due_text = task.due_date.astimezone().strftime("%d.%m.%Y %H:%M") if task.due_date else "-"
        category = task.category.name if task.category else "Без категории"
        text = (
            "🔔 Напоминание по задаче\n\n"
            f"📝 Название: {task.title}\n"
            f"📁 Категория: {category}\n"
            f"📅 Дедлайн: {due_text}"
        )

        reply_markup = {
            "inline_keyboard": [[
                {"text": "✅ Ок", "callback_data": "notification_ok"}
            ]]
        }

        sent = _send_telegram_message(chat_id=chat_id, text=text, reply_markup=reply_markup)
        if not sent:
            continue

        logger.info(
            "Отправлено уведомление | task_id=%s user=%s title=%s due_date=%s",
            task.id,
            task.user.username,
            task.title,
            task.due_date.isoformat() if task.due_date else None,
        )
        task.is_notified = True
        task.notification_sent_at = now
        task.save(update_fields=["is_notified", "notification_sent_at"])
        notified_count += 1
    return notified_count
