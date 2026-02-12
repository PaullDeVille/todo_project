from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from todo.views import TaskViewSet, CategoryViewSet

router = DefaultRouter()
router.register("tasks", TaskViewSet)
router.register("categories", CategoryViewSet)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
]
