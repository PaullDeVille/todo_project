from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Category, Task
from .services import get_or_create_user_by_telegram_id


class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор для операций создания, чтения, обновления и удаления категорий."""

    class Meta:
        model = Category
        fields = "__all__"

class TaskSerializer(serializers.ModelSerializer):
    """Сериализатор задач с поддержкой привязки Telegram-пользователя."""

    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), required=False, allow_null=True
    )
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source="category",
        write_only=True,
        required=False,
        allow_null=True,
    )
    telegram_id = serializers.CharField(write_only=True, required=False)
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Task
        fields = [
            "id",
            "user",
            "title",
            "category",
            "category_id",
            "category_name",
            "created_at",
            "due_date",
            "is_notified",
            "notification_sent_at",
            "telegram_id",
        ]
        read_only_fields = ("created_at", "is_notified", "notification_sent_at")

    def validate(self, attrs):
        """Проверяет наличие привязки к пользователю при создании задачи."""
        if self.instance:
            return attrs
        if attrs.get("user") is None and not attrs.get("telegram_id"):
            raise serializers.ValidationError(
                "Either `user` or `telegram_id` must be provided."
            )
        return attrs

    def create(self, validated_data):
        """Создает задачу и при необходимости связывает ее с Telegram-пользователем."""
        telegram_id = validated_data.pop("telegram_id", None)
        if validated_data.get("user") is None and telegram_id:
            validated_data["user"] = get_or_create_user_by_telegram_id(telegram_id)
        return super().create(validated_data)
