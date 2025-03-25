import datetime

from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from django.db import connection, transaction
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import Group as AuthGroup

from ozark.models import Person, NaturalPersonDetails, JuridicalPersonDetails, Blacklist, RolePermission


class AuthenticatedTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("user", "user@yotepresto.com", is_superuser=True)
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("select set_current_user_id(%s)", [self.user.id, ])
            self.group = AuthGroup.objects.create(name='group1')
            self.user.groups.add(self.group.id)
            self.group.role_permissions.create(role=self.group, permission='assign_permission')

            self.user.is_superuser = False
            self.user.save()


class UserTestCase(AuthenticatedTestCase):
    def setUp(self):
        super().setUp()

        self.url = reverse('users')
        self.user_data = {
            "username": "test",
            "email": "test4@ytp.com",
            "first_name": "Juan",
            "last_name": "Perez"
        }

    def test_create_user_permission(self):
        response = self.client.post(self.url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_user(self):
        self.group.role_permissions.create(role=self.group, permission='create_user')
        response = self.client.post(self.url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class PersonTestCase(AuthenticatedTestCase):
    def setUp(self):
        super().setUp()

        self.url = reverse('persons')

        self.natural_person = Person.objects.create(
            type='natural',
            active=True,
        )
        NaturalPersonDetails.objects.create(
            person=self.natural_person,
            curp='VERF881120HJCA2822',
            rfc='VERF881120J47',
            name='Juan',
            first_last_name='Perez',
            second_last_name='García',
            date_of_birth=datetime.date(year=1988, month=11, day=20),
        )

        self.deleted_person = Person.objects.create(
            type='natural',
            active=False,
            deleted_at=datetime.datetime.utcnow()
        )
        NaturalPersonDetails.objects.create(
            person=self.deleted_person,
            curp='BERF881120HJCA2822',
            rfc='BERF881120J47',
            name='Juana',
            first_last_name='Perez',
            second_last_name='García',
            date_of_birth=datetime.date(year=1988, month=11, day=21),
        )

        self.juridical_person = Person.objects.create(
            type='juridical',
            active=True,
        )
        JuridicalPersonDetails.objects.create(
            person=self.juridical_person,
            rfc='AAAAAAAAAAA1',
            legal_name='Ferreteria la Chida SA de CV'
        )


    def test_list_persons(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['count'], 2)
        self.assertEqual(response.data['results'][0]['natural_person_details']['full_name'], 'JUAN PEREZ GARCÍA')
        self.assertEqual(response.data['results'][0]['type'], 'natural')
        self.assertEqual(response.data['results'][1]['juridical_person_details']['legal_name'], 'Ferreteria la Chida SA de CV')
        self.assertEqual(response.data['results'][1]['type'], 'juridical')

    def test_create_persons(self):
        data = {
          "type": "natural",
          "natural_person_details": {
            "name": "juanito",
            "first_last_name": "martinez"
          }
        }
        response = self.client.post(self.url, format='json', data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(NaturalPersonDetails.objects.filter(name='juanito', first_last_name='martinez'))

        data = {
            "type": "juridical",
            "juridical_person_details": {
                "rfc": 'AAAAAAAAAAA2',
                "legal_name": "Ferreteria la Chida SA de CV"
            }
        }
        response = self.client.post(self.url, format='json', data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(JuridicalPersonDetails.objects.filter(rfc='AAAAAAAAAAA2', legal_name="Ferreteria la Chida SA de CV"))


class BlacklistTestCase(AuthenticatedTestCase):
    def setUp(self):
        super().setUp()

        self.url = reverse('blacklists')

        self.blacklist = Blacklist.objects.create(
            name='blacklist1',
            description='blacklist1 desc',
            attributes_schema={},
            import_configuration={},
        )

    def test_list_blacklists(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], 'blacklist1')

    def test_create_blacklist(self):
        data = {
          "name": "test bl",
          "attributes_schema": {},
          "import_configuration": {}
        }
        response = self.client.post(self.url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(Blacklist.objects.filter(name="test bl").exists())

    def test_get_blacklist(self):
        url = reverse('blacklists', kwargs={'pk':self.blacklist.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.blacklist.name)

class GroupTestCase(AuthenticatedTestCase):
    def setUp(self):
        super().setUp()

        self.url = reverse('groups')

    def test_list_groups(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.group.role_permissions.create(role=self.group, permission='read_role')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], 'group1')

    def test_create_group(self):
        data = {"name": "test_group2",}
        response = self.client.post(self.url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.group.role_permissions.create(role=self.group, permission='create_role')
        response = self.client.post(self.url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(AuthGroup.objects.filter(name="test_group2").exists())

    def test_get_blacklist(self):
        self.group.role_permissions.create(role=self.group, permission='create_role')
        self.test_group = AuthGroup.objects.create(name='test_group1')

        url = reverse('groups', kwargs={'pk':self.test_group.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.group.role_permissions.create(role=self.group, permission='read_role')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.test_group.name)


class ConfigTestCase(AuthenticatedTestCase):
    def setUp(self):
        super().setUp()

    def test_list_permissions(self):
        url = reverse('permissions')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.group.role_permissions.create(role=self.group, permission='read_permission')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        for per in response.data:
            self.assertIsInstance(per, dict)
            self.assertIn('permission', per)


class RolePermissionTestCase(AuthenticatedTestCase):
    def setUp(self):
        super().setUp()

    def test_get_role_permissions(self):
        self.group.role_permissions.create(role=self.group, permission='create_role')

        url = reverse('role_permissions', kwargs={'pk': self.group.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.group.role_permissions.create(role=self.group, permission='read_permission')
        response = self.client.get(url)
        self.assertIsInstance(response.data, list)
        self.assertTrue(len(response.data) > 2) # assign_permission, create_role and read_permission

    def test_create_role_permissions(self):
        url = reverse('role_permissions', kwargs={'pk': self.group.id})
        data = {"permissions": ["delete_product", "create_product"]}
        response = self.client.post(url, format='json', data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(RolePermission.objects.filter(role=self.group, permission='delete_product').exists())
        self.assertTrue(RolePermission.objects.filter(role=self.group, permission='create_product').exists())

    def test_delete_role_permissions(self):
        url = reverse('role_permissions', kwargs={'pk': self.group.id})
        data = {"permissions": ["create_user", "create_role"]}
        self.group.role_permissions.create(role=self.group, permission='create_user')
        self.group.role_permissions.create(role=self.group, permission='create_role')
        response = self.client.delete(url, format='json', data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.group.role_permissions.create(role=self.group, permission='remove_permission')
        response = self.client.delete(url, format='json', data=data)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(RolePermission.objects.filter(role=self.group, permission='create_user').exists())
        self.assertFalse(RolePermission.objects.filter(role=self.group, permission='create_role').exists())
