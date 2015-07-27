# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hx_lti_assignment', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assignmenttargets',
            name='target_object',
            field=models.ForeignKey(verbose_name=b'Source Material', to='target_object_database.TargetObject', unique=True),
            preserve_default=True,
        ),
    ]
