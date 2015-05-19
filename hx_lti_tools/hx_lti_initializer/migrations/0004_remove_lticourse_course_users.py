# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hx_lti_initializer', '0003_lticourse'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='lticourse',
            name='course_users',
        ),
    ]
