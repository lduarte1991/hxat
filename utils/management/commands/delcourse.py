import json

from django.core.management.base import BaseCommand

from hx_lti_initializer.models import LTICourse
from utils.utilities import delete_course, report_relationships_for_course


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--course-id", dest="cid",
        )
    def add_arguments(self, parser):
        parser.add_argument(
            "--input-json",
            dest="input_json",
            help="json file with list of course-ids to be deleted",
        )

    def handle(self, *args, **options):
        cid = options.get("cid", None)
        json_file = options.get("input_json", None)
        result = {"msg": "ok", "deleted": [], "failed": []}
        if cid:
            data = [cid]
        elif json_file:
            with open(json_file, "r") as fd:
                content = fd.read()
            data = json.loads(content)
        else:
            result["msg"] = "ERROR: missing input"
            print(json.dumps(result, indent=4))
            exit(1)

        for cid in data:
            _, msg = delete_course(cid)
            try:
                course = LTICourse.objects.get(course_id=cid)
            except LTICourse.DoesNotExist:
                result["deleted"].append([cid, msg])
            else:
                result["failed"].append([cid, msg])

        print(json.dumps(result, indent=4))
