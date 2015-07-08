# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hx_lti_assignment', '0004_assignment_assingment_name'),
    ]

    operations = [
        migrations.RenameField(
            model_name='assignment',
            old_name='assingment_name',
            new_name='assignment_name',
        ),
    ]
