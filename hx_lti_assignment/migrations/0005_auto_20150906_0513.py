# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hx_lti_assignment', '0004_auto_20150902_1842'),
    ]

    operations = [
        migrations.AddField(
            model_name='assignmenttargets',
            name='target_external_options',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assignmenttargets',
            name='target_instructions',
            field=models.TextField(help_text=b'Add instructions for this object within this particular assignment.', null=True, blank=True),
            preserve_default=True,
        ),
    ]
