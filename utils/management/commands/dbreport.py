
import json

from django.core.management.base import BaseCommand

from hx_lti_initializer.models import LTICourse
from utils.utilities import report_relationships_for_course


class Command(BaseCommand):
    help = "My shiny new management command."

    def add_arguments(self, parser):
        parser.add_argument(
            "--course-id", dest="cid", required=True,
        )

    def handle(self, *args, **options):
        cid = options["cid"]

        if cid == "all":
            result = {}
            all_courses = LTICourse.objects.all()
            for c in all_courses:
                c_result, msg = report_relationships_for_course(c.course_id)
                result[c.course_id] = c_result
        else:
            # print all relationships for course
            result, msg = report_relationships_for_course(cid)
            if msg != "ok":
                print(msg)
                return

        print(json.dumps(result, indent=4, sort_keys=True))


