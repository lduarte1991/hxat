# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('target_object_database', '0002_auto_20150519_1734'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='targetobject',
            options={'ordering': ['target_title'], 'verbose_name': 'Source'},
        ),
    ]
