import json
import logging
import uuid

import requests
from django.db import models
from hx_lti_initializer.models import LTICourse
from requests.exceptions import HTTPError, Timeout
from target_object_database.models import TargetObject

logger = logging.getLogger(__name__)


class AssignmentTargets(models.Model):
    # defaults for target_external_options
    VIEWTYPE_DEFAULT = ""
    CANVASID_DEFAULT = ""
    DASHBOARDHIDDEN_DEFAULT = "false"
    TRANSCRIPTHIDDEN_DEFAULT = "false"
    TRANSCRIPTDOWNLOAD_DEFAULT = "false"
    VIDEODOWNLOAD_DEFAULT = "false"
    TARGET_OPTIONS_LEN = 6

    assignment = models.ForeignKey(
        "Assignment", verbose_name="Assignment", on_delete=models.CASCADE
    )
    target_object = models.ForeignKey(
        TargetObject,
        verbose_name="Source Material",
        unique=False,
        on_delete=models.CASCADE,
    )
    order = models.IntegerField(
        verbose_name="Order",
    )
    target_external_css = models.CharField(
        max_length=255,
        blank=True,
        help_text="Only input a URL to an externally hosted CSS file.",
    )
    target_instructions = models.TextField(
        blank=True,
        null=True,
        help_text="Add instructions for this object in this assignment.",
    )
    target_external_options = models.TextField(
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Assignment Target"
        verbose_name_plural = "Assignment Targets"
        ordering = [
            "order",
        ]

    def get_target_external_options_list(self):
        """
        Returns a list of options that are saved to the target_external_options model attribute
        in CSV format.

        Notes:
        - since the model attribute could be null in the database, we have to check if it's None before trying parse it.
          07apr23 nmaekawa: setting default values to always have all options present
        - this field does not contain user-supplied values, so we don't need industrial-strength CSV parsing.

        Order of options:  # note that these are javaSCRIPT types!
          1. ViewType for mirador: string
          2. CanvasID for mirador: string|integer
          3. DashboardHidden: boolean
          4. TranscriptHidden: boolean
          5. TranscriptDownload: boolean
          6. VideoDownload: boolean
        """
        opts = (
            self.target_external_options.split(",")
            if self.target_external_options
            else []
        )
        if len(opts) < type(self).TARGET_OPTIONS_LEN:
            self.save_target_external_options_list(opts)  # self-healing defaults
        return self.target_external_options.split(",")

    def get_target_external_options_default(self):
        return "{},{},{},{},{},{}".format(
            type(self).VIEWTYPE_DEFAULT,
            type(self).CANVASID_DEFAULT,
            type(self).DASHBOARDHIDDEN_DEFAULT,
            type(self).TRANSCRIPTHIDDEN_DEFAULT,
            type(self).TRANSCRIPTDOWNLOAD_DEFAULT,
            type(self).VIDEODOWNLOAD_DEFAULT,
        )

    def save_target_external_options_list(self, options_list):
        new_value = self.get_target_external_options_default()
        new_value_list = new_value.split(",")  # set defaults
        if len(options_list) == 0:
            logger.warning("target_external_options to default, empty NOT ALLOWED")
        else:
            for i in range(6):
                try:
                    if options_list[i]:  # only replace if not blank
                        new_value_list[i] = options_list[i]
                except IndexError:
                    break  # keep default values
            new_value = ",".join([x.strip() for x in new_value_list])
        self.target_external_options = new_value
        self.save()

    def get_view_type_for_mirador(self):
        options = self.get_target_external_options_list()
        if not options[0]:  # self-healing default
            options[0] = "ImageView"
            self.save_target_external_options_list(options)
        return options[0]

    def get_canvas_id_for_mirador(self):
        options = self.get_target_external_options_list()
        logger.debug("OPTIONS: %s " % options)

        # Retrieve first canvas ID in the IIIF manifest if none is specified in the options list.
        # 07apr23 nmaekawa: SAVING canvas_id in the db!!!
        # -- canvas-id is saved as source_id in annotations and used as a search parameter
        #    when we moved iiif infrastructure to huit, all canvas-ids changed rendering
        #    past annotations unsearchable! Besides, we don't need to pull the manifest every time
        #    to have the canvas-id.
        if not options[1]:
            manifest_url = self.target_object.target_content
            try:
                req = requests.get(manifest_url, timeout=10)
                req.raise_for_status()
            except Timeout:
                logger.warning(
                    f"Request for manifest timed out: AssignmentTarget {self.pk} manifest: {manifest_url}"
                )
                return None
            except HTTPError as e:
                logger.error(
                    f"Failed to request manifest: AssignmentTarget {self.pk} status {e.response.status_code} manifest: {manifest_url}"
                )
                return None

            try:
                manifest = json.loads(req.text)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse manifest: AssignmentTarget {self.pk}")
                return None

            try:
                options[1] = manifest["sequences"][0]["canvases"][0]["@id"]
            except (KeyError, IndexError):
                logger.error(
                    f"Failed to extract canvas ID from manifest: AssignmentTarget {self.pk}"
                )
                return None
            self.save_target_external_options_list(options)  # self-healing
        return options[1]

    def get_dashboard_hidden(self):
        options = self.get_target_external_options_list()
        return options[2]

    def get_transcript_hidden(self):
        options = self.get_target_external_options_list()
        return options[3]

    def get_transcript_download(self):
        options = self.get_target_external_options_list()
        return options[4]

    def get_video_download(self):
        options = self.get_target_external_options_list()
        return options[5]

    @classmethod
    def get_by_assignment_id(cls, assignment_id, target_object_id):
        assignment = None
        try:
            assignment = Assignment.objects.get(assignment_id=assignment_id)
        except Assignment.DoesNotExist:
            return None

        assignment_target = None
        try:
            assignment_target = cls.objects.get(
                assignment=assignment, target_object_id=target_object_id
            )
        except AssignmentTargets.DoesNotExist:
            return None

        return assignment_target

    def __str__(self):
        return "%s - %s" % (
            self.assignment.assignment_name,
            self.target_object.target_title,
        )


class Assignment(models.Model):
    """
    This object will contain the objects and settings for the annotation tool
    """

    assignment_id = models.CharField(
        max_length=100, blank=True, unique=True, default=uuid.uuid4
    )
    assignment_name = models.CharField(
        max_length=255, blank=False, default="No Assignment Name Given"
    )
    assignment_objects = models.ManyToManyField(
        TargetObject, through="AssignmentTargets"
    )
    annotation_database_url = models.CharField(max_length=255)
    annotation_database_apikey = models.CharField(max_length=255)
    annotation_database_secret_token = models.CharField(max_length=255)
    include_instructor_tab = models.BooleanField(
        help_text="Include a tab for instructor annotations.", default=False
    )
    include_mynotes_tab = models.BooleanField(
        help_text="Include a tab for user's annotations. Warning: Turning this off will not allow students to make annotations.",
        default=True,
    )
    include_public_tab = models.BooleanField(
        help_text="Include a tab for peer annotations. Used for private annotations. If you want users to view each other's annotations.",
        default=True,
    )
    allow_highlights = models.BooleanField(
        help_text="Allow predetermined tags with colors.", default=False
    )
    highlights_options = models.TextField(max_length=1024, blank=True)
    allow_touch = models.BooleanField(
        help_text="Allow touch devices to use tool (warning, experimental).",
        default=False,
    )
    pagination_limit = models.IntegerField(
        help_text="How many annotations should show up when you hit the 'More' button?"  # noqa
    )
    allow_flags = models.BooleanField(
        help_text="Allow users to flag items as inappropriate/offensive.", default=False
    )
    is_published = models.BooleanField(
        help_text="Published assignments are available to students while unpublished are not.",
        default=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    TABS = (
        ("Instructor", "Instructor"),
        ("MyNotes", "My Notes"),
        ("Public", "Public"),
    )

    default_tab = models.CharField(choices=TABS, default="Public", max_length=20)
    course = models.ForeignKey(
        LTICourse, related_name="assignments", null=True, on_delete=models.SET_NULL
    )
    hidden = models.BooleanField(default=False)
    use_hxighlighter = models.BooleanField(default=False)
    common_inst_name = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.assignment_name

    def __unicode__(self):
        return "%s" % self.assignment_name

    def object_before(self, id):
        if len(self.assignment_objects.all()) > 1:
            try:
                obj = TargetObject.objects.get(pk=id)
                assignment_target = AssignmentTargets.objects.get(
                    assignment=self, target_object=obj
                )
                if assignment_target.order == 1:
                    return None
                else:
                    new_order = assignment_target.order - 1
                    return AssignmentTargets.objects.get(
                        assignment=self, order=new_order
                    )
            except (TargetObject.DoesNotExist, AssignmentTargets.DoesNotExist):
                return None
        return None

    def object_after(self, id):
        if len(self.assignment_objects.all()) > 1:
            try:
                obj = TargetObject.objects.get(pk=id)
                assignment_target = AssignmentTargets.objects.get(
                    assignment=self, target_object=obj
                )
                if assignment_target.order == len(
                    self.assignment_objects.all()
                ):  # noqa
                    return None
                else:
                    new_order = assignment_target.order + 1
                    return AssignmentTargets.objects.get(
                        assignment=self, order=new_order
                    )
            except (TargetObject.DoesNotExist, AssignmentTargets.DoesNotExist):
                return None
        return None

    def array_of_tags(self):
        def getColorValues(color):
            values = ""
            if "#" in color:
                # hex
                new_color = color[1:]
                if len(new_color) == 3:
                    values = (
                        "rgba("
                        + str(int(new_color[0] + new_color[0], 16))
                        + ","
                        + str(int(new_color[1] + new_color[1], 16))
                        + ","
                        + str(int(new_color[2] + new_color[2], 16))
                        + ",0.3)"
                    )
                else:
                    values = (
                        "rgba("
                        + str(int(new_color[0] + new_color[1], 16))
                        + ","
                        + str(int(new_color[2] + new_color[3], 16))
                        + ","
                        + str(int(new_color[4] + new_color[5], 16))
                        + ",0.3)"
                    )
            elif "rgb(" in color:
                values = color.replace("rgb(", "rgba(").replace(")", ",0.3)")
            elif "rgba(" in color:
                values = color
            else:
                stdCol = {
                    "acqua": "#0ff",
                    "teal": "#008080",
                    "blue": "#00f",
                    "navy": "#000080",
                    "yellow": "#ff0",
                    "olive": "#808000",
                    "lime": "#0f0",
                    "green": "#008000",
                    "fuchsia": "#f0f",
                    "purple": "#800080",
                    "red": "#f00",
                    "maroon": "#800000",
                    "white": "#fff",
                    "gray": "#808080",
                    "silver": "#c0c0c0",
                    "black": "#000",
                }
                if color in stdCol:
                    values = getColorValues(stdCol[color])
            return values

        if len(self.highlights_options) == 0:
            return []
        else:
            collection = self.highlights_options.split(",")
            result = []
            concat_tag_name = ""
            for col in collection:
                res = col.split(":")
                if len(res) % 2 == 1:
                    res = col.split(";")
                try:
                    result.append((concat_tag_name + res[0], getColorValues(res[1])))
                    concat_tag_name = ""
                except Exception:
                    concat_tag_name += res[0] + " "
            return result

    def get_target_objects(self):
        return self.assignment_objects.all()
