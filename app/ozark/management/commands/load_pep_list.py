import csv
import datetime
import sys

from django.db import transaction, connection
from django.core.management.base import BaseCommand, CommandError

from ozark.models import PepList, PepPerson


class Command(BaseCommand):
    help = "Comando para cargar un csv con la lista de PEPs"

    def add_arguments(self, parser):
        parser.add_argument("--user_id", type=int)
        parser.add_argument("--separator", type=str, default="|")
        parser.add_argument("--pep_list_id", type=int)

    def handle(self, *args, **options):
        lines = sys.stdin.readlines()
        reader = csv.reader(lines, delimiter=options['separator'])
        header = next(reader)

        pep_list = PepList.objects.get(id=options['pep_list_id'])

        for i, row in enumerate(reader):
            if i % 100 == 0:
                print(f'Processing {i} row')

            ID, relative_id, Record_Type, title, gender, first_name, last_name, full_name, other_names, Alternative_Script, function, specificfunction, category, ExPEPs, date_not_in_charge_since, DOB, POB, country, additional_information, Country_Of_Origin, Country_Of_Activity = row

            first_name = first_name.strip() or None
            last_name = last_name.strip() or None
            full_name = full_name.strip() or None

            if last_name and not first_name and len(last_name) < 10:
                print(f'Skipping {ID}: {last_name}')
                continue

            ex_pep = ExPEPs == 'Ex PEPs'

            attributes = {'ID': ID}
            if relative_id:
                attributes['relative_id'] = relative_id

            if ex_pep:
                attributes['ex_pep'] = ex_pep
            if gender:
                attributes['gender'] = gender
            if function:
                attributes['function'] = function
            if specificfunction:
                attributes['specificfunction'] = specificfunction

            date_of_birth = None
            if DOB:
                format = '%d.%m.%Y'
                if len(DOB) == 4:
                    format = '%Y'
                elif len(DOB) == 7:
                    format = '%m.%Y'
                if len(DOB) in (4, 7, 10) and ';' not in DOB:
                    date_of_birth = datetime.datetime.strptime(DOB, format)

            if date_not_in_charge_since:
                format = '%d.%m.%Y'
                if len(date_not_in_charge_since) == 4:
                    format = '%Y'
                elif len(date_not_in_charge_since) == 7:
                    format = '%m.%Y'
                date_not_in_charge_since = datetime.datetime.strptime(date_not_in_charge_since, format)
            else:
                date_not_in_charge_since = None

            if POB:
                attributes['POB'] = POB

            if additional_information:
                attributes['additional_information'] = additional_information

            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute("select set_current_user_id(%s)", [options["user_id"], ])

                person = PepPerson.objects.create(
                    pep_list=pep_list,
                    name=first_name,
                    first_last_name=last_name,
                    full_name=full_name,
                    date_of_birth=date_of_birth,
                    category=category,
                    date_not_in_charge_since=date_not_in_charge_since,
                    country=country,
                    attributes=attributes,
                )
