import json

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from hx_lti_assignment.models import Assignment, AssignmentTargets
from hx_lti_initializer.models import LTICourse, LTIProfile
from target_object_database.models import TargetObject

SEED_LOADER_USERNAME = "seed-loader"
SEED_LOADER_ANON_ID = "seed-loader"
SEED_LOADER_SCOPE = "seed"


def _safe_defaults(model, data_dict):
    field_names = {f.name for f in model._meta.get_fields() if hasattr(f, "column")}
    return {k: v for k, v in data_dict.items() if k in field_names}


class Command(BaseCommand):
    help = (
        "Import a seed JSON file produced by exportcourse into the target database. "
        "Uses update_or_create on natural keys; re-running is idempotent. "
        "Creates a fixed 'seed-loader' identity as target_creator for TargetObjects. "
        "NOTE: the target DB should be fresh or previously seeded from the same file "
        "to avoid TargetObject PK collisions."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--input-json",
            dest="input_json",
            required=True,
            help="Path to the seed JSON file produced by exportcourse",
        )

    def handle(self, *args, **options):
        json_file = options["input_json"]

        with open(json_file, "r") as fd:
            seed = json.loads(fd.read())

        data = seed.get("data", {})
        created = {}
        updated = {}
        warnings = []

        def _tally(model_name, was_created):
            bucket = created if was_created else updated
            bucket[model_name] = bucket.get(model_name, 0) + 1

        # step 1: seed-loader identity
        loader_user, c = User.objects.get_or_create(
            username=SEED_LOADER_USERNAME,
            defaults={"is_staff": False},
        )
        _tally("auth.User", c)

        loader_profile, c = LTIProfile.objects.get_or_create(
            anon_id=SEED_LOADER_ANON_ID,
            scope=SEED_LOADER_SCOPE,
            defaults={"user": loader_user},
        )
        _tally("LTIProfile", c)

        # step 2: courses
        course_map = {}
        for c_data in data.get("courses", []):
            course_id = c_data["course_id"]
            defaults = _safe_defaults(LTICourse, {
                k: v for k, v in c_data.items() if k != "course_id"
            })
            course, c = LTICourse.objects.update_or_create(
                course_id=course_id,
                defaults=defaults,
            )
            course_map[course_id] = course
            _tally("LTICourse", c)

        # step 3: target objects
        to_map = {}
        for to_data in data.get("target_objects", []):
            pk = to_data["id"]
            target_courses_ids = to_data.pop("target_courses", [])
            defaults = _safe_defaults(TargetObject, {
                k: v for k, v in to_data.items() if k != "id"
            })
            defaults["target_creator"] = loader_profile
            to, c = TargetObject.objects.update_or_create(
                pk=pk,
                defaults=defaults,
            )
            to_map[pk] = (to, target_courses_ids)
            _tally("TargetObject", c)

        # step 4: assignments
        assignment_map = {}
        for a_data in data.get("assignments", []):
            assignment_id = a_data["assignment_id"]
            course_id = a_data.pop("course_id", None)
            course = course_map.get(course_id)
            if course is None and course_id:
                warnings.append(
                    "assignment {}: course {} not in seed, leaving course null".format(
                        assignment_id, course_id
                    )
                )
            defaults = _safe_defaults(Assignment, {
                k: v for k, v in a_data.items() if k != "assignment_id"
            })
            defaults["course"] = course
            assignment, c = Assignment.objects.update_or_create(
                assignment_id=assignment_id,
                defaults=defaults,
            )
            assignment_map[assignment_id] = assignment
            _tally("Assignment", c)

        # step 5: assignment targets
        for at_data in data.get("assignment_targets", []):
            assignment_id = at_data["assignment_id"]
            target_object_id = at_data["target_object_id"]
            assignment = assignment_map.get(assignment_id)
            to_entry = to_map.get(target_object_id)
            if assignment is None or to_entry is None:
                warnings.append(
                    "skipping assignment_target: assignment {} or target_object {} not found".format(
                        assignment_id, target_object_id
                    )
                )
                continue
            to, _ = to_entry
            defaults = _safe_defaults(AssignmentTargets, {
                k: v for k, v in at_data.items()
                if k not in ("assignment_id", "target_object_id")
            })
            _, c = AssignmentTargets.objects.update_or_create(
                assignment=assignment,
                target_object=to,
                defaults=defaults,
            )
            _tally("AssignmentTargets", c)

        # step 6: target_courses M2M
        for pk, (to, target_courses_ids) in to_map.items():
            courses = [course_map[cid] for cid in target_courses_ids if cid in course_map]
            to.target_courses.set(courses)

        summary = {
            "created": created,
            "updated": updated,
            "warnings": warnings,
        }
        self.stdout.write(json.dumps(summary, indent=2))
