import pytest


from hx_lti_initializer.models import LTICourse
from hx_lti_initializer.models import LTIProfile
from hx_lti_initializer.models import LTIResourceLinkConfig

from .conftest import random_instructor
from .conftest import random_learner


@pytest.mark.django_db
def test_LTIProfile_create(random_instructor):
    """
    Checks that an LTIProfile object was automatically created
    as soon as a user object was created in setup.
    """
    instructor = LTIProfile.objects.get(user=random_instructor['user'])

    assert(isinstance(instructor, LTIProfile))
    assert(instructor.__unicode__() == instructor.user.username)


@pytest.mark.django_db
def test_LTICourse_create_course(random_instructor):
    """
    Checks that you can make a course given a course id and an instructor
    """
    instructor = random_instructor['profile']

    course_object = LTICourse.create_course('test_course_id', instructor)
    assert(isinstance(course_object, LTICourse))
    assert(course_object.__unicode__() == course_object.course_name)


@pytest.mark.django_db
def test_LTICourse_get_course_by_id(random_instructor):
    """
    Checks that you can get a course given an id.
    """
    instructor = random_instructor['profile']
    course_object = LTICourse.create_course('test_course_id', instructor)
    course_to_test = LTICourse.get_course_by_id('test_course_id')

    assert(isinstance(course_to_test, LTICourse))
    assert(course_object == course_to_test)
    assert(course_to_test.course_id == 'test_course_id')


@pytest.mark.django_db
def test_LTICourse_get_courses_of_admin(random_instructor):
    """
    Checks that it returns a list of all the courses for that admin.
    """
    instructor = random_instructor['profile']

    course_object = LTICourse.create_course('test_course_id', instructor)
    list_of_courses = LTICourse.get_courses_of_admin(instructor)
    assert(isinstance(list_of_courses, list))
    assert(len(list_of_courses) == 1)
    assert(course_object in list_of_courses)

    course_object2 = LTICourse.create_course('test_course_id2', instructor)
    list_of_courses2 = LTICourse.get_courses_of_admin(instructor)
    assert(len(list_of_courses2) == 2)
    assert(course_object2 in list_of_courses2)


@pytest.mark.django_db
def test_LTICourse_get_all_courses(random_instructor, random_learner):
    """
    Checks that all courses are returned regardless of admin user
    """
    instructor1 = LTIProfile.objects.get(user_id=random_instructor['user'].pk)
    instructor2 = LTIProfile.objects.get(user_id=random_learner['user'].pk)

    list_of_courses = LTICourse.get_all_courses()
    assert(isinstance(list_of_courses, list))
    assert(len(list_of_courses) == 0)

    LTICourse.create_course('test_course_id', instructor1)
    list_of_courses2 = LTICourse.get_all_courses()
    assert(isinstance(list_of_courses2, list))
    assert(len(list_of_courses2) == 1)

    LTICourse.create_course('test_course_id2', instructor2)
    list_of_courses3 = LTICourse.get_all_courses()
    assert(isinstance(list_of_courses3, list))
    assert(len(list_of_courses3) == 2)

@pytest.mark.django_db
def test_LTIResourceLinkConfig_create(random_assignment_target):
    assignment = random_assignment_target['assignment']
    target_object = random_assignment_target['target_object']
    assignment_target = random_assignment_target['assignment_target']
    resource_link_id = 'FakeResourceLinkID'

    lti_resource_link_config = LTIResourceLinkConfig.objects.create(
        resource_link_id=resource_link_id,
        assignment_target=assignment_target, 
    )
    assert(isinstance(lti_resource_link_config, LTIResourceLinkConfig))
    assert(lti_resource_link_config.resource_link_id == resource_link_id)
    assert(assignment_target.assignment.pk == assignment.pk)
    assert(assignment_target.target_object.pk == target_object.pk)

    lti_resource_link_config.delete()

@pytest.mark.django_db
def test_LTIResourceLinkConfig_target_object_removed_from_assignment(random_assignment_target):
    assignment = random_assignment_target['assignment']
    target_object = random_assignment_target['target_object']
    assignment_target = random_assignment_target['assignment_target']
    resource_link_id = 'FakeResourceLinkID'

    lti_resource_link_config = LTIResourceLinkConfig.objects.create(
        resource_link_id=resource_link_id,
        assignment_target=assignment_target,
    )

    assert(LTIResourceLinkConfig.objects.filter(resource_link_id=resource_link_id).exists())
    assignment.assignment_objects.remove(target_object)
    assert(not LTIResourceLinkConfig.objects.filter(resource_link_id=resource_link_id).exists())

@pytest.mark.django_db
def test_LTIResourceLinkConfig_target_object_deleted(random_assignment_target):
    assignment = random_assignment_target['assignment']
    target_object = random_assignment_target['target_object']
    assignment_target = random_assignment_target['assignment_target']
    resource_link_id = 'FakeResourceLinkID'

    lti_resource_link_config = LTIResourceLinkConfig.objects.create(
        resource_link_id=resource_link_id,
        assignment_target=assignment_target,
    )

    assert(LTIResourceLinkConfig.objects.filter(resource_link_id=resource_link_id).exists())
    deleted_target_object = target_object.delete()
    assert(deleted_target_object)
    assert(not LTIResourceLinkConfig.objects.filter(resource_link_id=resource_link_id).exists())

@pytest.mark.django_db
def test_LTIResourceLinkConfig_assignment_deleted(random_assignment_target):
    assignment = random_assignment_target['assignment']
    assignment_target = random_assignment_target['assignment_target']
    resource_link_id = 'FakeResourceLinkID'

    lti_resource_link_config = LTIResourceLinkConfig.objects.create(
        resource_link_id=resource_link_id,
        assignment_target=assignment_target,
    )

    assert(LTIResourceLinkConfig.objects.filter(resource_link_id=resource_link_id).exists())
    deleted_assignment = assignment.delete()
    assert(deleted_assignment)
    assert(not LTIResourceLinkConfig.objects.filter(resource_link_id=resource_link_id).exists())
