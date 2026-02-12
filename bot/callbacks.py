import logging
from datetime import datetime

from aiohttp import ClientError, ClientResponseError
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, ShowMode

from getters import (
    build_due_date_iso,
    create_task_for_telegram_user,
    delete_task,
    get_task_by_id,
    parse_user_date,
    parse_user_time,
    update_task_field,
    _parse_due_or_now,
)
from states import TodoSG

logger = logging.getLogger(__name__)


async def go_tasks_list(c: CallbackQuery, button, manager: DialogManager):
    """Переход к списку задач."""
    await manager.switch_to(TodoSG.tasks_list)


async def go_add_task(c: CallbackQuery, button, manager: DialogManager):
    """Начать добавление задачи."""
    manager.dialog_data.pop("add_title", None)
    manager.dialog_data.pop("add_category", None)
    manager.dialog_data.pop("add_date", None)
    await manager.switch_to(TodoSG.add_title)


async def back_to_menu(c: CallbackQuery, button, manager: DialogManager):
    """Возврат в главное меню."""
    await manager.switch_to(TodoSG.menu)


async def back_to_tasks_list(c: CallbackQuery, button, manager: DialogManager):
    """Возврат к списку задач."""
    await manager.switch_to(TodoSG.tasks_list)


async def back_to_task_view(c: CallbackQuery, button, manager: DialogManager):
    """Возврат к просмотру задачи."""
    await manager.switch_to(TodoSG.task_view)


async def on_task_click(c: CallbackQuery, widget, manager: DialogManager, item_id: str):
    """Обработка клика на задачу в списке."""
    manager.dialog_data["task_id"] = int(item_id)
    logger.debug("task_view | telegram_id=%s task_id=%s", c.from_user.id, item_id)
    await manager.switch_to(TodoSG.task_view)


async def go_edit_menu(c: CallbackQuery, button, manager: DialogManager):
    """Открыть меню редактирования."""
    await manager.switch_to(TodoSG.task_edit_menu)


async def ask_delete(c: CallbackQuery, button, manager: DialogManager):
    """Подтверждение удаления."""
    await manager.switch_to(TodoSG.delete_confirm)


async def do_delete(c: CallbackQuery, button, manager: DialogManager):
    """Удаление задачи."""
    telegram_id = str(c.from_user.id)
    task_id = manager.dialog_data.get("task_id")

    try:
        await delete_task(telegram_id, int(task_id))
        manager.dialog_data["flash"] = "✅ Задача удалена"
        logger.info("task_deleted | telegram_id=%s task_id=%s", telegram_id, task_id)
    except (ValueError, ClientError, ClientResponseError) as e:
        manager.dialog_data["flash"] = "❌ Не удалось удалить задачу"
        logger.warning("task_delete_failed | telegram_id=%s task_id=%s error=%s", telegram_id, task_id, e)

    await manager.switch_to(TodoSG.tasks_list)


async def cancel_delete(c: CallbackQuery, button, manager: DialogManager):
    """Отмена удаления."""
    await manager.switch_to(TodoSG.task_view)


async def start_edit_title(c: CallbackQuery, button, manager: DialogManager):
    """Начать редактирование названия."""
    await manager.switch_to(TodoSG.edit_title)


async def start_edit_category(c: CallbackQuery, button, manager: DialogManager):
    """Начать редактирование категории."""
    await manager.switch_to(TodoSG.edit_category)


async def start_edit_date(c: CallbackQuery, button, manager: DialogManager):
    """Начать редактирование даты."""
    await manager.switch_to(TodoSG.edit_date)


async def start_edit_time(c: CallbackQuery, button, manager: DialogManager):
    """Начать редактирование времени."""
    await manager.switch_to(TodoSG.edit_time)


async def on_add_title_input(m: Message, widget, manager: DialogManager):
    """Обработка ввода названия новой задачи."""
    manager.dialog_data["add_title"] = m.text.strip()
    await manager.switch_to(TodoSG.add_category)


async def on_add_category_input(m: Message, widget, manager: DialogManager):
    """Обработка ввода категории новой задачи."""
    manager.show_mode = ShowMode.DELETE_AND_SEND
    manager.dialog_data["add_category"] = m.text.strip()
    await manager.switch_to(TodoSG.add_date)


async def add_date_error(m: Message, widget, manager: DialogManager, error: ValueError):
    """Ошибка валидации даты при добавлении задачи."""
    logger.info("validation_error | field=date telegram_id=%s value=%s", m.from_user.id, m.text)
    await m.answer("❌ Неверный формат даты. Используйте ДД.ММ.ГГГГ (например: 25.12.2024)")


async def add_date_success(m: Message, widget, manager: DialogManager, data):
    """Успешный ввод даты при добавлении задачи."""
    manager.show_mode = ShowMode.DELETE_AND_SEND
    manager.dialog_data["add_date"] = m.text.strip()
    await manager.switch_to(TodoSG.add_time)


async def add_time_error(m: Message, widget, manager: DialogManager, error: ValueError):
    """Ошибка валидации времени при добавлении задачи."""
    logger.info("validation_error | field=time telegram_id=%s value=%s", m.from_user.id, m.text)
    await m.answer("❌ Неверный формат времени. Используйте ЧЧ:ММ (например: 14:30)")


