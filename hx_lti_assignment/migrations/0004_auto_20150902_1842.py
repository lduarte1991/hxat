# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hx_lti_assignment', '0003_auto_20150727_1821'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assignmenttargets',
            name='target_object',
            field=models.ForeignKey(verbose_name=b'Source Material', to='target_object_database.TargetObject'),
            preserve_default=True,
        ),
    ]
