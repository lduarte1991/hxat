from django.test import TestCase
from target_object_database.models import TargetObject
from hx_lti_assignment.models import Assignment
from hx_lti_initializer.models import LTICourse
from hx_lti_initializer.test_helper import *
from target_object_database.views import *
from hx_lti_initializer.utils import *
from django.http import Http404

class TODViewsTests(TestCase):
	"""
	"""
	def setUp(self):
		"""
		"""
		course = LTICourse(course_name="Fake Course", course_id="BlueMonkeyFake")
		course.save()
		self.assignment = Assignment(assignment_name="Test", pagination_limit=10, course=course)
		self.assignment.save()
		self.tod = TargetObject(target_title="TObj2", target_author="Test Author", target_content="Fake Content2", target_citation="Fake Citation2", target_type="tx")
		self.tod.save()
		#self.assignment.assignment_objects.add(self.tod)
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
		#response = self.client.post('lti_init/launch_lti/annotation/%s/%d' % (self.assignment.assignment_id, self.tod.id), self.other_request)
		#self.assertTrue(open_target_object(response, self.assignment.assignment_id, self.tod.id).status_code == 200)
		#response2 = self.client.post('lti_init/launch_lti/annotation/%s/fake_id' % self.assignment.assignment_id)
		#self.assertRaises(Http404, open_target_object, response, self.assignment.assignment_id, 34)

	def test_get_admin_url(self):
		"""
		"""
		print self.tod.get_admin_url()
