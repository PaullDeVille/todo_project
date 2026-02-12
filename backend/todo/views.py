from rest_framework.viewsets import ModelViewSet

from .models import Category, Task
from .serializers import CategorySerializer, TaskSerializer

class TaskViewSet(ModelViewSet):
    """Операции создания, чтения, обновления и удаления задач с фильтрацией по Telegram."""

    serializer_class = TaskSerializer
    queryset = Task.objects.select_related("category", "user").all()

    def get_queryset(self):
        """Фильтрует задачи по Telegram ID, если он передан в запросе."""
        queryset = super().get_queryset()
        telegram_id = self.request.query_params.get("telegram_id")
        if telegram_id:
            queryset = queryset.filter(user__username=f"tg_{telegram_id}")
        return queryset

class CategoryViewSet(ModelViewSet):
    """Эндпоинты создания, чтения, обновления и удаления категорий."""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
