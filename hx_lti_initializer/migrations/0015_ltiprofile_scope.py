# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hx_lti_initializer', '0014_auto_20160318_1433'),
    ]

    operations = [
        migrations.AddField(
            model_name='ltiprofile',
            name='scope',
            field=models.CharField(max_length=1024, null=True, blank=True),
            preserve_default=True,
        ),
    ]
