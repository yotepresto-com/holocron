from django.urls import path

from .views import ConfigViewSet, ProfileViewSet, ProductViewSet, PersonViewSet, BlacklistPersonViewSet

urlpatterns = [
    path('config/', ConfigViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('config/<str:name>/', ConfigViewSet.as_view({'get': 'retrieve', 'put': 'update'})),

    # Products
    path('products/', ProductViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('products/<int:pk>/', ProductViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),

    # Persons
    path('persons/', PersonViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('persons/<int:pk>/', PersonViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'})),

    # Blacklisted Persons
    path('blacklisted_persons/', BlacklistPersonViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('blacklisted_persons/<int:pk>/', BlacklistPersonViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'})),

    # Profile Management
    #path('profiles/', ProfileViewSet.create_profile, name='create_profile'),
    #path('profiles/<int:id>/', ProfileViewSet.get_profile_by_id, name='get_profile_by_id'),
    #path('profiles/<int:id>/', ProfileViewSet.update_profile_base_info, name='update_profile_base_info'),
    #path('profiles/<int:id>/attribute', ProfileViewSet.create_attribute_in_profile, name='create_attribute_in_profile'),
    #path('profiles/<int:id>/attribute/<int:attribute_id>/', ProfileViewSet.delete_attribute_from_profile, name='delete_attribute_from_profile'),
    #path('profiles/<int:id>/', ProfileViewSet.delete_profile, name='delete_profile'),
]
