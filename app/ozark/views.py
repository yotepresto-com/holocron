from django.db.models import Q
from django.db import connection, transaction
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.authentication import TokenAuthentication
from django.contrib.auth.models import User as AuthUser, Group as AuthGroup


from .models import Config, Product, Person, Profile, ProfileAttribute, BlacklistPerson, Blacklist, \
    RolePermission
from .serializers import ConfigSerializer, ProductSerializer, PersonSerializer, BlacklistPersonSerializer, \
    ProfileSerializer, ProfileAttributeSerializer, BlacklistSerializer, UserSerializer, GroupSerializer, \
    RolePermissionSerializer, MultipleRolePermissionsSerializer, UserRoleSerializer



class DbAuthenticatedViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication, ]
    permission_classes = [IsAuthenticated]

    def has_permission(self, user, permission_type: str):
        with connection.cursor() as cursor:
            cursor.execute("select has_permission(%s, %s)", [user.id, permission_type, ])
            res = cursor.fetchone()
            return res[0]

    def authenticate(self, request):
        with connection.cursor() as cursor:
            cursor.execute("select set_current_user_id(%s)", [request.user.id, ])

    def update(self, request, pk=None):
        with transaction.atomic():
            self.authenticate(request)
            return super().update(request, pk)

    def create(self, request):
        with transaction.atomic():
            self.authenticate(request)
            return super().create(request)


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
            return Response(serializer.data, 201)

    def update(self, request, name=None):
        with transaction.atomic():
            self.authenticate(request)
            config = get_object_or_404(Config, name=name)
            serializer = ConfigSerializer(config, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

    def list_permissions(self, request):
        sql = "SELECT unnest(enum_range(NULL::permission_type))::text as name order by 1;"
        res = []
        with connection.cursor() as cursor:
            cursor.execute(sql, [])
            permissions = cursor.fetchall()
        for permission in permissions:
            res.append({'permission': permission[0]})
        return Response(res)


class ProductViewSet(DbAuthenticatedViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def list(self, request):
        permission = 'read_product'
        if not self.has_permission(self.request.user, permission):
            return Response({'permission': permission}, status=403)

        return super().list(request)

    def update(self, request, pk=None):
        with transaction.atomic():
            self.authenticate(request)
            product = get_object_or_404(Product, pk=pk)
            serializer = ProductSerializer(product, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, 201)

    def destroy(self, request, pk=None):
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
            return Response(status=204)


class BlacklistViewSet(DbAuthenticatedViewSet):
    queryset = Blacklist.objects.all().order_by('id')
    serializer_class = BlacklistSerializer

    def create(self, request):
        with transaction.atomic():
            self.authenticate(request)
            serializer = BlacklistSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, 201)


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
            return Response(serializer.data, 201)

    def delete(self, request, pk=None):
        with transaction.atomic():
            self.authenticate(request)
            person = get_object_or_404(BlacklistPerson, pk=pk)
            person.delete()
            return Response(status=204)


class UserViewSet(DbAuthenticatedViewSet):
    queryset = AuthUser.objects.all()
    serializer_class = UserSerializer

    def list(self, request):
        permission = 'read_user'
        if not self.has_permission(self.request.user, permission):
            return Response({'permission': permission}, status=403)

        return super().list(request)

    def create(self, request):
        with transaction.atomic():
            self.authenticate(request)
            serializer = UserSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, 201)

    def destroy(self, request, pk=None):
        with transaction.atomic():
            self.authenticate(request)
            user = get_object_or_404(AuthUser, pk=pk, is_active=True)
            user.is_active = False
            user.save()
            return Response(status=204)


class GroupViewSet(DbAuthenticatedViewSet):
    queryset = AuthGroup.objects.all()
    serializer_class = GroupSerializer

    def list(self, request):
        permission = 'read_role'
        if not self.has_permission(self.request.user, permission):
            return Response({'permission': permission}, status=403)

        return super().list(request)

    def create(self, request):
        with transaction.atomic():
            self.authenticate(request)
            serializer = GroupSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, 201)

    def destroy(self, request, pk=None):
       with transaction.atomic():
           self.authenticate(request)
           group = get_object_or_404(AuthGroup, pk=pk)
           group.delete()
           return Response(status=204)


class RolePermissionViewSet(DbAuthenticatedViewSet):
    queryset = RolePermission.objects.all()
    serializer_class = RolePermissionSerializer

    def get_role_permissions(self, request, pk):
        permission = 'read_permission'
        if not self.has_permission(self.request.user, permission):
            return Response({'permission': permission}, status=403)

        role = get_object_or_404(AuthGroup, pk=pk)
        permissions = role.role_permissions.all()
        serializer = RolePermissionSerializer(permissions, many=True)
        return Response(serializer.data)

    def create_role_permissions(self, request, pk):
        role = get_object_or_404(AuthGroup, pk=pk)
        serializer = MultipleRolePermissionsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            self.authenticate(request)
            for permission in serializer.validated_data['permissions']:
                role.role_permissions.create(role=role, permission=permission)

        return Response(serializer.data, 201)


    def delete_role_permissions(self, request, pk):
        role = get_object_or_404(AuthGroup, pk=pk)
        serializer = MultipleRolePermissionsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            self.authenticate(request)
            for permission in serializer.validated_data['permissions']:
                role.role_permissions.get(role=role, permission=permission).delete()

        return Response(serializer.data, 204)


class UserRoleViewSet(DbAuthenticatedViewSet):
    queryset = AuthUser.objects.all()
    serializer_class = UserRoleSerializer

    def create(self, request, pk):
        user = get_object_or_404(AuthUser, pk=pk)
        serializer = UserRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            self.authenticate(request)
            user.groups.add(serializer.validated_data['role_id'])

        return Response(serializer.data, 201)

    def delete(self, request, user_id, role_id):
        user = get_object_or_404(AuthUser, pk=user_id)
        role = get_object_or_404(AuthGroup, pk=role_id)
        with transaction.atomic():
            self.authenticate(request)
            user.groups.remove(role)

        return Response(status=204)


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
