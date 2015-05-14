# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hx_lti_assignment', '0003_auto_20150514_1608'),
    ]

    operations = [
        migrations.AddField(
            model_name='assignment',
            name='assingment_name',
            field=models.CharField(default=b'No Assignment Name Given', max_length=255),
            preserve_default=True,
        ),
    ]
