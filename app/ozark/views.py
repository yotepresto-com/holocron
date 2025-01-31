from django.db import connection, transaction
from rest_framework import viewsets
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.authentication import TokenAuthentication


from .models import Config, User, Product, Person, NaturalPersonDetails
from .serializers import ConfigSerializer, ProductSerializer, PersonSerializer, NaturalPersonDetailsSerializer


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
