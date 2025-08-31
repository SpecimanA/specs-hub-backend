# projects/urls.py
from django.urls import path
from . import api

urlpatterns = [
    path('api/projects/create/', api.create_project_api, name='projects_create_project_api'),
]
