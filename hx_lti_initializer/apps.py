"""
apps.py
by Luis Duarte, HarvardX

This file purely exists to give the app the name "Courses and Instructors"
in the admin panel instead of "hx_lti_initializer".
"""

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class InitializerConfig(AppConfig):
    name = "hx_lti_initializer"
    verbose_name = _("Courses and Instructors")
