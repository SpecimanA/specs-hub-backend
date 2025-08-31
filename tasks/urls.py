# tasks/urls.py
from django.urls import path
from . import api

urlpatterns = [
    path('api/tasks/create/', api.create_task_api, name='tasks_create_task_api'),
]
