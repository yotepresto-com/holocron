from django.contrib import admin
from django.urls import path, include

from .views import ConfigViewSet, ProductViewSet, PersonViewSet, BlacklistPersonViewSet


urlpatterns = [
    path('config/', ConfigViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('config/<str:name>/', ConfigViewSet.as_view({'get': 'retrieve', 'put': 'update'})),
    path('products/', ProductViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('products/<int:pk>/', ProductViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),
    path('persons/', PersonViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('persons/<int:pk>/', PersonViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'})),
    path('blacklisted_persons/', BlacklistPersonViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('blacklisted_persons/<int:pk>/', BlacklistPersonViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'})),
]
