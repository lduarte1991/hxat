
import json

from django.core.management.base import BaseCommand

from hx_lti_initializer.models import LTICourse
from utils.utilities import courses_with_annotations


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--input-json",
            dest="input_json",
            required=True,
            help="json file with (context-id,collection-id) tuples from annotation db",
        )

    def handle(self, *args, **options):
        input_json = options.get("input_json")
        with open(input_json, "r") as fd:
            content = fd.read()
        data = json.loads(content)

        result = courses_with_annotations(data)
        print(json.dumps(result, indent=4))


