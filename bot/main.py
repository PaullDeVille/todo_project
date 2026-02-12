import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram_dialog import DialogManager, StartMode, setup_dialogs

from dialogs import todo_dialog
from states import TodoSG

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

router = Router()


@router.message(Command("start"))
async def start(message: Message, dialog_manager: DialogManager) -> None:
    """Запускает главное меню."""
    user = message.from_user
    logger.info("start | telegram_id=%s username=%s", user.id, user.username or "")
    await dialog_manager.start(TodoSG.menu, mode=StartMode.RESET_STACK)


@router.callback_query(lambda c: c.data == "notification_ok")
async def on_notification_ok(callback: CallbackQuery):
    """Обработчик нажатия кнопки 'Ок' в уведомлении - удаляет сообщение."""
    await callback.message.delete()
    await callback.answer()


async def main() -> None:
    """Запускает режим длинного опроса бота."""
    logger.info("Бот запускается")
    bot = Bot(os.environ["TELEGRAM_BOT_TOKEN"])
    dp = Dispatcher()
    dp.include_router(router)
    dp.include_router(todo_dialog)
    setup_dialogs(dp)
    await dp.start_polling(bot)
    logger.info("Бот остановлен")


if __name__ == "__main__":
    asyncio.run(main())
