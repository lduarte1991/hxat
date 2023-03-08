from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from hx_lti_assignment.models import Assignment, AssignmentTargets
from hx_lti_initializer.models import LTICourse, LTIProfile, LTIResourceLinkConfig
from lti import ToolConsumer
from target_object_database.models import TargetObject


class TODViewsTests(TestCase):
    def setUp(self):
        """
        1. Creates a test course.
        2. Creates a test Assignment.
        3. Creates a fake Target Object record.
        4. Starts the LTI tool consumer and makes a data launch request.
        """

        user = User(username="Luis", email="dfslkjfijeflkj")
        user.save()
        lti_profile = LTIProfile.objects.create(
            user=user, name=user.username, anon_id="luis123"
        )
        lti_profile.save()

        course = LTICourse(course_name="Fake Course", course_id="BlueMonkeyFake")
        course.save()
        course.course_admins.add(lti_profile)

        self.assignment = Assignment(
            assignment_name="Test", pagination_limit=10, course=course
        )
        self.assignment.save()

        self.tod = TargetObject(
            target_title="TObj2",
            target_author="Test Author",
            target_content="Fake Content2",
            target_citation="Fake Citation2",
            target_type="tx",
        )
        self.tod.save()

        self.aTarget = AssignmentTargets(
            assignment=self.assignment,
            target_object=self.tod,
            order=1,
            target_external_css="",
            target_instructions="Fake Instructions",
            target_external_options="",
        )
        self.aTarget.save()

        self.target_path = reverse("hx_lti_initializer:launch_lti")
        self.launch_url = "http://testserver{}".format(self.target_path)
        self.resource_link_id = "some_string_to_be_the_fake_resource_link_id"

        # set the starting resource
        lti_resource_link_config = LTIResourceLinkConfig.objects.create(
            resource_link_id=self.resource_link_id,
            assignment_target=self.aTarget,
        )

        self.consumer = ToolConsumer(
            consumer_key=settings.CONSUMER_KEY,
            consumer_secret=settings.LTI_SECRET,
            launch_url=self.launch_url,
            params={
                "lti_message_type": "basic-lti-launch-request",
                "lti_version": "LTI-1p0",
                "resource_link_id": self.resource_link_id,
                "lis_person_sourcedid": lti_profile.name,
                "lis_outcome_service_url": "fake_url",
                "user_id": lti_profile.anon_id,
                "roles": ["Learner"],
                "context_id": course.course_id,
            },
        )
        self.lti_params = self.consumer.generate_launch_data()

    def tearDown(self):
        del self.assignment
        del self.tod

    def test_call_view_loads(self):
        lti_params = self.consumer.generate_launch_data()
        response0 = self.client.post(self.target_path, lti_params)

        self.assertTrue(response0.status_code == 302)

        target_url = reverse(
            "target_object_database:open_target_object",
            kwargs={"collection_id": self.assignment.id, "target_obj_id": self.tod.id,},
        )
        response = self.client.get(target_url)
        self.assertTrue(response.status_code == 200)

        target_url = reverse(
            "target_object_database:open_target_object",
            kwargs={"collection_id": self.assignment.id, "target_obj_id": "987654321",},
        )
        response = self.client.get(target_url)
        self.assertTrue(response.status_code == 404)

    '''
    24feb20 naomi: not sure how relevant this test is, it seems no one uses
    this "get_admin_url" method...

    def test_get_admin_url(self):
        """
        """
        self.assertEqual(
            self.tod.get_admin_url(),
            '/admin/target_object_database/targetobject/%d/' % self.tod.id
        )
    '''
