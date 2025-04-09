import json

from django.db.models import Q
from django.db import connection, transaction
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.utils import ProgrammingError
from django.shortcuts import get_object_or_404
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.authentication import TokenAuthentication
from django.contrib.auth.models import User as AuthUser, Group as AuthGroup


from .models import Config, Product, Person, Profile, ProfileAttribute, BlacklistPerson, Blacklist, \
    RolePermission, NaturalPersonDetails
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
        permission = 'read_permission'
        if not self.has_permission(self.request.user, permission):
            return Response({'permission': permission}, status=403)

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
    queryset = Person.objects.filter(deleted_at__isnull=True).order_by('id')
    serializer_class = PersonSerializer

    # TODO: add permissions

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
        permission = 'create_user'
        with transaction.atomic():
            self.authenticate(request)
            serializer = UserSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            try:
                serializer.save()
                Token.objects.create(user=serializer.instance)
            except ProgrammingError as ex:
                if f'does not have permission {permission}' in str(ex):
                    return Response({'permission': permission}, status=403)
                else:
                    raise ex
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

    def retrieve(self, request, pk):
        permission = 'read_role'
        if not self.has_permission(self.request.user, permission):
            return Response({'permission': permission}, status=403)

        return super().retrieve(request, pk)

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
            permission = 'create_role'
            try:
                serializer.save()
            except ProgrammingError as ex:
                if f'does not have permission {permission}' in str(ex):
                    return Response({'permission': permission}, status=403)
                else:
                    raise ex
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
            try:
                for permission in serializer.validated_data['permissions']:
                    role.role_permissions.get(role=role, permission=permission).delete()
            except ProgrammingError as ex:
                if f'does not have permission remove_permission' in str(ex):
                    return Response({'permission': 'remove_permission'}, status=403)
                else:
                    raise ex

        return Response(serializer.data, 204)


class UserRoleViewSet(DbAuthenticatedViewSet):
    queryset = AuthUser.objects.all()
    serializer_class = UserRoleSerializer

    def create(self, request, pk):
        user = get_object_or_404(AuthUser, pk=pk)
        serializer = UserRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        permission = 'assign_role'
        with transaction.atomic():
            self.authenticate(request)
            try:
                user.groups.add(serializer.validated_data['role_id'])
            except ProgrammingError as ex:
                if f'does not have permission {permission}' in str(ex):
                    return Response({'permission': permission}, status=403)
                else:
                    raise ex

        return Response(serializer.data, 201)

    def delete(self, request, user_id, role_id):
        user = get_object_or_404(AuthUser, pk=user_id)
        role = get_object_or_404(AuthGroup, pk=role_id)
        permission = 'remove_role'
        with transaction.atomic():
            self.authenticate(request)
            try:
                user.groups.remove(role)
            except ProgrammingError as ex:
                if f'does not have permission {permission}' in str(ex):
                    return Response({'permission': permission}, status=403)
                else:
                    raise ex

        return Response(status=204)


class SearchViewSet(DbAuthenticatedViewSet):
    #serializer_class = UserRoleSerializer

    def list(self, request, *args, **kwargs):
        name = request.query_params.get('name') or None
        first_last_name = request.query_params.get('first_last_name') or None
        second_last_name = request.query_params.get('second_last_name') or None
        min_score = request.query_params.get('min_score') or 0.9

        sql = """
        select *,
            compute_match_score(%(name)s, %(first_last_name)s, %(second_last_name)s, npd.full_name) as score
        from natural_person_details npd
        where compute_match_score(%(name)s, %(first_last_name)s, %(second_last_name)s, npd.full_name) >= %(min_score)s
        """

        params = {
            'name': name,
            'first_last_name': first_last_name,
            'second_last_name': second_last_name,
            'min_score': min_score,
        }
        natural_persons = NaturalPersonDetails.objects.raw(sql, params)

        natural_persons_res = []
        for p in natural_persons:
            natural_persons_res.append({
                'name': p.name,
                'first_last_name': p.first_last_name,
                'second_last_name': p.second_last_name,
                'curp': p.curp,
                'rfc': p.rfc,
                'full_name': p.full_name,
                'score': p.score,
            })

        sql = """
        select bl_npd.name, bl_npd.first_last_name, bl_npd.second_last_name,
            bl_npd.calculated_full_name as full_name,
            bl_npd.rfc, bl_npd.curp, bl_npd.date_of_birth as birth_date,
            bl_p.created_at,
            bl.name as blacklist_name, bl_p.attributes,
            compute_match_score(%(name)s, %(first_last_name)s, %(second_last_name)s, bl_npd.calculated_full_name) as score
        from blacklist_natural_person_details bl_npd
            inner join blacklist_person bl_p on bl_p.id = bl_npd.blacklist_person_id
            inner join blacklist bl on bl.id = bl_p.blacklist_id
        where bl_p.deleted_at is null
            and compute_match_score(%(name)s, %(first_last_name)s, %(second_last_name)s, bl_npd.calculated_full_name) >= %(min_score)s
        ;
        """

        blacklist_res = []

        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            for row in cursor.fetchall():
                attributes = json.loads(row[9]) if row[9] else None
                blacklist_res.append({
                    'name': row[0],
                    'first_last_name': row[1],
                    'second_last_name': row[2],
                    'full_name': row[3],
                    'rfc': row[4],
                    'curp': row[5],
                    'birth_date': row[6],
                    'created_at': row[7],
                    'blacklist_name': row[8],
                    'attributes': attributes,
                    'score': row[10],
                })

        sql = """
        select pp.name, pp.first_last_name, pp.second_last_name, pp.calculated_full_name as full_name,
           pp.rfc, pp.curp, pp.date_of_birth as birth_date,
           pp.created_at,
           pp.date_not_in_charge_since,
           pp.category,
           pp.country,
           pl.name as list,
           pp.attributes,
           compute_match_score(%(name)s, %(first_last_name)s, %(second_last_name)s, pp.calculated_full_name) as score
        from pep_person pp
            inner join pep_list pl on pl.id = pp.pep_list_id
        where pp.deleted_at is null
            and compute_match_score(%(name)s, %(first_last_name)s, %(second_last_name)s, pp.calculated_full_name) >= %(min_score)s
        ;

        """
        pep_res = []
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            for row in cursor.fetchall():
                attributes = json.loads(row[12]) if row[12] else None
                pep_res.append({
                    'name': row[0],
                    'first_last_name': row[1],
                    'second_last_name': row[2],
                    'full_name': row[3],
                    'rfc': row[4],
                    'curp': row[5],
                    'birth_date': row[6],
                    'created_at': row[7],
                    'date_not_in_charge_since': row[8],
                    'category': row[9],
                    'country': row[10],
                    'list': row[11],
                    'attributes': attributes,
                    'score': row[13],
                })

        res = {
            'users': natural_persons_res,
            'blacklist_persons': blacklist_res,
            'pep_res': pep_res,
        }
        return Response(res, status=200)


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
