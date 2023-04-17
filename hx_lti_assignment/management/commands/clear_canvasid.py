import glob
import json
import os
import traceback

from django.core.management import BaseCommand
from hx_lti_assignment.models import AssignmentTargets


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        all_img_at = AssignmentTargets.objects.filter(target_object__target_type="ig")
        result = {}
        for at in all_img_at:
            course_id = at.assignment.course.course_id
            if course_id not in result:
                result[course_id] = {}
            result[course_id][at.assignment.assignment_id] = {
                "before": at.get_target_external_options_list(),
                "clear": "",
            }
            options_list = at.get_target_external_options_default().split(",")
            options_list[0] = "ImageView"  # set default options for images
            at.save_target_external_options_list(options_list)
            result[course_id][at.assignment.assignment_id][
                "clear"
            ] = at.get_target_external_options_list()

        print(json.dumps(result, indent=4, sort_keys=True))
