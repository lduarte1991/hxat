from django.test import TestCase
from target_object_database.models import TargetObject
from hx_lti_assignment.models import Assignment, AssignmentTargets
from hx_lti_initializer.models import LTICourse, LTIProfile
from hx_lti_initializer.test_helper import *
from target_object_database.views import *
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

        user = User(username="Luis", email="dfslkjfijeflkj")
        user.save()

        lti_profile = LTIProfile.objects.get(user=user)

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
        response = self.client.post(
            'lti_init/launch_lti/annotation/%s/%d' %
            (self.assignment.assignment_id, self.tod.id), self.other_request)
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
            '/admin/target_object_database/targetobject/%d/' % self.tod.id
        )
