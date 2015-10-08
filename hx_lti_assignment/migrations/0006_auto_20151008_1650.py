# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hx_lti_assignment', '0005_auto_20150906_0513'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assignment',
            name='allow_touch',
            field=models.BooleanField(default=False, help_text=b'Allow touch devices to use tool (warning, experimental).'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='assignmenttargets',
            name='target_external_css',
            field=models.CharField(help_text=b'Only input a URL to an externally hosted CSS file.', max_length=255, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='assignmenttargets',
            name='target_instructions',
            field=models.TextField(help_text=b'Add instructions for this object in this assignment.', null=True, blank=True),
            preserve_default=True,
        ),
    ]
