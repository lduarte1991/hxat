"""
Django database set up for the tool.

This file creates the LTIProfile class model within the MySQL database for Django. It sets up the attributes for the model and any functions related to saving/retrieving data from the database.
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

    # uses the Django default user to store email and user id information
    user = models.OneToOneField(User, related_name='annotations_user_profile', null=True)
    # saves the list of roles attached to that user
    roles = models.CharField(max_length=255, blank=True, null=True,  verbose_name=_("Roles"))
    # saves the anonymous id for research purposes
    anon_id = models.CharField(max_length=255, blank=True, null=True)

    @models.permalink
    def get_absolute_url(self):
        """ Returns the username as a source of the view profile url """
        return ('view_profile', None, {'username': self.user.username})
    
    def __unicode__(self):
        """ When asked to print itself, this object will print the username """
        return self.user.username

    class Meta:
         """ The name of this section within the admin site """
         verbose_name = _("User Profile")

def user_post_save(sender, instance, created, **kwargs):
    """ 
    This function will create an LTIProfile object.
    Then save the user object to it so that they are interconnected.
    """
    
    if created == True:
        p = LTIProfile()
        p.user = instance
        p.save()

# this function will then connect the function created above so that a matching LTIProfile object is created after any User object is created.
post_save.connect(user_post_save, sender=User)

class LTICourse(models.Model):
    course_id = models.CharField(max_length=255, default='No Course ID')
    course_name = models.CharField(max_length=255, default='No Default Name')
    course_admins = models.ManyToManyField(LTIProfile,  related_name='course_admin_user_profiles')
    course_users = models.ManyToManyField(LTIProfile, related_name='course_student_user_profiles')
    class Meta:
        verbose_name = "Course"
    pass