import csv
import sys

from django.db import transaction, connection
from django.core.management.base import BaseCommand, CommandError

from ozark.models import Blacklist, BlacklistPerson, BlacklistNaturalPersonDetails, BlacklistJuridicalPersonDetails


class Command(BaseCommand):
    help = "Comando para cargar un csv con la lista negra de personas"

    def add_arguments(self, parser):
        parser.add_argument("--blacklist_id", type=int)
        parser.add_argument("--user_id", type=int)
        parser.add_argument("--separator", type=str, default=",")
        parser.add_argument("--format", type=str, default="1")

    def load_blacklist_person(self, user_id, blacklist, person_type, attributes, rfc, curp, nombre):
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("select set_current_user_id(%s)", [user_id, ])

            person = BlacklistPerson.objects.create(
                blacklist=blacklist,
                type=person_type,
                attributes=attributes,
                # official_registration_number=''
            )

            if person_type == 'natural':
                BlacklistNaturalPersonDetails.objects.create(
                    blacklist_person=person,
                    rfc=rfc,
                    curp=curp,
                    full_name=nombre,
                )
            else:
                BlacklistJuridicalPersonDetails.objects.create(
                    blacklist_person=person,
                    rfc=rfc,
                    legal_name=nombre,
                )

    def load_blacklist_format_1(self, reader, blacklist, options):
        for i, row in enumerate(reader):
            nombre, rfc, curp, nacionalidad, actividad, fecha, estatus, tipo, acciones = row

            curp = curp.strip() or None
            rfc = rfc.strip() or None
            rfcs = [None]
            person_type = 'natural'

            attributes = {
                'nacionalidad': nacionalidad,
                'actividad': actividad,
                'fecha': fecha,
                'estatus': estatus,
            }

            if acciones:
                attributes['acciones'] = acciones


            if rfc:
                if ' o ' not in rfc and (len(rfc) > 13 or len(rfc) < 9):
                    print(f"RFC {rfc} is too long or short, skipping")
                    rfcs = [None]
                elif rfc and ' o ' in rfc:
                   rfcs = rfc.split(' o ')
                else:
                    rfcs = [rfc]

            n = nombre.upper().strip().replace('.', '')
            if n.endswith(' SA DE CV') or n.endswith(' SR DE RL') or n.endswith(' RL DE CV') or n.endswith(' INC') or n.endswith(' CO.'):
                person_type = 'juridical'

            for j, rfc in enumerate(rfcs):
                if rfc and len(rfc) == 12:
                    person_type = 'juridical'

                if j > 0:
                    if not rfc:
                        print(f"RFC {rfc} is empty, skipping row")
                        continue
                    if len(rfc) > 13 or len(rfc) < 9:
                        print(f"RFC {rfc} is too long or short, skipping row")
                        continue

                self.load_blacklist_person(options["user_id"], blacklist, person_type, attributes, rfc, curp, nombre)

                print(f'Done {i}-{j}: {nombre} - {person_type}: {rfc}')

    def load_blacklist_format_2(self, reader, blacklist, options):
        for i, row in enumerate(reader):
            ID, Relative_ID, Tite, First_Name, Last_Name, full_name, other_names, Alternative_Script, Case, entity_type, date_of_publication, no_longer_on_list, DOB, POB, additional_information, country, Category, Address, Address_Country, Passport_Nr, name_of_the_list, date_of_information, Authority = row

            if i % 100 == 0:
                print(f'Processing {i} row')

            if name_of_the_list not in ('Condemnatory enforceable sentence by the commission of a tax offence (Article 69 of the Tax Code of the Federation)', 'List of taxpayers (Article 69-B of the Tax Code of the Federation)'):
                continue

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

            #print(f'Done {i}: {full_name}')

            if other_names:
                pass
                # TODO: agregar otro registro con el otro nombre

    def load_blacklist_format_3(self, reader, blacklist, options):
        # TODO: implementar
        return None

        for i, row in enumerate(reader):
            ID, Relative_ID, Record_Type, title, gender, first_name, last_name, full_name, other_names, Alternative_Script, function, specificfunction, category, ExPEPs, Date_Not_In_Charge_Since, DOB, POB, Country, Additional_Information, Country_Of_Origin, Country_Of_Activity = row

            attributes = {}
            attributes['gender'] = gender

            if Date_Not_In_Charge_Since:
                print(Date_Not_In_Charge_Since)

    def load_blacklist_format_4(self, reader, blacklist, options):
        for i, row in enumerate(reader):
            if i % 100 == 0:
                print(f'Processing {i} row')

            ID, title, first_name, last_name, full_name, other_names, alternative_script, DOB, POB, additional_information, type_SDN_or_entity, Address, passsport_nr, Name_of_the_List, type_of_list, date_of_publication_of_the_list, authority, whitelist = row

            if type_of_list not in ('Mexico List', 'OFAC List', 'OFAC SDN Lis', 'UN List', 'European Union Lists', 'FinCEN List'):
                continue

            if type_SDN_or_entity in ('P', 'Individual', 'I', 'INDIVIDUAL'):
                person_type = 'natural'
            else:
                person_type = 'juridical'

            first_name = first_name.strip() or None
            last_name = last_name.strip() or None
            full_name = full_name.strip() or None

            if person_type == 'natural' and full_name:
                first_name = None
                last_name = None

            if person_type == 'natural' and first_name and not last_name:
                # no tiene apellido
                full_name = first_name
                first_name = None

            # TODO: use other_names and alternative_script

            if person_type == 'juridical' and not full_name:
                # pueden poner el nombre de la empresa como apellido o primer nombre
                full_name = first_name or last_name

            attributes = {'ID': ID, 'type_of_list': type_of_list}
            if DOB:
                attributes['DOB'] = DOB
            if POB:
                attributes['POB'] = POB
            if additional_information:
                attributes['additional_information'] = additional_information
            if passsport_nr:
                attributes['passsport_nr'] = passsport_nr
            if date_of_publication_of_the_list:
                attributes['date_of_publication_of_the_list'] = date_of_publication_of_the_list
            if authority:
                attributes['authority'] = authority
            if whitelist:
                attributes['whitelist'] = whitelist

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
                        rfc=None,
                        curp=None,
                        full_name=full_name,
                        name=first_name,
                        first_last_name=last_name,
                    )
                else:
                    BlacklistJuridicalPersonDetails.objects.create(
                        blacklist_person=person,
                        rfc=None,
                        legal_name=full_name,
                        #incorporation_date=
                    )


    def handle(self, *args, **options):
        blacklist = Blacklist.objects.get(id=options["blacklist_id"])
        lines = sys.stdin.readlines()
        reader = csv.reader(lines, delimiter=options['separator'])
        header = next(reader)

        method = self.load_blacklist_format_1

        if options['format'] == '2':
            method = self.load_blacklist_format_2
        elif options['format'] == '3':
            method = self.load_blacklist_format_3
        elif options['format'] == '4':
            method = self.load_blacklist_format_4

        # with transaction.atomic():
        #     with connection.cursor() as cursor:
        #         cursor.execute("select set_current_user_id(%s)", [options["user_id"], ])

        method(reader, blacklist, options)
