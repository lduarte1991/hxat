from django.test import TestCase
from hx_lti_assignment.models import Assignment


class AssignmentTests(TestCase):
    """
    """
    def setUp(self):
        """
        """
        self.assignment = Assignment(
            assignment_name="Assignment One",
            annotation_database_url="http://fakedatabaseurl.com",
            annotation_database_apikey="apikey",
            annotation_database_secret_token="secret token",
            highlights_options="test1:red;test2:blue",
            pagination_limit="10"
        )

    def tearDown(self):
        """
        """
        del self.assignment

    def test_str_output(self):
        """
        """
        self.assertEqual(self.assignment.assignment_name, "Assignment One")
        self.assertEqual(self.assignment.__str__(), "Assignment One")
        self.assertEqual(self.assignment.assignment_name, self.assignment.__str__())  # noqa
