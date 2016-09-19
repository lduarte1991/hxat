# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hx_lti_assignment', '0008_auto_20160503_1721'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='assignment',
            options={'ordering': ['id']},
        ),
        migrations.AddField(
            model_name='assignment',
            name='is_published',
            field=models.BooleanField(default=True, help_text=b'Published assignments are available to students while unpublished are not.'),
            preserve_default=True,
        ),
    ]
