import json

from django.core.management.base import BaseCommand

from hx_lti_initializer.models import LTICourse
from utils.utilities import delete_course, report_relationships_for_course


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--course-id", dest="cid", required=True,
        )

    def handle(self, *args, **options):
        cid = options["cid"]

        # print all relationships for course
        delete_course(cid)
        try:
            course = LTICourse.objects.get(course_id=cid)
        except LTICourse.DoesNotExist:
            print("course({}) is DELETED".format(cid))
        else:
            result = report_relationships_for_course(cid)
            print(json.dumps(result, indent=4, sort_keys=True))

