import csv
import sys

from django.db import transaction, connection
from django.core.management.base import BaseCommand, CommandError

from ozark.models import Blacklist, BlacklistPerson, BlacklistNaturalPersonDetails


class Command(BaseCommand):
    help = "Comando para cargar un csv con la lista negra de personas"

    def add_arguments(self, parser):
        parser.add_argument("blacklist_id", type=int)
        parser.add_argument("user_id", type=int)

    def handle(self, *args, **options):
        blacklist = Blacklist.objects.get(id=options["blacklist_id"])
        lines = sys.stdin.readlines()
        reader = csv.reader(lines)
        header = next(reader)

        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("select set_current_user_id(%s)", [options["user_id"], ])

            for row in reader:
                consecutivo, nombre, rfc, curp, nacionalidad, actividad, fecha, estatus, tipo, acciones = row

                curp = curp.strip() or None
                rfc = rfc.strip() or None

                if rfc and (len(rfc) > 13 or len(rfc) < 9):
                    print(f"RFC {rfc} is too long or short, skipping")
                    rfc = None

                person = BlacklistPerson.objects.create(
                    blacklist=blacklist,
                    type='natural',
                    attributes={},
                    #official_registration_number=''
                )
                BlacklistNaturalPersonDetails.objects.create(
                    blacklist_person=person,
                    rfc=rfc,
                    curp=curp,
                    full_name=nombre,
                )
