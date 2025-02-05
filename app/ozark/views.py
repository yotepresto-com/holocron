from django.db import connection, transaction
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.authentication import TokenAuthentication


from .models import Config, User, Product, Person, Profile, ProfileAttribute, BlacklistPerson
from .serializers import ConfigSerializer, ProductSerializer, PersonSerializer, BlacklistPersonSerializer, \
    ProfileSerializer, ProfileAttributeSerializer


class DbAuthenticatedViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication, ]
    permission_classes = [IsAuthenticated]

    def authenticate(self, request):
        # TODO: use the django user model
        user = User.objects.get(username=request.user.username)
        with connection.cursor() as cursor:
            cursor.execute("select set_current_user_id(%s)", [user.id, ])


class ConfigViewSet(DbAuthenticatedViewSet):
    queryset = Config.objects.all()
    serializer_class = ConfigSerializer

    def retrieve(self, request, name=None):
        queryset = Config.objects.all()
        config = get_object_or_404(queryset, name=name)
        serializer = ConfigSerializer(config)
        return Response(serializer.data)

    def create(self, request):
        with transaction.atomic():
            self.authenticate(request)
            serializer = ConfigSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

    def update(self, request, name=None):
        with transaction.atomic():
            self.authenticate(request)
            config = get_object_or_404(Config, name=name)
            serializer = ConfigSerializer(config, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)


<<<<<<< Updated upstream
class ProductViewSet(DbAuthenticatedViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def update(self, request, pk=None):
        with transaction.atomic():
            self.authenticate(request)
            product = get_object_or_404(Product, pk=pk)
            serializer = ProductSerializer(product, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

    def delete(self, request, pk=None):
        with transaction.atomic():
            self.authenticate(request)
            product = get_object_or_404(Product, pk=pk)
            product.delete()
            return Response(status=200)


class PersonViewSet(DbAuthenticatedViewSet):
    queryset = Person.objects.all()
    serializer_class = PersonSerializer

    def delete(self, request, pk=None):
        with transaction.atomic():
            self.authenticate(request)
            person = get_object_or_404(Person, pk=pk)
            person.delete()
            return Response(status=200)


class BlacklistPersonViewSet(DbAuthenticatedViewSet):
    queryset = BlacklistPerson.objects.all()
    serializer_class = BlacklistPersonSerializer

    def create(self, request):
        with transaction.atomic():
            self.authenticate(request)
            serializer = BlacklistPersonSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

    def delete(self, request, pk=None):
        with transaction.atomic():
            self.authenticate(request)
            person = get_object_or_404(BlacklistPerson, pk=pk)
            person.delete()
            return Response(status=200)


class ProfileViewSet(DbAuthenticatedViewSet):
    """
    ViewSet to handle all Profile CRUD operations plus nested attribute endpoints.

    Endpoints:
      - POST   /profiles                  -> create()
      - GET    /profiles                  -> list()
      - GET    /profiles/{id}            -> retrieve()
      - PATCH  /profiles/{id}            -> partial_update()
      - DELETE /profiles/{id}            -> destroy()
      - POST   /profiles/{id}/attribute  -> create_attribute()
      - DELETE /profiles/{id}/attribute/{attribute_id} -> delete_attribute()
    """
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer

    @action(detail=True, methods=['post'], url_path='attribute')
    def create_attribute(self, request, pk=None):
        """Adds a new attribute definition to an existing profile."""
        profile = self.get_object()
        serializer = ProfileAttributeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(profile=profile)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'], url_path=r'attribute/(?P<attribute_id>[^/.]+)')
    def delete_attribute(self, request, pk=None, attribute_id=None):
        """Permanently removes a specific attribute from a profile."""
        profile = self.get_object()
        try:
            attribute = profile.attributes.get(id=attribute_id)
        except ProfileAttribute.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        attribute.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
