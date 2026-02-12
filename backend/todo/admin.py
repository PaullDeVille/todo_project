from django.contrib import admin
from django.contrib.auth.models import Group

from .models import Category, Task

admin.site.unregister(Group)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Настройки отображения категорий в админ-панели."""

    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Настройки отображения задач в админ-панели."""

    list_display = (
        "id",
        "title",
        "user",
        "category",
        "created_at",
        "due_date",
        "is_notified",
    )
    list_filter = ("category", "is_notified", "created_at")
    search_fields = ("title", "user__username")
