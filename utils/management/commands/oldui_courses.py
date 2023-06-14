
import json

from django.core.management.base import BaseCommand

from hx_lti_initializer.models import LTICourse
from utils.utilities import courses_with_oldui, assignments_being_accessed


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--summary-only",
            dest="summary_only",
            action="store_true",
            help="print only course_ids for each category",
        )

    def handle(self, *args, **options):
        summary_only = options.get("summary_only", False)
        result = courses_with_oldui()

        if summary_only:
            res = {}
            for k in result:
                res[k] = result[k]["summary"]
            result = res

        print(json.dumps(result, indent=4))




