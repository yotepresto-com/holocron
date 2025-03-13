import csv
import sys

from django.db import transaction, connection
from django.core.management.base import BaseCommand, CommandError

from ozark.models import NaturalPersonDetails, Person


class Command(BaseCommand):
    help = "Comando para cargar un csv con los usuarios de ytp"

    def add_arguments(self, parser):
        parser.add_argument("--user_id", type=int)

    def handle(self, *args, **options):
        lines = sys.stdin.readlines()
        reader = csv.reader(lines)
        header = next(reader)

        #with transaction.atomic():
        #with connection.cursor() as cursor:
        #    cursor.execute("select set_current_user_id(%s)", [options["user_id"], ])

        transaction.set_autocommit(False)

        for i, row in enumerate(reader):
            name,first_last_name,second_last_name,curp,rfc = row

            curp = curp.strip() or None
            rfc = rfc.strip() or None

            if rfc and (len(rfc) > 13 or len(rfc) < 10):
                print(f"RFC {rfc} is too long or short, skipping")
                rfc = None

            if len(curp) != 18:
                print(f"CURP {curp} is too long or short, skipping")
                continue


            person = Person.objects.create(
                type='natural',
                active=True
            )
            NaturalPersonDetails.objects.create(
                person=person,
                rfc=rfc,
                curp=curp,
                name=name,
                first_last_name=first_last_name,
                second_last_name=second_last_name,
                # date_of_birth=...
            )

            if i % 100 == 0:
                transaction.commit()
                print(f"Processing {i+1} row")

        transaction.commit()
