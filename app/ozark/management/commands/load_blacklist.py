import csv
import sys

from django.db import transaction, connection
from django.core.management.base import BaseCommand, CommandError

from ozark.models import Blacklist, BlacklistPerson, BlacklistNaturalPersonDetails, BlacklistJuridicalPersonDetails


class Command(BaseCommand):
    help = "Comando para cargar un csv con la lista negra de personas"

    def add_arguments(self, parser):
        parser.add_argument("blacklist_id", type=int)
        parser.add_argument("user_id", type=int)

    def load_blacklist_format_1(self, reader, blacklist, options):
        for i, row in enumerate(reader):
            consecutivo, nombre, rfc, curp, nacionalidad, actividad, fecha, estatus, tipo, acciones = row

            curp = curp.strip() or None
            rfc = rfc.strip() or None


            if rfc and (len(rfc) > 13 or len(rfc) < 9):
                print(f"RFC {rfc} is too long or short, skipping")
                rfc = None

            if rfc and len(rfc) == 12:
                # TODO: insert persona moral
                print(f"RFC ({nombre}): {rfc}  is a moral person, skipping")
                continue

            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute("select set_current_user_id(%s)", [options["user_id"], ])

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

            print(f'Done {i}: {nombre}')

    def load_blacklist_format_2(self, reader, blacklist, options):
        for i, row in enumerate(reader):
            ID, Relative_ID, Title, First_Name, Last_Name, full_name, other_names, Alternative_Script, Case, entity_type, date_of_publication, no_longer_on_list, DOB, POB, additional_information, country, Category, Address, Address_Country, Passport_Nr, name_of_the_list, date_of_information, Authority = row

            rfc = None
            if additional_information and additional_information.startswith("RFC: "):
                rfc = additional_information[5:].strip()
                if ';' in rfc:
                    rfc = rfc.split(';')[0]

                if rfc and len(rfc) < 10:
                    rfc = None

            person_type = 'natural' if entity_type == 'I' else 'juridical'

            attributes = {}
            if date_of_publication:
                # TODO: convertir a fecha
                attributes['date_of_publication'] = date_of_publication

            if no_longer_on_list:
                attributes['no_longer_on_list'] = no_longer_on_list

            if name_of_the_list:
                attributes['name_of_the_list'] = name_of_the_list

            if date_of_information:
                attributes['date_of_information'] = date_of_information

            # if not rfc or len(rfc) not in (10, 12, 13):
            #     print(f'{i}, RFC no válido: {rfc}')
            #     rfc = None

            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute("select set_current_user_id(%s)", [options["user_id"], ])


                person = BlacklistPerson.objects.create(
                    blacklist=blacklist,
                    type=person_type,
                    attributes=attributes,
                    official_registration_number=ID
                )

                if person_type == 'natural':
                    BlacklistNaturalPersonDetails.objects.create(
                        blacklist_person=person,
                        rfc=rfc,
                        curp=None,
                        full_name=full_name,
                    )
                else:
                    BlacklistJuridicalPersonDetails.objects.create(
                        blacklist_person=person,
                        rfc=None,
                        legal_name=full_name,
                        #incorporation_date=
                    )

            print(f'Done {i}: {full_name}')

            if other_names:
                pass
                # TODO: agregar otro registro con el otro nombre



    def handle(self, *args, **options):
        blacklist = Blacklist.objects.get(id=options["blacklist_id"])
        lines = sys.stdin.readlines()
        reader = csv.reader(lines)
        header = next(reader)

        # with transaction.atomic():
        #     with connection.cursor() as cursor:
        #         cursor.execute("select set_current_user_id(%s)", [options["user_id"], ])

        if len(header) == 10:
            self.load_blacklist_format_1(reader, blacklist, options)
        else:
            self.load_blacklist_format_2(reader, blacklist, options)
