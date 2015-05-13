# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hx_lti_assignment', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assignment',
            name='allow_flags',
            field=models.BooleanField(default=False, help_text=b'Allow users to flag items as inappropriate/offensive.'),
            preserve_default=True,
        ),
    ]
