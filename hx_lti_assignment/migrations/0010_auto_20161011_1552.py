# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hx_lti_assignment', '0009_auto_20160919_2029'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assignment',
            name='course',
            field=models.ForeignKey(related_name='assignments', to='hx_lti_initializer.LTICourse'),
            preserve_default=True,
        ),
    ]
