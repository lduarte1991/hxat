from django.test import TestCase, Client
from django.test.client import RequestFactory
from .models import TargetObject
from .views import *
from hx_lti_assignment.models import Assignment, AssignmentTargets
from hx_lti_initializer.models import LTICourse, LTIProfile
from hx_lti_initializer.test_helper import *

from hx_lti_initializer.utils import *
from django.http import Http404


class TODViewsTests(TestCase):
    """
    """
    def setUp(self):
        """
        1. Creates a test course.
        2. Creates a test Assignment.
        3. Creates a fake Target Object record.
        4. Starts the LTI tool consumer and makes a data launch request.
        """

        self.rf = RequestFactory()

        self.user = User(username="Luis", email="dfslkjfijeflkj")
        self.user.save()
        lti_profile = LTIProfile.objects.create(user=self.user)

        self.client = Client()

        course = LTICourse(
            course_name="Fake Course",
            course_id="BlueMonkeyFake"
        )
        course.save()
        course.course_admins.add(lti_profile)

        self.assignment = Assignment(
            assignment_name="Test",
            pagination_limit=10,
            course=course
        )
        self.assignment.save()

        self.tod = TargetObject(
            target_title="TObj2",
            target_author="Test Author",
            target_content="Fake Content2",
            target_citation="Fake Citation2",
            target_type="tx"
        )
        self.tod.save()

        self.aTarget = AssignmentTargets(
            assignment=self.assignment,
            target_object=self.tod,
            order=1,
            target_external_css="",
            target_instructions="Fake Instructions",
            target_external_options=""
        )


    def tearDown(self):
        """
        """
        del self.assignment
        del self.tod

    def test_call_view_loads(self):
        """
        """
        response = self.rf.post('lti_init/launch_lti/annotation/%s/%d' %
            (self.assignment.assignment_id, self.tod.id), {
            "lti_message_type": "basic-lti-launch-request",
            "oauth_consumer_key": TEST_CONSUMER_KEY,
            "lti_version": "LTI-1p0",
            "resource_link_id": "c28ddcf1b2b13c52757aed1fe9b2eb0a4e2710a3",
            "lis_result_sourcedid": "261-154-728-17-784",
            "lis_outcome_service_url": "http://localhost/lis_grade_passback",
            "launch_presentation_return_url": "http://example.com/lti_return",
            "custom_param1": "custom1",
            "custom_param2": "custom2",
            "oauth_signature": "aVQIRM6OkBku6yk3Guqyz+VUdgU=",
            "user_id": "234jfhrwekljrsfw8abcd35cseddda",
            "ext_lti_message_type": "extension-lti-launch",
            "roles": "Learner,Instructor,Observer",
            "lis_person_sourcedid": "fakeusername",
        })

        self.assertTrue(
            open_target_object(
                response,
                self.assignment.assignment_id,
                self.tod.id
            ).status_code == 200
        )

        response2 = self.client.post(
            'lti_init/launch_lti/annotation/%s/fake_id' %
            self.assignment.assignment_id
        )
        self.assertRaises(
            Http404,
            open_target_object,
            response2,
            self.assignment.assignment_id,
            34
        )

    def test_get_admin_url(self):
        """
        """
        self.assertEqual(
            self.tod.get_admin_url(),
            '/admin/target_object_database/targetobject/%d/change/' % self.tod.id
        )
