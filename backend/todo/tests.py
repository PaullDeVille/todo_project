from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from .models import Category, Task
from .tasks import send_due_task_notifications


class TaskApiTests(TestCase):
    """Тесты API для CRUD задач и фильтрации по Telegram ID."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(username="tg_1001")
        self.category = Category.objects.create(name="Work")

    def test_create_task_with_telegram_id(self):
        response = self.client.post(
            "/api/tasks/",
            {
                "title": "Finish interview task",
                "category_id": self.category.id,
                "telegram_id": "1001",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Task.objects.count(), 1)
        task = Task.objects.first()
        self.assertEqual(task.user.username, "tg_1001")

    def test_filter_tasks_by_telegram_id(self):
        Task.objects.create(title="Mine", user=self.user, category=self.category)
        other_user = User.objects.create(username="tg_9999")
        Task.objects.create(title="Not mine", user=other_user, category=self.category)
        response = self.client.get("/api/tasks/?telegram_id=1001")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["title"], "Mine")


class CeleryNotificationTests(TestCase):
    """Тесты Celery-уведомлений при наступлении дедлайна."""

    @patch("todo.tasks._send_telegram_message", return_value=True)
    def test_due_tasks_are_marked_notified(self, mocked_sender):
        user = User.objects.create(username="tg_2002")
        task = Task.objects.create(
            title="Overdue",
            user=user,
            due_date=timezone.now() - timedelta(minutes=5),
        )
        processed = send_due_task_notifications()
        task.refresh_from_db()
        self.assertEqual(processed, 1)
        self.assertTrue(task.is_notified)
        self.assertIsNotNone(task.notification_sent_at)
        mocked_sender.assert_called_once()
