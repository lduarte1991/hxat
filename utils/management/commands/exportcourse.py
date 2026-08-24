import json
import sys
from datetime import datetime, timezone

from django.core.management.base import BaseCommand

from hx_lti_assignment.models import Assignment, AssignmentTargets
from hx_lti_initializer.models import LTICourse
from target_object_database.models import TargetObject


class Command(BaseCommand):
    help = (
        "Export a representative set of courses and their full dependency graph "
        "to a JSON seed file. Exports: LTICourse, Assignment, AssignmentTargets, "
        "TargetObject. Does NOT export LTIProfile, auth.User, LTIResourceLinkConfig, "
        "or course_users. Target DB should be fresh or previously seeded from the "
        "same file to avoid TargetObject PK collisions."
    )

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("--course-id", dest="cid", help="Single course ID to export")
        group.add_argument(
            "--input-json",
            dest="input_json",
            help="JSON file containing a list of course ID strings to export",
        )
        parser.add_argument(
            "--output",
            dest="output",
            help="Output file path; omit to write to stdout",
        )

    def handle(self, *args, **options):
        cid = options.get("cid")
        json_file = options.get("input_json")
        output_path = options.get("output")

        if cid:
            course_ids = [cid]
        else:
            with open(json_file, "r") as fd:
                course_ids = json.loads(fd.read())

        exported_course_ids = set()
        courses_data = []
        target_objects_by_pk = {}
        assignments_data = []
        assignment_targets_data = []
        warnings = []

        for course_id in course_ids:
            try:
                course = LTICourse.objects.get(course_id=course_id)
            except LTICourse.DoesNotExist:
                warnings.append("course({}) not found, skipping".format(course_id))
                self.stderr.write(self.style.WARNING(warnings[-1]))
                continue

            exported_course_ids.add(course_id)
            courses_data.append({
                "course_id": course.course_id,
                "course_name": course.course_name,
                "course_external_css_default": course.course_external_css_default,
            })

            for assignment in course.assignments.all():
                assignments_data.append({
                    "assignment_id": str(assignment.assignment_id),
                    "assignment_name": assignment.assignment_name,
                    "course_id": course_id,
                    "annotation_database_url": assignment.annotation_database_url,
                    "annotation_database_apikey": assignment.annotation_database_apikey,
                    "annotation_database_secret_token": assignment.annotation_database_secret_token,
                    "include_instructor_tab": assignment.include_instructor_tab,
                    "include_mynotes_tab": assignment.include_mynotes_tab,
                    "include_public_tab": assignment.include_public_tab,
                    "allow_highlights": assignment.allow_highlights,
                    "highlights_options": assignment.highlights_options,
                    "allow_touch": assignment.allow_touch,
                    "pagination_limit": assignment.pagination_limit,
                    "allow_flags": assignment.allow_flags,
                    "is_published": assignment.is_published,
                    "default_tab": assignment.default_tab,
                    "hidden": assignment.hidden,
                    "use_hxighlighter": assignment.use_hxighlighter,
                    "common_inst_name": assignment.common_inst_name,
                })

                for at in AssignmentTargets.objects.filter(assignment=assignment):
                    to = at.target_object
                    if to.pk not in target_objects_by_pk:
                        target_objects_by_pk[to.pk] = {
                            "id": to.pk,
                            "target_title": to.target_title,
                            "target_author": to.target_author,
                            "target_content": to.target_content,
                            "target_citation": to.target_citation,
                            "target_type": to.target_type,
                        }

                    assignment_targets_data.append({
                        "assignment_id": str(assignment.assignment_id),
                        "target_object_id": to.pk,
                        "order": at.order,
                        "target_external_css": at.target_external_css,
                        "target_instructions": at.target_instructions,
                        "target_external_options": at.target_external_options,
                    })

        # trim target_courses M2M to exported set only
        for pk, to_data in target_objects_by_pk.items():
            to = TargetObject.objects.get(pk=pk)
            to_data["target_courses"] = [
                c.course_id
                for c in to.target_courses.all()
                if c.course_id in exported_course_ids
            ]

        result = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "courses": list(exported_course_ids),
            "data": {
                "courses": courses_data,
                "target_objects": list(target_objects_by_pk.values()),
                "assignments": assignments_data,
                "assignment_targets": assignment_targets_data,
            },
        }

        output = json.dumps(result, indent=2)
        summary = {
            "courses": len(courses_data),
            "target_objects": len(target_objects_by_pk),
            "assignments": len(assignments_data),
            "assignment_targets": len(assignment_targets_data),
            "warnings": warnings,
        }

        if output_path:
            with open(output_path, "w") as fd:
                fd.write(output)
            self.stdout.write(json.dumps(summary, indent=2))
        else:
            sys.stdout.write(output)
            self.stderr.write(json.dumps(summary, indent=2))
