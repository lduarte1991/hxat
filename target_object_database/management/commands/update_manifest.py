import glob
import json
import os
import traceback

from django.core.management import BaseCommand

from hx_lti_assignment.models import AssignmentTargets
from target_object_database.models import TargetObject


class Command(BaseCommand):
    def handle(self, *args, **kwargs):

        ig_targets = TargetObject.objects.filter(target_type="ig")
        result = {}
        for target in ig_targets:
            if target.target_content.startswith("https://oculus"):
                prefix, suffix = target.target_content.split("manifests/")
                p, s = suffix.split(":")
                nrs = f"https://nrs.lib.harvard.edu/URN-3:VPAL.HARVARDONLINE:{p}{s}:MANIFEST:2"

                result[target.id] = {
                    "previous": target.target_content,
                    "updated": nrs,
                }

                # update manifest url to mps
                target.target_content = nrs
                target.save()


        print(json.dumps(result, indent=4, sort_keys=True))

        all_img_at = AssignmentTargets.objects.filter(target_object__target_type="ig")
