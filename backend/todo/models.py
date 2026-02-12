import os
import threading
import time

from django.contrib.auth.models import User
from django.db import models

_PK_LOCK = threading.Lock()
_PK_COUNTER = 0


def gen_pk() -> int:
    """Генерирует уникальные сортируемые BigInt ID без последовательностей БД."""
    global _PK_COUNTER
    ts_ms = int(time.time() * 1000)
    pid_bits = os.getpid() & 0x3FF
    with _PK_LOCK:
        _PK_COUNTER = (_PK_COUNTER + 1) & 0xFFF
        counter_bits = _PK_COUNTER
    return (ts_ms << 22) | (pid_bits << 12) | counter_bits

class Category(models.Model):
    id = models.BigIntegerField(primary_key=True, default=gen_pk, editable=False)
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Task(models.Model):
    id = models.BigIntegerField(primary_key=True, default=gen_pk, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=255)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="tasks"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(null=True, blank=True)
    is_notified = models.BooleanField(default=False)
    notification_sent_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} ({self.user.username})"
