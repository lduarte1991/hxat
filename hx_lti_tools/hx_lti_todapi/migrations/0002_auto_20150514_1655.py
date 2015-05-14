# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hx_lti_todapi', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='targetobject',
            options={'verbose_name': 'Source Material'},
        ),
    ]
