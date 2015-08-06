# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hx_lti_initializer', '0009_auto_20150727_1821'),
    ]

    operations = [
        migrations.AddField(
            model_name='lticourse',
            name='course_users',
            field=models.ManyToManyField(related_name='course_user_profiles', to='hx_lti_initializer.LTIProfile'),
            preserve_default=True,
        ),
    ]
