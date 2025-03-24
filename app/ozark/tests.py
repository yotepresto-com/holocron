import datetime

from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from django.db import connection, transaction
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import Group as AuthGroup

from ozark.models import Person, NaturalPersonDetails, JuridicalPersonDetails


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
