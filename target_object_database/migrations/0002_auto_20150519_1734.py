# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('target_object_database', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='targetobject',
            name='target_creator',
            field=models.ForeignKey(to='hx_lti_initializer.LTIProfile', null=True),
            preserve_default=True,
        ),
    ]
