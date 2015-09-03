# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hx_lti_initializer', '0004_remove_lticourse_course_users'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='ltiprofile',
            options={'verbose_name': 'Instructor/Administrator'},
        ),
    ]