async def add_time_success(m: Message, widget, manager: DialogManager, data):
    """Успешный ввод времени и создание задачи."""
    manager.show_mode = ShowMode.DELETE_AND_SEND
    telegram_id = str(m.from_user.id)
    title = manager.dialog_data["add_title"]
    category = manager.dialog_data["add_category"]
    date_value = manager.dialog_data["add_date"]
    time_value = m.text.strip()
    try:
        due_date_iso = build_due_date_iso(date_value, time_value)
        await create_task_for_telegram_user(telegram_id, title, category, due_date_iso)
        manager.dialog_data["flash"] = "✅ Задача успешно создана"
        logger.info("task_created | telegram_id=%s title=%s due=%s", telegram_id, title, due_date_iso)
    except (ClientError, ClientResponseError) as e:
        manager.dialog_data["flash"] = "❌ Не удалось создать задачу"
        logger.warning("task_create_failed | telegram_id=%s title=%s error=%s", telegram_id, title, e)
    await manager.switch_to(TodoSG.menu)


async def on_edit_title_input(m: Message, widget, manager: DialogManager):
    """Изменение названия задачи."""
    manager.show_mode = ShowMode.DELETE_AND_SEND
    telegram_id = str(m.from_user.id)
    task_id = manager.dialog_data["task_id"]

    try:
        await update_task_field(telegram_id, task_id, title=m.text.strip())
        manager.dialog_data["flash"] = "✅ Название обновлено"
        logger.info("task_updated | telegram_id=%s task_id=%s field=title", telegram_id, task_id)
    except (ClientError, ClientResponseError, ValueError) as e:
        manager.dialog_data["flash"] = "❌ Не удалось обновить название"
        logger.warning("task_update_failed | telegram_id=%s task_id=%s field=title error=%s", telegram_id, task_id, e)

    await manager.switch_to(TodoSG.task_view)


async def on_edit_category_input(m: Message, widget, manager: DialogManager):
    """Изменение категории задачи."""
    manager.show_mode = ShowMode.DELETE_AND_SEND
    telegram_id = str(m.from_user.id)
    task_id = manager.dialog_data["task_id"]

    try:
        await update_task_field(telegram_id, task_id, category_name=m.text.strip())
        manager.dialog_data["flash"] = "✅ Категория обновлена"
        logger.info("task_updated | telegram_id=%s task_id=%s field=category", telegram_id, task_id)
    except (ClientError, ClientResponseError, ValueError) as e:
        manager.dialog_data["flash"] = "❌ Не удалось обновить категорию"
        logger.warning("task_update_failed | telegram_id=%s task_id=%s field=category error=%s", telegram_id, task_id, e)

    await manager.switch_to(TodoSG.task_view)


async def edit_date_error(m: Message, widget, manager: DialogManager, error: ValueError):
    """Ошибка валидации даты при редактировании."""
    logger.info("validation_error | field=date edit telegram_id=%s value=%s", m.from_user.id, m.text)
    await m.answer("❌ Неверный формат даты. Используйте ДД.ММ.ГГГГ (например: 25.12.2024)")


async def edit_date_success(m: Message, widget, manager: DialogManager, data):
    """Успешный ввод даты при редактировании задачи."""
    manager.show_mode = ShowMode.DELETE_AND_SEND
    telegram_id = str(m.from_user.id)
    task_id = manager.dialog_data["task_id"]
    new_date = data
    try:
        task = await get_task_by_id(telegram_id, task_id)
        if not task:
            manager.dialog_data["flash"] = "❌ Задача не найдена"
            await manager.switch_to(TodoSG.tasks_list)
            return
        base_dt = _parse_due_or_now(task.get("due_date"))
        due_date_iso = datetime.combine(new_date, base_dt.time()).isoformat()
        await update_task_field(telegram_id, task_id, due_date_iso=due_date_iso)
        manager.dialog_data["flash"] = "✅ Дата обновлена"
        logger.info("task_updated | telegram_id=%s task_id=%s field=due_date", telegram_id, task_id)
    except (ClientError, ClientResponseError, ValueError) as e:
        manager.dialog_data["flash"] = "❌ Не удалось обновить дату"
        logger.warning("task_update_failed | telegram_id=%s task_id=%s field=due_date error=%s", telegram_id, task_id, e)
    await manager.switch_to(TodoSG.task_view)


async def edit_time_error(m: Message, widget, manager: DialogManager, error: ValueError):
    """Ошибка валидации времени при редактировании."""
    logger.info("validation_error | field=time edit telegram_id=%s value=%s", m.from_user.id, m.text)
    await m.answer("❌ Неверный формат времени. Используйте ЧЧ:ММ (например: 14:30)")


async def edit_time_success(m: Message, widget, manager: DialogManager, data):
    """Успешный ввод времени при редактировании задачи."""
    manager.show_mode = ShowMode.DELETE_AND_SEND
    telegram_id = str(m.from_user.id)
    task_id = manager.dialog_data["task_id"]
    new_time = data
    try:
        task = await get_task_by_id(telegram_id, task_id)
        if not task:
            manager.dialog_data["flash"] = "❌ Задача не найдена"
            await manager.switch_to(TodoSG.tasks_list)
            return
        base_dt = _parse_due_or_now(task.get("due_date"))
        due_date_iso = datetime.combine(base_dt.date(), new_time).isoformat()
        await update_task_field(telegram_id, task_id, due_date_iso=due_date_iso)
        manager.dialog_data["flash"] = "✅ Время обновлено"
        logger.info("task_updated | telegram_id=%s task_id=%s field=due_time", telegram_id, task_id)
    except (ClientError, ClientResponseError, ValueError) as e:
        manager.dialog_data["flash"] = "❌ Не удалось обновить время"
        logger.warning("task_update_failed | telegram_id=%s task_id=%s field=due_time error=%s", telegram_id, task_id, e)
    await manager.switch_to(TodoSG.task_view)
