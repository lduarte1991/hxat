from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class InitializerConfig(AppConfig):
    name = 'hx_lti_initializer'
    verbose_name = _("Courses and Instructors")