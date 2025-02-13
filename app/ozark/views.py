from django.db.models import Q
from django.contrib.auth.models import User as AuthUser
from django.db import connection, transaction
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.authentication import TokenAuthentication


from .models import Config, User, Product, Person, Profile, ProfileAttribute, BlacklistPerson, Blacklist
from .serializers import ConfigSerializer, ProductSerializer, PersonSerializer, BlacklistPersonSerializer, \
    ProfileSerializer, ProfileAttributeSerializer, BlacklistSerializer, UserSerializer


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


class BlacklistViewSet(DbAuthenticatedViewSet):
    queryset = Blacklist.objects.all().order_by('id')
    serializer_class = BlacklistSerializer

    def create(self, request):
        with transaction.atomic():
            self.authenticate(request)
            serializer = BlacklistSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)


class BlacklistPersonViewSet(DbAuthenticatedViewSet):
    queryset = BlacklistPerson.objects.all()
    serializer_class = BlacklistPersonSerializer

    def get_queryset(self):
        # TODO: fix the N+1 query issue
        _type = self.request.query_params.get('type')
        if _type:
            self.queryset = self.queryset.filter(type=_type)

        curp = self.request.query_params.get('curp')
        if curp:
            self.queryset = self.queryset.filter(natural_person_details__curp=curp)

        rfc = self.request.query_params.get('rfc')
        if rfc:
            self.queryset = self.queryset.filter(Q(juridical_person_details__rfc=rfc) | Q(natural_person_details__rfc=rfc))

        name = self.request.query_params.get('name')
        if name:
            self.queryset = self.queryset.filter(natural_person_details__name=name)

        # TODO: use second last name too
        last_name = self.request.query_params.get('last_name')
        if last_name:
            self.queryset = self.queryset.filter(natural_person_details__first_last_name=last_name)

        full_name = self.request.query_params.get('full_name')
        if full_name:
            self.queryset = self.queryset.filter(natural_person_details__calculated_full_name__icontains=full_name)

        date_of_birth = self.request.query_params.get('date_of_birth')
        if date_of_birth:
            self.queryset = self.queryset.filter(natural_person_details__date_of_birth=date_of_birth)

        legal_name = self.request.query_params.get('legal_name')
        if legal_name:
            self.queryset = self.queryset.filter(juridical_person_details__legal_name=legal_name)

        incorporation_date = self.request.query_params.get('incorporation_date')
        if incorporation_date:
            self.queryset = self.queryset.filter(juridical_person_details__incorporation_date=incorporation_date)

        return self.queryset

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


class UsersViewSet(DbAuthenticatedViewSet):
    queryset = AuthUser.objects.all()
    serializer_class = UserSerializer

    def create(self, request):
        with transaction.atomic():
            self.authenticate(request)
            serializer = UserSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

    def destroy(self, request, pk=None):
        with transaction.atomic():
            self.authenticate(request)
            user = get_object_or_404(AuthUser, pk=pk, is_active=True)
            user.is_active = False
            user.save()
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
