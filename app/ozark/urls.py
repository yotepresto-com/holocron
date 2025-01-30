from django.contrib import admin
from django.urls import path, include

from .views import ConfigViewSet, ProductViewSet


urlpatterns = [
    path('config/', ConfigViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('config/<str:name>/', ConfigViewSet.as_view({'get': 'retrieve', 'put': 'update'})),
    path('products/', ProductViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('products/<int:pk>/', ProductViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),
]