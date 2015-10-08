# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hx_lti_initializer', '0011_auto_20150805_1606'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lticourse',
            name='course_external_css_default',
            field=models.CharField(help_text=b'Please only add a URL to an externally hosted file.', max_length=255, blank=True),
            preserve_default=True,
        ),
    ]
