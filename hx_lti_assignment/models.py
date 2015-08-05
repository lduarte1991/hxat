from django.db import models
from target_object_database.models import TargetObject
from hx_lti_initializer.models import LTICourse
import uuid


class AssignmentTargets(models.Model):
	assignment = models.ForeignKey(
		"Assignment",
		verbose_name = 'Assignment',
	)
	target_object = models.ForeignKey(
		TargetObject,
		verbose_name = 'Source Material',
		unique = True,
	)
	order = models.IntegerField(
		verbose_name = 'Order',
	)
	target_external_css = models.CharField(
		max_length = 255,
		blank=True,
		help_text='(Optional) Please only input a URL to an externally hosted CSS file.'
	)

	class Meta:
		verbose_name = "Assignment Target"
		verbose_name_plural = "Assignment Targets"
		ordering = [
			'order',
		]

class Assignment(models.Model):
	"""
	This object will contain the objects and settings for the annotation tool
	"""

	assignment_id = models.CharField(max_length=100, blank=True, unique=True, default=uuid.uuid4)
	assignment_name = models.CharField(max_length=255, blank=False, default="No Assignment Name Given")
	assignment_objects = models.ManyToManyField(TargetObject, through="AssignmentTargets")
	annotation_database_url = models.CharField(max_length=255)
	annotation_database_apikey = models.CharField(max_length=255)
	annotation_database_secret_token = models.CharField(max_length=255)
	include_instructor_tab = models.BooleanField(help_text="Include a tab for instructor annotations.", default=False)
	allow_highlights = models.BooleanField(help_text="Allow predetermined tags with colors.", default=False)
	highlights_options = models.CharField(max_length=255, blank=True)
	allow_touch = models.BooleanField(help_text="Allow touch devices to use tool (warning, still experimental).", default=False)
	pagination_limit = models.IntegerField(help_text="How many annotations should show up when you hit the 'More' button?")
	allow_flags = models.BooleanField(help_text="Allow users to flag items as inappropriate/offensive.", default=False)

	TABS = (
		('Instructor', 'Instructor'),
		('MyNotes', 'My Notes'),
		('Public', 'Public'),
	)

	default_tab = models.CharField(choices=TABS, default="Public", max_length=20)
	course = models.ForeignKey(LTICourse)
	hidden = models.BooleanField(default=False)

	def __str__(self):
		return self.assignment_name

	def __unicode__(self):
		return u"%s" % self.assignment_name

	def object_before(self, id):
		if len(self.assignment_objects.all()) > 1:
			try:
				obj = TargetObject.objects.get(pk=id)
				assignment_target = AssignmentTargets.objects.get(assignment=self, target_object=obj)
				if assignment_target.order == 1:
					return None
				else:
					new_order = assignment_target.order-1
					return AssignmentTargets.objects.get(assignment=self, order=new_order)
			except:
				return None
		return None

	def object_after(self, id):
		if len(self.assignment_objects.all()) > 1:
			try:
				obj = TargetObject.objects.get(pk=id)
				assignment_target = AssignmentTargets.objects.get(assignment=self, target_object=obj)
				if assignment_target.order == len(self.assignment_objects.all()):
					return None
				else:
					new_order = assignment_target.order+1
					return AssignmentTargets.objects.get(assignment=self, order=new_order)
			except:
				return None
		return None

