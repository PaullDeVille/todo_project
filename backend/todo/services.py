from django.contrib.auth.models import User


def get_or_create_user_by_telegram_id(telegram_id: str) -> User:
    """Возвращает Django-пользователя, связанного с Telegram ID."""
    username = f"tg_{telegram_id}"
    user, _ = User.objects.get_or_create(
        username=username,
        defaults={"first_name": "Telegram", "last_name": str(telegram_id)},
    )
    return user
