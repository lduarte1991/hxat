# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('target_object_database', '0003_auto_20150702_1614'),
    ]

    operations = [
        migrations.AlterField(
            model_name='targetobject',
            name='target_citation',
            field=models.TextField(blank=True),
            preserve_default=True,
        ),
    ]
