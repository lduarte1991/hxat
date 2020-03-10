import pytest


from hx_lti_initializer.models import LTICourse
from hx_lti_initializer.models import LTIProfile

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


