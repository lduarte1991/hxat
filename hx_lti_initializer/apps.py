"""
apps.py
by Luis Duarte, HarvardX

This file purely exists to give the app the name "Courses and Instructors"
in the admin panel instead of "hx_lti_initializer".
"""
# Update depreciated ugettext_lazy to gettext_lazy https://docs.djangoproject.com/en/3.0/releases/3.0/#id3
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class InitializerConfig(AppConfig):
    name = "hx_lti_initializer"
    verbose_name = _("Courses and Instructors")
