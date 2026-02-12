from aiogram.fsm.state import State, StatesGroup


class TodoSG(StatesGroup):
    """Состояния диалога управления задачами."""

    menu = State()
    tasks_list = State()
    task_view = State()
    task_edit_menu = State()
    delete_confirm = State()

    add_title = State()
    add_category = State()
    add_date = State()
    add_time = State()

    edit_title = State()
    edit_category = State()
    edit_date = State()
    edit_time = State()
