from django.db import models
from target_object_database.models import TargetObject
from hx_lti_initializer.models import LTICourse
import uuid


class AssignmentTargets(models.Model):
    assignment = models.ForeignKey(
        "Assignment",
        verbose_name='Assignment',
    )
    target_object = models.ForeignKey(
        TargetObject,
        verbose_name='Source Material',
        unique=False,
    )
    order = models.IntegerField(
        verbose_name='Order',
    )
    target_external_css = models.CharField(
        max_length=255,
        blank=True,
        help_text='Only input a URL to an externally hosted CSS file.'
    )
    target_instructions = models.TextField(
        blank=True,
        null=True,
        help_text='Add instructions for this object in this assignment.'
    )
    target_external_options = models.TextField(
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = "Assignment Target"
        verbose_name_plural = "Assignment Targets"
        ordering = [
            'order',
        ]

    def get_target_external_options_list(self):
        """
        Returns a list of options that are saved to the target_external_options model attribute
        in CSV format.
        
        Notes:
        - since the model attribute could be null in the database, we have to
          check if it's None before trying parse it.
        - this field does not contain user-supplied values, so we don't need industrial-strength
          CSV parsing.
        """
        if self.target_external_options is None:
            return []
        return self.target_external_options.split(',')    

    def get_view_type_for_mirador(self):
        """
        """
        options = self.get_target_external_options_list()
        if len(options) == 1:
            return "ImageView"
        else:
            return options[0] if options[0] != '' else "ImageView"

    def get_canvas_id_for_mirador(self):
        """
        """
        options = self.get_target_external_options_list()
        if len(options) == 1:
            return None
        else:
            return options[1] if options[1] != '' else None

    def get_dashboard_hidden(self):
        """
        """
        options = self.get_target_external_options_list()
        if len(options) < 3:
            return "false"
        else:
            return options[2] if options[2] != '' else "false"


class Assignment(models.Model):
    """
    This object will contain the objects and settings for the annotation tool
    """

    assignment_id = models.CharField(
        max_length=100,
        blank=True,
        unique=True,
        default=uuid.uuid4
    )
    assignment_name = models.CharField(
        max_length=255,
        blank=False,
        default="No Assignment Name Given"
    )
    assignment_objects = models.ManyToManyField(
        TargetObject,
        through="AssignmentTargets"
    )
    annotation_database_url = models.CharField(max_length=255)
    annotation_database_apikey = models.CharField(max_length=255)
    annotation_database_secret_token = models.CharField(max_length=255)
    include_instructor_tab = models.BooleanField(
        help_text="Include a tab for instructor annotations.",
        default=False
    )
    allow_highlights = models.BooleanField(
        help_text="Allow predetermined tags with colors.",
        default=False
    )
    highlights_options = models.CharField(
        max_length=255,
        blank=True
    )
    allow_touch = models.BooleanField(
        help_text="Allow touch devices to use tool (warning, experimental).",
        default=False
    )
    pagination_limit = models.IntegerField(
        help_text="How many annotations should show up when you hit the 'More' button?"  # noqa
    )
    allow_flags = models.BooleanField(
        help_text="Allow users to flag items as inappropriate/offensive.",
        default=False
    )

    TABS = (
        ('Instructor', 'Instructor'),
        ('MyNotes', 'My Notes'),
        ('Public', 'Public'),
    )

    default_tab = models.CharField(
        choices=TABS,
        default="Public",
        max_length=20
    )
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
                assignment_target = AssignmentTargets.objects.get(
                    assignment=self,
                    target_object=obj
                )
                if assignment_target.order == 1:
                    return None
                else:
                    new_order = assignment_target.order-1
                    return AssignmentTargets.objects.get(
                        assignment=self,
                        order=new_order
                    )
            except:
                return None
        return None

    def object_after(self, id):
        if len(self.assignment_objects.all()) > 1:
            try:
                obj = TargetObject.objects.get(pk=id)
                assignment_target = AssignmentTargets.objects.get(
                    assignment=self,
                    target_object=obj
                )
                if assignment_target.order == len(self.assignment_objects.all()):  # noqa
                    return None
                else:
                    new_order = assignment_target.order+1
                    return AssignmentTargets.objects.get(
                        assignment=self,
                        order=new_order
                    )
            except:
                return None
        return None
