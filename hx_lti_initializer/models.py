"""
Django database set up for the tool.

This file creates the LTIProfile class model within the MySQL database for
Django. It sets up the attributes for the model and any functions related to
saving/retrieving data from the database.
"""

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.utils.translation import ugettext_lazy as _


class LTIProfile(models.Model):
    """
    This profile stores information for the user.
    It will contain the role information as well as any identifying data,
    including anonymous_ids or platform/consumer-specific ids.
    """

    # uses the Django default user to store username and user id information
    user = models.OneToOneField(
        User,
        related_name='annotations_user_profile',
        null=True,
    )
    # saves the list of roles attached to that user
    roles = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("Roles"),
    )

    # saves the anonymous id for research purposes
    anon_id = models.CharField(
        max_length=255, blank=True, null=True
    )

    def __unicode__(self):
        """ When asked to print itself, this object will print the username """
        return self.user.username
    
    def get_id(self):
        """Returns Canvas user_id of LTIProfile"""
        anon_id = self.anon_id
    
        # The user_id is the part of the anon_id after the colon
        user_id = anon_id.rpartition(':')[2]
    
        return anon_id

    class Meta:
        """ The name of this section within the admin site """
        verbose_name = _("Instructor/Administrator")


def user_post_save(sender, instance, created, **kwargs):
    """
    This function will create an LTIProfile object.
    Then save the user object to it so that they are interconnected.
    """

    if created is True:
        p = LTIProfile()
        p.user = instance
        p.save()

# this function will then connect the function created above so that a
# matching LTIProfile object is created after any User object is created.
post_save.connect(user_post_save, sender=User)


class LTICourse(models.Model):
    """
    This model will store information about a given "Course" passed in.
    In other words, whatever is within the context_id of the LTI request will be
    considered a course and will hold assignments and target objects to annotate.
    """

    # this id will come from the context_id value in the LTI
    course_id = models.CharField(
        max_length=255,
        default=_('No Course ID'),
    )

    # this is used for usability purposes only, course_id is the unique value
    course_name = models.CharField(
        max_length=255,
        default=_('No Default Name'),
    )

    # admins are able to add other users with LTIProfiles already in the system
    course_admins = models.ManyToManyField(
        LTIProfile,
        related_name='course_admin_user_profiles',
    )

    course_external_css_default = models.CharField(
        max_length=255,
        blank=True,
        help_text='(Optional) Please only input a URL to an externally hosted CSS file.',
    )

    class Meta:
        verbose_name = _("Course")

    def __unicode__(self):
        """ When asked to print itself, this object will print the name of the course """
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
        courses_for_user = list(LTICourse.objects.filter(course_admins=user_requested.id))
        return courses_for_user

    @staticmethod
    def get_course_by_id(course_id):
        """
        Should return the LTICourse with the given course_id
        """
        return LTICourse.objects.get(course_id=course_id)

    @staticmethod
    def create_course(course_id, lti_profile):
        """
        Given a course_id and a profile, it creates a new LTICourse object
        and adds the LTIProfile as a course_admin.
        """
        course_object = LTICourse(course_id=course_id)
        course_object.save()
        course_object.course_admins.add(lti_profile)
        return course_object
