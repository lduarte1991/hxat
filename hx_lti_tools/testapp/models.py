from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.utils.translation import ugettext_lazy as _

class LTIProfile(models.Model):
    """
    User profile model. This profile can be retrieved by calling
    get_profile() on the User model
    """

    user = models.OneToOneField(User, null=True)
    roles = models.CharField(max_length=255, blank=True, null=True,  verbose_name=_("Roles"))

    @models.permalink
    def get_absolute_url(self):
        return ('view_profile', None, {'suername': self.user.username})
    
    def __unicode__(self):
        return self.user.username

    class Meta:
         verbose_name = _("User Profile")

def user_post_save(sender, instance, created, **kwargs):
    if created == True:
        p = LTIProfile()
        p.user = instance
        p.save()

post_save.connect(user_post_save, sender=User)
