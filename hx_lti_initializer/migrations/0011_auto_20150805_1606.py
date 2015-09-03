# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hx_lti_initializer', '0010_lticourse_course_users'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lticourse',
            name='course_users',
            field=models.ManyToManyField(related_name='course_user_profiles', to='hx_lti_initializer.LTIProfile', blank=True),
            preserve_default=True,
        ),
    ]
