# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hx_lti_assignment', '0006_auto_20151008_1650'),
    ]

    operations = [
        migrations.AddField(
            model_name='assignment',
            name='include_mynotes_tab',
            field=models.BooleanField(default=True, help_text=b"Include a tab for user's annotations. Warning: Turning this off will not allow students to make annotations."),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assignment',
            name='include_public_tab',
            field=models.BooleanField(default=True, help_text=b"Include a tab for public annotations. Used for private annotations. If you want users to view each other's annotations."),
            preserve_default=True,
        ),
    ]
