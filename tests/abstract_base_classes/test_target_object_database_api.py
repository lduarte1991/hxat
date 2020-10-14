"""
hx-annotations-lti/abstract_base_classes/target_object_database_api.py

Documentation URL/Ref#: TODO
Test Script for the Target Object Database API and its current implementation

Original purpose of this app:
    1) Create an API for the Target Object Database and what it expects
    2) Set up an implementation of the object
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from target_object_database.models import TargetObject
from hx_lti_initializer.models import LTIProfile, LTICourse
from abstract_base_classes.target_object_database_api import TODAPI_LTI
from abstract_base_classes.target_object_database_api import TOD_Implementation
from abstract_base_classes.target_object_database_api import TODAPI_LTI, TOD_Implementation


class LTITODAPITests(TestCase):
    """
    """

    def setUp(self):
        """
        """
        TODAPI_LTI.__abstractmethods__ = set()
        self.sampleTODAPI = TODAPI_LTI()

    def tearDown(self):
        """
        """
        del self.sampleTODAPI

    def test_abc_TODAPI_LTI(self):
        """
        """
        self.assertIsInstance(self.sampleTODAPI, TODAPI_LTI)

        # not sure if this is considered cheating, but as we are testing the
        # non-implementation of functions, this might be okay. Because you
        # can't make abstract methods static within an abstract base class, it
        # treats them as class methods, thus below we are passing in one less
        # trivial parameter because class methods also pass in "self" as a
        # parameter first
        self.assertRaises(
            NotImplementedError,
            self.sampleTODAPI.get_own_targets_from_course,
            ''
        )
        self.assertRaises(
            NotImplementedError,
            self.sampleTODAPI.get_own_targets_as_user
        )


class TOD_ImplementationTests(TestCase):
    """
    """

    def createFakeUser(self, username, userid):
        user = User.objects.create_user(username, userid)
        user.set_unusable_password()
        user.is_superuser = False
        user.is_staff = False
        user.save()
        lti_profile = LTIProfile.objects.create(user=user)
        return user, lti_profile

    def setUp(self):
        """
        """
        self.sampleImplementation = TOD_Implementation()
        self.user1, self.ltiprofile1 = self.createFakeUser("fakeusername1", "fakeuserid1")
        self.user2, self.ltiprofile2 = self.createFakeUser("fakeusername2", "fakeuserid2")

        self.samplecourse = LTICourse.create_course(
            "fake_course",
            self.ltiprofile1
        )
        self.samplecourse.course_name = "Fake Course"
        self.samplecourse.save()
        self.target1 = TargetObject(
            target_title="TObj1",
            target_author="Test Author",
            target_content="Fake Content",
            target_citation="Fake Citation",
            target_type="tx"
        )
        self.target1.save()
        self.target1.target_courses.add(self.samplecourse)
        self.target2 = TargetObject(
            target_title="TObj2",
            target_author="Test Author",
            target_content="Fake Content2",
            target_citation="Fake Citation2",
            target_type="tx"
        )
        self.target2.save()
        self.target2.target_courses.add(self.samplecourse)

    def tearDown(self):
        """
        """
        del self.sampleImplementation
        del self.ltiprofile1
        del self.ltiprofile2
        del self.samplecourse
        del self.target1
        del self.target2

    def test_implentation_of_TODAPI_LTI(self):
        """
        """
        self.assertIsInstance(self.sampleImplementation, TOD_Implementation)
        self.assertIsInstance(self.sampleImplementation, TODAPI_LTI)

    def test_get_own_targets_from_course(self):
        """
        """
        self.assertTrue(len(TOD_Implementation.get_own_targets_from_course("fake_course")) == 2)  # noqa
        self.assertRaises(ObjectDoesNotExist, TOD_Implementation.get_own_targets_from_course, 'fake_course2')  # noqa
        course2 = LTICourse.create_course('fake_course2', self.ltiprofile1)
        self.assertTrue(len(TOD_Implementation.get_own_targets_from_course("fake_course2")) == 0)  # noqa

    def test_get_dict_of_files_from_courses(self):
        """
        """
        dict_of_targets = TOD_Implementation.get_dict_of_files_from_courses(
            LTICourse.get_all_courses()
        )
        self.assertIsInstance(dict_of_targets, dict)
        self.assertTrue(len(dict_of_targets['Fake Course']) == 2)
        self.assertTrue(self.target1 in dict_of_targets['Fake Course'])
        self.assertTrue(self.target2 in dict_of_targets['Fake Course'])

    def test_get_own_targets_as_user(self):
        """
        """
        self.assertTrue(len(TOD_Implementation.get_own_targets_as_user(self.ltiprofile1)) == 2)  # noqa
        self.assertTrue(len(TOD_Implementation.get_own_targets_as_user(self.ltiprofile2)) == 0)  # noqa
