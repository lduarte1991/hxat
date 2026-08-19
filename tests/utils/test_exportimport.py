import json
import tempfile

import pytest
from django.contrib.auth.models import User

from hx_lti_assignment.models import Assignment, AssignmentTargets
from hx_lti_initializer.models import LTICourse, LTIProfile
from target_object_database.models import TargetObject
from utils.management.commands.exportcourse import Command as ExportCommand
from utils.management.commands.importcourse import (
    SEED_LOADER_ANON_ID,
    SEED_LOADER_SCOPE,
    SEED_LOADER_USERNAME,
    Command as ImportCommand,
)


def _run_export(course_ids=None, course_id=None):
    cmd = ExportCommand()
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as out_file:
        out_path = out_file.name

    if course_id:
        opts = {"cid": course_id, "input_json": None, "output": out_path}
    else:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as in_file:
            json.dump(course_ids, in_file)
            in_path = in_file.name
        opts = {"cid": None, "input_json": in_path, "output": out_path}

    cmd.handle(**opts)
    with open(out_path) as f:
        return json.load(f)


def _run_import(seed_data):
    cmd = ImportCommand()
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as f:
        json.dump(seed_data, f)
        in_path = f.name
    cmd.handle(input_json=in_path)


@pytest.mark.django_db
def test_export_basic_structure(assignment_target_factory, course_instructor_factory):
    course, instructor = course_instructor_factory()
    assignment_target_factory(course)

    result = _run_export(course_id=course.course_id)

    assert "exported_at" in result
    assert course.course_id in result["courses"]
    data = result["data"]
    assert len(data["courses"]) == 1
    assert len(data["assignments"]) == 1
    assert len(data["target_objects"]) == 1
    assert len(data["assignment_targets"]) == 1


@pytest.mark.django_db
def test_export_excludes_profiles_users_and_course_users(
    assignment_target_factory, course_instructor_factory, user_profile_factory
):
    course, instructor = course_instructor_factory()
    learner = user_profile_factory(roles=["Learner"])
    course.course_users.add(learner)
    assignment_target_factory(course)

    result = _run_export(course_id=course.course_id)

    data = result["data"]
    assert "users" not in data
    assert "profiles" not in data
    # no LTIResourceLinkConfig key either
    assert "resource_link_configs" not in data


@pytest.mark.django_db
def test_export_deduplicates_shared_target_object(
    course_instructor_factory, assignment_target_factory
):
    course1, _ = course_instructor_factory()
    course2, _ = course_instructor_factory()

    # share the same target object across two assignments in two courses
    shared_to = TargetObject.objects.create(
        target_title="Shared",
        target_author="Author",
        target_content="content",
        target_type="tx",
    )
    a1 = Assignment.objects.create(
        course=course1,
        assignment_name="A1",
        pagination_limit=50,
        annotation_database_url="http://x",
        annotation_database_apikey="k",
        annotation_database_secret_token="s",
    )
    a2 = Assignment.objects.create(
        course=course2,
        assignment_name="A2",
        pagination_limit=50,
        annotation_database_url="http://x",
        annotation_database_apikey="k",
        annotation_database_secret_token="s",
    )
    AssignmentTargets.objects.create(assignment=a1, target_object=shared_to, order=1)
    AssignmentTargets.objects.create(assignment=a2, target_object=shared_to, order=1)
    shared_to.target_courses.add(course1, course2)

    result = _run_export(course_ids=[course1.course_id, course2.course_id])

    to_list = result["data"]["target_objects"]
    assert len(to_list) == 1
    assert to_list[0]["id"] == shared_to.pk

    # target_courses trimmed to exported set
    assert set(to_list[0]["target_courses"]) == {course1.course_id, course2.course_id}


