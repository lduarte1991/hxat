from django.test import TestCase, Client
from .models import TargetObject
from .views import *
from .forms import SourceForm
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

        self.tool_consumer = create_test_tc()
        self.other_request = self.tool_consumer.generate_launch_data()
        for key, value in self.other_request.items():
            if not value:
                self.other_request[key] = ''
        self.other_request.pop('oauth_body_hash')

    def tearDown(self):
        """
        """
        del self.assignment
        del self.tod
        del self.tool_consumer
        del self.other_request

    def test_call_view_loads(self):
        """
        """


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

    def test_create_new_source(self):
        self.client.force_login(user=self.user, backend=None)
        response = self.client.get('lti_init/launch_lti/source/create_new_source/')
        self.assertEqual(response.status_code, 200)

    def test_get_admin_url(self):
        """
        """
        self.assertEqual(
            self.tod.get_admin_url(),
            '/admin/target_object_database/targetobject/%d/change/' % self.tod.id
        )


# class TODModelTests(TestCase):
#
#     def test_create(self):
#
#         target_object = TargetObject.objects.create(
#
#         )
#         self.assertEqual("Test title", target_object.title)
