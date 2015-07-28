# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hx_lti_initializer', '0006_lticourse_course_external_css_default'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lticourse',
            name='course_external_css_default',
            field=models.CharField(blank=True, help_text=b'Please only input a URL to an externally hosted CSS file.', max_length=255, validators=[b'URLValidator']),
            preserve_default=True,
        ),
    ]
