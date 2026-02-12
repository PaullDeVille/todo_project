from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import MessageInput, TextInput
from aiogram_dialog.widgets.kbd import Button, ScrollingGroup, Select
from aiogram_dialog.widgets.text import Const, Format

from callbacks import (
    add_date_error,
    add_date_success,
    add_time_error,
    add_time_success,
    ask_delete,
    back_to_menu,
    back_to_task_view,
    back_to_tasks_list,
    cancel_delete,
    do_delete,
    edit_date_error,
    edit_date_success,
    edit_time_error,
    edit_time_success,
    go_add_task,
    go_edit_menu,
    go_tasks_list,
    on_add_category_input,
    on_add_title_input,
    on_edit_category_input,
    on_edit_title_input,
    on_task_click,
    start_edit_category,
    start_edit_date,
    start_edit_time,
    start_edit_title,
)
from getters import parse_user_date, parse_user_time
from getters import (
    edit_input_getter,
    menu_getter,
    task_view_getter,
    tasks_list_getter,
)
from states import TodoSG

todo_dialog = Dialog(
    Window(
        Format(
            "📋 Управление задачами\n\n"
            "{flash}"
        ),
        Button(Const("📝 Мои задачи"), id="tasks", on_click=go_tasks_list),
        Button(Const("➕ Добавить задачу"), id="add", on_click=go_add_task),
        state=TodoSG.menu,
        getter=menu_getter,
    ),
    Window(
        Format(
            "📝 Ваши задачи\n"
            "Всего: {count}\n\n"
            "{flash}"
        ),
        ScrollingGroup(
            Select(
                Format("{item[text]}"),
                id="task_select",
                item_id_getter=lambda item: str(item["id"]),
                items="tasks",
                on_click=on_task_click,
            ),
            id="task_scroll",
            width=1,
            height=10,
        ),
        Button(Const("⬅ Назад"), id="back_menu", on_click=back_to_menu),
        state=TodoSG.tasks_list,
        getter=tasks_list_getter,
    ),
    Window(
        Format(
            "{flash}"
            "{task_text}",
            when="found",
        ),
        Button(Const("✏ Изменить"), id="edit", on_click=go_edit_menu, when="found"),
        Button(Const("🗑 Удалить"), id="del", on_click=ask_delete, when="found"),
        Button(Const("⬅ Назад"), id="back_list", on_click=back_to_tasks_list),
        state=TodoSG.task_view,
        getter=task_view_getter,
    ),
    Window(
        Const("✏ Выберите, что изменить:"),
        Button(Const("📝 Изменить название"), id="edit_title", on_click=start_edit_title),
        Button(Const("📁 Изменить категорию"), id="edit_cat", on_click=start_edit_category),
        Button(Const("📅 Изменить дату"), id="edit_date", on_click=start_edit_date),
        Button(Const("⏰ Изменить время"), id="edit_time", on_click=start_edit_time),
        Button(Const("⬅ Назад"), id="back_view", on_click=back_to_task_view),
        state=TodoSG.task_edit_menu,
    ),
    Window(
        Const("🗑 Удалить эту задачу?"),
        Button(Const("✅ Да"), id="confirm_del", on_click=do_delete),
        Button(Const("⬅ Назад"), id="cancel_del", on_click=cancel_delete),
        state=TodoSG.delete_confirm,
    ),
    Window(
        Const(
            "✍ Введите название задачи:"
        ),
        MessageInput(on_add_title_input),
        state=TodoSG.add_title,
    ),
    Window(
        Const(
            "✍ Введите категорию задачи:"
        ),
        MessageInput(on_add_category_input),
        state=TodoSG.add_category,
    ),
    Window(
        Format(
            "✍ Введите дату дедлайна\n"
            "📄 Формат: ДД.ММ.ГГГГ\n"
            "🔸 Пример: 25.12.2024\n\n"
            "{flash}"
        ),
        TextInput(
            id="add_date",
            type_factory=parse_user_date,
            on_success=add_date_success,
            on_error=add_date_error,
        ),
        state=TodoSG.add_date,
        getter=edit_input_getter,
    ),
    Window(
        Format(
            "✍ Введите время дедлайна\n"
            "📄 Формат: ЧЧ:ММ\n"
            "🔸 Пример: 14:30\n\n"
            "{flash}"
        ),
        TextInput(
            id="add_time",
            type_factory=parse_user_time,
            on_success=add_time_success,
            on_error=add_time_error,
        ),
        state=TodoSG.add_time,
        getter=edit_input_getter,
    ),
    Window(
        Format(
            "✍ Введите новое название\n\n"
            "{flash}"
        ),
        MessageInput(on_edit_title_input),
        state=TodoSG.edit_title,
        getter=edit_input_getter,
    ),
    Window(
        Format(
            "✍ Введите новую категорию\n\n"
            "{flash}"
        ),
        MessageInput(on_edit_category_input),
        state=TodoSG.edit_category,
        getter=edit_input_getter,
    ),
    Window(
        Format(
            "✍ Введите новую дату\n"
            "📄 Формат: ДД.ММ.ГГГГ\n\n"
            "{flash}"
        ),
        TextInput(
            id="edit_date",
            type_factory=parse_user_date,
            on_success=edit_date_success,
            on_error=edit_date_error,
        ),
        state=TodoSG.edit_date,
        getter=edit_input_getter,
    ),
    Window(
        Format(
            "✍ Введите новое время\n"
            "📄 Формат: ЧЧ:ММ\n\n"
            "{flash}"
        ),
        TextInput(
            id="edit_time",
            type_factory=parse_user_time,
            on_success=edit_time_success,
            on_error=edit_time_error,
        ),
        state=TodoSG.edit_time,
        getter=edit_input_getter,
    ),
)
