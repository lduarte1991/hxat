"""
hx_annotations/hx_lti_tools/hx_lti_initializer/tests.py

Documentation URL/Ref#: TODO
Test Script for app hx_lti_initializer

Original purpose of this app: This app should take a request from a tool consumer, authorize the user, log them in, and kickstart the lti tool.

Normal Test Case:
    1. Tool receives HTTP request
    2. Tool determines whether the user is authorized to access the product
    3. User account is either retrieved or created (if first time)
    4. User is logged in and sent to either the introduction page or the reference link passed in
    
Corner Cases Found:
    1. User tries to refresh page
    2. User tries to reach page via URL while logged in recently
    3. User tries to reach page via URL while not logged in
    4. User tries to view "Share" page while not logged in.
"""
from django.test import TestCase
from utils import *
from ims_lti_py.tool_provider import DjangoToolProvider

class LTIInitializerUtilsTests(TestCase):

    def setUp(self):
        """
        This is very simple, imitate the paramaters passed in via a request and create a tool provider from ims_lti_py. 
        """
        tool_provider_parameters = {
          "lti_message_type": "basic-lti-launch-request",
          "lti_version": "LTI-1p0",
          "resource_link_id": "c28ddcf1b2b13c52757aed1fe9b2eb0a4e2710a3",
          "lis_result_sourcedid": "261-154-728-17-784",
          "lis_outcome_service_url": "http://localhost/lis_grade_passback",
          "launch_presentation_return_url": "http://example.com/lti_return",
          "custom_param1": "custom1",
          "custom_param2": "custom2",
          "ext_lti_message_type": "extension-lti-launch",
          "roles": "Learner,Instructor,Observer"
        }
        self.tp = DjangoToolProvider('hi', 'oi', tool_provider_parameters)
    
    def tearDown(self):
        """
        Make sure to delete the provider created in the set up.
        """
        del self.tp
    
    def test_get_lti_value(self):
        """
        Should return the attribute within the LTI tool provider.
        """
        value_found = get_lti_value('launch_presentation_return_url', self.tp)
        self.assertEqual(value_found, 'http://example.com/lti_return')
    
    def test_get_lti_value_negation(self):
        """
        Should NOT return the wrong value for an attribute within the LTI tool provider, i.e. checking contraposition.
        """
        value_found = get_lti_value('launch_presentation_return_url', self.tp)
        self.assertNotEqual(value_found, 'http://fake.com/lti_return')