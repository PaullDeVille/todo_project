from datetime import datetime
from typing import Optional

import aiohttp
from aiogram_dialog import DialogManager

TASKS_API_URL = "http://backend:8000/api/tasks/"
CATEGORIES_API_URL = "http://backend:8000/api/categories/"
HTTP_TIMEOUT = aiohttp.ClientTimeout(total=12)


def parse_user_date(value: str) -> datetime.date:
    """Преобразует пользовательскую дату DD.MM.YYYY."""
    return datetime.strptime(value.strip(), "%d.%m.%Y").date()


def parse_user_time(value: str) -> datetime.time:
    """Преобразует пользовательское время HH:MM."""
    return datetime.strptime(value.strip(), "%H:%M").time()


def build_due_date_iso(date_value: str, time_value: str) -> str:
    """Собирает ISO-дату из отдельных строк даты и времени."""
    parsed_date = parse_user_date(date_value)
    parsed_time = parse_user_time(time_value)
    return datetime.combine(parsed_date, parsed_time).isoformat()


async def get_tasks_for_telegram_user(telegram_id: str) -> list[dict]:
    """Возвращает список задач для указанного Telegram ID."""
    async with aiohttp.ClientSession(timeout=HTTP_TIMEOUT) as session:
        async with session.get(TASKS_API_URL, params={"telegram_id": telegram_id}) as response:
            response.raise_for_status()
            return await response.json()


async def get_task_by_id(telegram_id: str, task_id: int) -> Optional[dict]:
    """Возвращает задачу по ID, если она принадлежит пользователю."""
    tasks = await get_tasks_for_telegram_user(telegram_id)
    for task in tasks:
        if int(task["id"]) == int(task_id):
            return task
    return None


async def get_or_create_category_id(session: aiohttp.ClientSession, name: str) -> int:
    """Возвращает ID существующей категории или создает новую."""
    category_name = name.strip()
    async with session.get(CATEGORIES_API_URL) as response:
        response.raise_for_status()
        categories = await response.json()
    for category in categories:
        if category["name"].lower() == category_name.lower():
            return category["id"]
    async with session.post(CATEGORIES_API_URL, json={"name": category_name}) as response:
        response.raise_for_status()
        created = await response.json()
    return created["id"]


async def create_task_for_telegram_user(
    telegram_id: str, title: str, category_name: str, due_date: str
) -> None:
    """Создает задачу в бекенде для пользователя Telegram."""
    async with aiohttp.ClientSession(timeout=HTTP_TIMEOUT) as session:
        category_id = await get_or_create_category_id(session, category_name)
        payload = {
            "title": title,
            "category_id": category_id,
            "telegram_id": telegram_id,
            "due_date": due_date,
        }
        async with session.post(TASKS_API_URL, json=payload) as response:
            response.raise_for_status()


async def update_task_field(
    telegram_id: str,
    task_id: int,
    *,
    title: Optional[str] = None,
    category_name: Optional[str] = None,
    due_date_iso: Optional[str] = None,
) -> None:
    """Обновляет поля задачи пользователя."""
    task = await get_task_by_id(telegram_id, task_id)
    if task is None:
        raise ValueError("Задача не найдена")
    async with aiohttp.ClientSession(timeout=HTTP_TIMEOUT) as session:
        payload: dict = {}
        if title is not None:
            payload["title"] = title
        if category_name is not None:
            payload["category_id"] = await get_or_create_category_id(session, category_name)
        if due_date_iso is not None:
            payload["due_date"] = due_date_iso
        async with session.patch(f"{TASKS_API_URL}{task_id}/", json=payload) as response:
            response.raise_for_status()


async def delete_task(telegram_id: str, task_id: int) -> None:
    """Удаляет задачу пользователя."""
    task = await get_task_by_id(telegram_id, task_id)
    if task is None:
        raise ValueError("Задача не найдена")
    async with aiohttp.ClientSession(timeout=HTTP_TIMEOUT) as session:
        async with session.delete(f"{TASKS_API_URL}{task_id}/") as response:
            response.raise_for_status()


def format_task_card(task: dict) -> str:
    """Формирует карточку задачи для детального просмотра."""
    created = _format_dt(task.get("created_at"))
    due = _format_dt(task.get("due_date")) if task.get("due_date") else "Не задан"
    category = task.get("category_name") or "Без категории"
    return (
        f"📋 Задача: {task.get('title')}\n"
        f"📁 Категория: {category}\n"
        f"📅 Создана: {created}\n"
        f"⏰ Дедлайн: {due}"
    )


def _format_dt(value: Optional[str]) -> str:
    """Преобразует ISO-дату в формат DD.MM.YYYY HH:MM."""
    if not value:
        return "-"
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return dt.strftime("%d.%m.%Y %H:%M")


def _parse_due_or_now(value: str | None) -> datetime:
    """Возвращает datetime дедлайна или текущее время."""
    if not value:
        return datetime.now()
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


async def menu_getter(dialog_manager: DialogManager, **kwargs):
    """Getter для главного меню."""
    flash = dialog_manager.dialog_data.pop("flash", "")
    if flash:
        flash = flash + "\n\n"
    return {"flash": flash}


async def tasks_list_getter(dialog_manager: DialogManager, **kwargs):
    """Getter для списка задач."""
    telegram_id = str(dialog_manager.event.from_user.id)
    try:
        tasks = await get_tasks_for_telegram_user(telegram_id)
    except Exception:
        return {
            "tasks": [],
            "count": 0,
            "flash": "❌ Не удалось получить задачи\n\n",
        }

    items = []
    for task in tasks:
        title = (task.get("title") or "Без названия")[:35]
        items.append({"id": task["id"], "text": title})

    flash = dialog_manager.dialog_data.pop("flash", "")
    if flash:
        flash = flash + "\n\n"

    return {
        "tasks": items,
        "count": len(items),
        "flash": flash,
    }


async def task_view_getter(dialog_manager: DialogManager, **kwargs):
    """Getter для карточки задачи."""
    telegram_id = str(dialog_manager.event.from_user.id)
    task_id = dialog_manager.dialog_data.get("task_id")

    flash = dialog_manager.dialog_data.pop("flash", "")
    if flash:
        flash = flash + "\n\n"

    if not task_id:
        return {"found": False, "flash": flash}

    try:
        task = await get_task_by_id(telegram_id, int(task_id))
    except Exception:
        return {"found": False, "flash": flash}

    if not task:
        return {"found": False, "flash": flash}

    return {
        "found": True,
        "flash": flash,
        "task_text": format_task_card(task),
    }


async def edit_input_getter(dialog_manager: DialogManager, **kwargs):
    """Getter для окон редактирования с flash."""
    flash = dialog_manager.dialog_data.get("flash", "")
    if flash:
        flash = flash + "\n"
    return {"flash": flash}
