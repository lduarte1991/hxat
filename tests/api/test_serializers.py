import json

import pytest
from hx_lti_assignment.models import AssignmentTargets
from hx_lti_initializer.models import LTIResourceLinkConfig
from hxat.apps.api.serializers import LTICourseSerializer


@pytest.mark.django_db
def test_course_serializer_ok(random_assignment_target):
    assignment = random_assignment_target["assignment"]
    target_object = random_assignment_target["target_object"]
    assignment_target = random_assignment_target["assignment_target"]
    profile = random_assignment_target["profile"]
    course = random_assignment_target["course"]

    # set starting target_object
    assignment_target = AssignmentTargets.get_by_assignment_id(
        assignment_id=assignment.assignment_id,
        target_object_id=target_object.id,
    )
    config = LTIResourceLinkConfig.objects.create(
        resource_link_id="fake_resource_link_id_for_test",
        assignment_target=assignment_target,
    )
    config.save()

    serializer = LTICourseSerializer(instance=course)
    result = serializer.data

    assert result["course_id"] == course.course_id
    assert result["assignments"][0]["assignment_id"] == str(assignment.assignment_id)
    assert (
        result["assignments"][0]["assignmenttargets_set"][0]["target_object"][
            "target_title"
        ]
        == target_object.target_title
    )
    assert (
        result["assignments"][0]["assignmenttargets_set"][0][
            "ltiresourcelinkconfig_set"
        ][0]["resource_link_id"]
        == "fake_resource_link_id_for_test"
    )
    assert result["course_admins"][0]["anon_id"] == str(profile.anon_id)

    print("---------------- result({})".format(json.dumps(result, indent=4)))
    # assert 1 < 0
