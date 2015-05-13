from django.db import models
from hx_lti_todapi.models import TargetObject
import uuid

class Assignment(models.Model):
	"""
	This object will contain the objects and settings for the annotation tool
	"""

	assignment_id = models.CharField(max_length=100, blank=True, unique=True, default=uuid.uuid4)
	assignment_objects = models.ManyToManyField(TargetObject)
	annotation_database_url = models.CharField(max_length=255)
	annotation_database_apikey = models.CharField(max_length=255)
	annotation_database_secret_token = models.CharField(max_length=255)
	include_instructor_tab = models.BooleanField(help_text="Include a tab for instructor annotations.", default=False)
	allow_highlights = models.BooleanField(help_text="Allow predetermined tags with colors.", default=False)
	highlights_options = models.CharField(max_length=255)
	allow_touch = models.BooleanField(help_text="Allow touch devices to use tool (warning, still experimental).", default=False)
	pagination_limit = models.IntegerField(help_text="How many annotations should show up when you hit the 'More' button?")
	allow_flags = models.BooleanField(help_text="Allow users to flag items as inappropriate/offensive.", default=False)

	TABS = (
		('Instructor', 'Instructor'),
		('My Notes', 'My Notes'),
		('Public', 'Public'),
	)

	default_tab = models.CharField(choices=TABS, default="Public", max_length=20)
