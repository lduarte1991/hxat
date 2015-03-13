from django.db import models
from django.core.urlresolvers import reverse

# Add admin Url to every content object
def get_admin_url(self):
    return reverse('admin:%s_%s_change' % (self._meta.app_label,  self._meta.module_name),  args=[self.pk])

models.Model.get_admin_url = get_admin_url