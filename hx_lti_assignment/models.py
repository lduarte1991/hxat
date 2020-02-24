from django.db import models
from target_object_database.models import TargetObject
from hx_lti_initializer.models import LTICourse
import requests
import uuid
import sys
import json
import logging

logger = logging.getLogger(__name__)


class AssignmentTargets(models.Model):
    assignment = models.ForeignKey(
        "Assignment",
        verbose_name='Assignment',
        on_delete=models.CASCADE
    )
    target_object = models.ForeignKey(
        TargetObject,
        verbose_name='Source Material',
        unique=False,
        on_delete=models.CASCADE
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
        logger.debug("OPTIONS: %s " % options)
        if options is None or len(options) <= 1:
            logger.debug('Trying to get canvas id but none in list')
            req = requests.get(self.target_object.all()[0].target_content)
            manifest = json.load(req.text)
            canv_id = manifest['sequences'][0]['canvases'][0]['@id']
            return canv_id
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

    def get_transcript_hidden(self):
        """
        """
        options = self.get_target_external_options_list()
        if len(options) < 4:
            return "false"
        else:
            return options[3] if options[3] != '' else "false"

    def get_transcript_download(self):
        """
        """
        options = self.get_target_external_options_list()
        if len(options) < 5:
            return "false"
        else:
            return options[4] if options[4] != '' else "false"

    def get_video_download(self):
        """
        """
        options = self.get_target_external_options_list()
        if len(options) < 6:
            return "false"
        else:
            return options[5] if options[5] != '' else "false"

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
    include_mynotes_tab = models.BooleanField(
        help_text="Include a tab for user's annotations. Warning: Turning this off will not allow students to make annotations.",
        default=True
    )
    include_public_tab = models.BooleanField(
        help_text="Include a tab for peer annotations. Used for private annotations. If you want users to view each other's annotations.",
        default=True
    )
    allow_highlights = models.BooleanField(
        help_text="Allow predetermined tags with colors.",
        default=False
    )
    highlights_options = models.TextField(
        max_length=1024,
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
    is_published = models.BooleanField(
        help_text="Published assignments are available to students while unpublished are not.",
        default=True
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
    course = models.ForeignKey(LTICourse, related_name="assignments", null=True, on_delete=models.SET_NULL)
    hidden = models.BooleanField(default=False)
    use_hxighlighter = models.BooleanField(default=False)
    common_inst_name = models.CharField(
        max_length=255,
        blank=True
    )

    class Meta:
        ordering = ['id']

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

    def array_of_tags(self):
        def getColorValues(color):
            values = ''
            if '#' in color:
                # hex
                new_color = color[1:]
                if len(new_color) == 3:
                    values = 'rgba(' + str(int(new_color[0] + new_color[0], 16)) + ',' + str(int(new_color[1] + new_color[1], 16)) + ',' + str(int(new_color[2] + new_color[2], 16)) + ',0.3)'
                else:
                    values = 'rgba(' + str(int(new_color[0] + new_color[1], 16)) + ',' + str(int(new_color[2] + new_color[3], 16)) + ',' + str(int(new_color[4] + new_color[5], 16)) + ',0.3)'
            elif 'rgb(' in color:
                values = color.replace('rgb(', 'rgba(').replace(')', ',0.3)')
            elif 'rgba(' in color:
                values = color
            else:
                stdCol = {
                    "acqua": '#0ff',
                    "teal": '#008080',
                    "blue": '#00f',
                    "navy": '#000080',
                    "yellow": '#ff0',
                    "olive": '#808000',
                    "lime": '#0f0',
                    "green": '#008000',
                    "fuchsia": '#f0f',
                    "purple": '#800080',
                    "red": '#f00',
                    "maroon": '#800000',
                    "white": '#fff',
                    "gray": '#808080',
                    "silver": '#c0c0c0',
                    "black": '#000'
                }
                if color in stdCol:
                    values = getColorValues(stdCol[color])
            return values

        if len(self.highlights_options) == 0:
            return []
        else:
            collection = self.highlights_options.split(',')
            result = []
            concat_tag_name = ""
            for col in collection:
                res = col.split(':')
                if len(res) %2 == 1:
                    res = col.split(';')
                try:
                    result.append((concat_tag_name + res[0], getColorValues(res[1])))
                    concat_tag_name = ""
                except:
                    concat_tag_name += res[0] + " "
            return result
