import glob
import json
import traceback
import os

from django.core.management import BaseCommand

from hx_lti_assignment.models import AssignmentTargets
from hx_lti_initializer.models import LTICourse


class Command(BaseCommand):
    def add_arguments(self,parser):
        parser.add_argument(
            "--manifest-dir", dest="mani_dir", required=False,
        )
        parser.add_argument(
            "--mani-filepath", dest="mani_filepath", required=False,
        )

    def gather_mani(self, mani_dir):
        all_mani = {}
        for filename in glob.glob(os.path.join(mani_dir, "*.json")):
            with open(os.path.join(mani_dir, filename), "r") as fd:
                mani = json.load(fd)
            # find manifest url
            all_mani[mani["@id"]] = mani
        return all_mani

    def get_image_assignments(self):
        img_at = []
        all_at = AssignmentTargets.objects.all()
        for at in all_at:
            if at.target_object.target_type == 'ig':
                # collect
                img_at.append(at)
        return img_at

    def handle(self, *args, **kwargs):
        all_mani = None
        mani_dir = kwargs.get("mani_dir", None)
        if mani_dir:
            all_mani = self.gather_mani(mani_dir)
            print(json.dumps(all_mani, indent=4, sort_keys=True))
            return(0)

        mani_filepath = kwargs.get("mani_filepath", None)
        if not mani_filepath:
            print("---------- unable to rename the canvases, missing manifests info")
            return(1)

        with open(mani_filepath, "r") as fd:
            all_mani = json.load(fd)

        result = {}
        all_img_at = self.get_image_assignments()
        for at in all_img_at:
            # skip course-v1:HarvardX+HUM1.10x+1T2022 due to mixed source_id in catchpy
            if at.assignment.course.course_id == "course-v1:HarvardX+HUM1.10x+1T2022":
                continue

            try:
                options_list = at.get_target_external_options_list()
                manifest = all_mani[at.target_object.target_content.strip()]
                manifest_id = manifest["@id"]
                canvas_id = all_mani[manifest_id]["sequences"][0]["canvases"][0]["@id"]
                if not options_list:
                    options_list = ["ImageView", "", "", "", "", ""]
                if len(options_list) == 1:
                    options_list.append("placeholder")
                options_list[0] = "ImageView"  # only view_type supported
                options_list[1] = canvas_id    # original canvas_id
                at.save_target_external_options_list(options_list)
                item = result.get(at.assignment.course.course_id, {})
                item[manifest_id] = options_list
                result[at.assignment.course.course_id] = item
            except Exception as e:
                item = result.get(at.assignment.course.course_id, {})
                item[manifest_id] = traceback.format_exc()
                result[at.assignment.course.course_id] = item

        print(json.dumps(result, indent=4, sort_keys=True))






