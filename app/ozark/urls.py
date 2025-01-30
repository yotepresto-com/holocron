from django.contrib import admin
from django.urls import path, include

from .views import ConfigViewSet

urlpatterns = [
    path('config/', ConfigViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('config/<str:name>/', ConfigViewSet.as_view({'get': 'retrieve', 'put': 'update'})),
]