@pytest.mark.django_db
def test_export_trims_target_courses_to_exported_set(
    course_instructor_factory, assignment_target_factory
):
    course1, _ = course_instructor_factory()
    course2, _ = course_instructor_factory()  # not exported

    to = TargetObject.objects.create(
        target_title="T",
        target_author="A",
        target_content="c",
        target_type="tx",
    )
    a = Assignment.objects.create(
        course=course1,
        assignment_name="A",
        pagination_limit=50,
        annotation_database_url="http://x",
        annotation_database_apikey="k",
        annotation_database_secret_token="s",
    )
    AssignmentTargets.objects.create(assignment=a, target_object=to, order=1)
    to.target_courses.add(course1, course2)

    result = _run_export(course_id=course1.course_id)

    to_data = result["data"]["target_objects"][0]
    assert to_data["target_courses"] == [course1.course_id]


@pytest.mark.django_db
def test_import_creates_records(assignment_target_factory, course_instructor_factory):
    course, _ = course_instructor_factory()
    assignment_target_factory(course)

    seed = _run_export(course_id=course.course_id)

    # wipe the DB records to simulate a fresh DB
    AssignmentTargets.objects.all().delete()
    Assignment.objects.all().delete()
    TargetObject.objects.all().delete()
    LTICourse.objects.all().delete()

    _run_import(seed)

    assert LTICourse.objects.filter(course_id=course.course_id).exists()
    assert Assignment.objects.count() == 1
    assert TargetObject.objects.count() == 1
    assert AssignmentTargets.objects.count() == 1

    to = TargetObject.objects.first()
    assert to.target_creator is not None
    assert to.target_creator.anon_id == SEED_LOADER_ANON_ID
    assert to.target_creator.scope == SEED_LOADER_SCOPE


@pytest.mark.django_db
def test_import_target_courses_m2m(course_instructor_factory, assignment_target_factory):
    course, _ = course_instructor_factory()
    at = assignment_target_factory(course)
    at.target_object.target_courses.add(course)

    seed = _run_export(course_id=course.course_id)

    AssignmentTargets.objects.all().delete()
    Assignment.objects.all().delete()
    TargetObject.objects.all().delete()
    LTICourse.objects.all().delete()

    _run_import(seed)

    to = TargetObject.objects.first()
    assert to.target_courses.filter(course_id=course.course_id).exists()


@pytest.mark.django_db
def test_import_is_idempotent(assignment_target_factory, course_instructor_factory):
    course, _ = course_instructor_factory()
    assignment_target_factory(course)

    seed = _run_export(course_id=course.course_id)

    AssignmentTargets.objects.all().delete()
    Assignment.objects.all().delete()
    TargetObject.objects.all().delete()
    LTICourse.objects.all().delete()

    _run_import(seed)
    counts_after_first = {
        "courses": LTICourse.objects.count(),
        "assignments": Assignment.objects.count(),
        "target_objects": TargetObject.objects.count(),
        "assignment_targets": AssignmentTargets.objects.count(),
        "users": User.objects.filter(username=SEED_LOADER_USERNAME).count(),
    }

    _run_import(seed)
    counts_after_second = {
        "courses": LTICourse.objects.count(),
        "assignments": Assignment.objects.count(),
        "target_objects": TargetObject.objects.count(),
        "assignment_targets": AssignmentTargets.objects.count(),
        "users": User.objects.filter(username=SEED_LOADER_USERNAME).count(),
    }

    assert counts_after_first == counts_after_second


@pytest.mark.django_db
def test_import_ignores_unknown_fields(
    assignment_target_factory, course_instructor_factory
):
    course, _ = course_instructor_factory()
    assignment_target_factory(course)

    seed = _run_export(course_id=course.course_id)

    # inject a spurious field into each model's first record
    for key in ("courses", "target_objects", "assignments", "assignment_targets"):
        if seed["data"][key]:
            seed["data"][key][0]["__spurious_field__"] = "should be ignored"

    AssignmentTargets.objects.all().delete()
    Assignment.objects.all().delete()
    TargetObject.objects.all().delete()
    LTICourse.objects.all().delete()

    # should complete without raising
    _run_import(seed)

    assert LTICourse.objects.filter(course_id=course.course_id).exists()
