"""
Django database set up for the tool.

This file creates the LTIProfile class model within the MySQL database for
Django. It sets up the attributes for the model and any functions related to
saving/retrieving data from the database.
"""

from django.contrib.auth.models import User
from django.db import models
from django.db.models.functions import Lower
from django.db.models.signals import post_save
from django.utils.translation import gettext_lazy as _
# Update depreciated ugettext_lazy to gettext_lazy https://docs.djangoproject.com/en/3.0/releases/3.0/#id3

class LTIProfile(models.Model):
    """
    This profile stores information for the user.
    It will contain the role information as well as any identifying data,
    including anonymous_ids or platform/consumer-specific ids.
    """

    # uses the Django default user to store username and user id information
    # Many profiles can be associated with a single user object.
    user = models.ForeignKey(
        User,
        related_name="annotations_user_profile",
        null=True,
        on_delete=models.CASCADE,
    )

    # saves the list of roles attached to that user
    roles = models.CharField(
        max_length=255, blank=True, null=True, verbose_name=_("Roles"),
    )

    # saves the anonymous id for research purposes
    anon_id = models.CharField(max_length=255, blank=True, null=True)

    # saves the name for display purposes
    name = models.CharField(max_length=255, blank=True, null=True)

    # saves the scope where this profile is valid (i.e. domain instance for canvas, course instance for edx)
    scope = models.CharField(max_length=1024, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        """ When asked to print itself, this object will print the username """
        return self.name or self.user.username
    
    def __str__(self):
        return "%s (%s)" % (self.name or self.user.username, self.anon_id)


    class Meta:
        """ The name of this section within the admin site """

        verbose_name = _("Instructor/Administrator")
        unique_together = ["anon_id", "scope"]

    def get_id(self):
        """Returns Canvas user_id of LTIProfile"""
        anon_id = self.anon_id
        return anon_id


class LTICourse(models.Model):
    """
    This model will store information about a given "Course" passed in.
    In other words, whatever is within the context_id of the request will be
    considered a course and hold assignments and target objects to annotate.
    """

    # this id will come from the context_id value in the LTI
    course_id = models.CharField(max_length=255, default=_("No Course ID"),)

    # this is used for usability purposes only, course_id is the unique value
    course_name = models.CharField(max_length=255, default=_("No Default Name"),)

    # admins are able to add other users with LTIProfiles already in the system
    course_admins = models.ManyToManyField(
        LTIProfile, related_name="course_admin_user_profiles", blank=True,
    )

    course_users = models.ManyToManyField(
        LTIProfile, related_name="course_user_profiles", blank=True,
    )

    course_external_css_default = models.CharField(
        max_length=255,
        blank=True,
        help_text="Please only add a URL to an externally hosted file.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Course")
        ordering = ['course_name', 'course_id']

    def __unicode__(self):
        """
        When asked to print itself, this object will print the name
        of the course.
        """
        return "%s" % self.course_name

    def __str__(self):
        return self.course_name

    @staticmethod
    def get_all_courses():
        """
        Should return a QuerySet of all LTICourse items, regardless of user.
        """
        return list(LTICourse.objects.all())

    @staticmethod
    def get_courses_of_admin(user_requested):
        """
        Given an administrator, it will return all LTICourse objects
        in which that user appears within the course_admins attribute.
        """
        courses_for_user = list(
            LTICourse.objects.filter(course_admins=user_requested.id)
        )
        return courses_for_user

    @staticmethod
    def get_course_by_id(course_id):
        """
        Should return the LTICourse with the given course_id
        """
        return LTICourse.objects.get(course_id=course_id)

    @staticmethod
    def create_course(course_id, lti_profile, **kwargs):
        """
        Given a course_id and a profile, it creates a new LTICourse object
        and adds the LTIProfile as a course_admin.
        """
        course_object = LTICourse(course_id=course_id)
        course_name = kwargs.get("name", None)
        if course_name:
            course_object.course_name = course_name
        course_object.save()
        course_object.add_admin(lti_profile)
        return course_object

    def add_admin(self, lti_profile):
        """
        Given an lti_profile, adds a user to the course_admins of an LTICourse if not already there
        """
        current_profiles = self.course_admins.all()
        if lti_profile and lti_profile not in current_profiles:
            self.course_admins.add(lti_profile)
            self.save()
        return self

    def add_user(self, lti_profile):
        """
        Given an lti_profile, adds a user to the course_users of an LTICourse if not already there
        """
        current_profiles = self.course_users.all()
        if lti_profile and lti_profile not in current_profiles:
            self.course_users.add(lti_profile)
            self.save()
        return self

    def get_assignments(self):
        """
        Returns a QuerySet of all assignments (published and unpublished) for this course, ordered by name.
        """
        return self.assignments.order_by(Lower("assignment_name"))

    def get_published_assignments(self):
        """
        Returns a QuerySet of published assignments for this course.
        """
        return self.get_assignments().filter(is_published=True)


class LTICourseAdmin(models.Model):

    admin_unique_identifier = models.CharField(max_length=255)

    new_admin_course_id = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Pending Admin")
        unique_together = ("admin_unique_identifier", "new_admin_course_id")

    def __unicode__(self):
        """
        """
        return "%s for course %s" % (
            self.admin_unique_identifier,
            self.new_admin_course_id,
        )

    def __str__(self):
        """
        """
        return "%s for course %s" % (
            self.admin_unique_identifier,
            self.new_admin_course_id,
        )


class LTIResourceLinkConfig(models.Model):
    resource_link_id = models.CharField(
        max_length=255, unique=True, blank=False, null=False
    )
    assignment_target = models.ForeignKey(
        "hx_lti_assignment.AssignmentTargets", null=False, on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
