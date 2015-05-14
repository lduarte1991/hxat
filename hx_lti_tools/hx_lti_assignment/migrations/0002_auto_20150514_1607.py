# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hx_lti_assignment', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assignment',
            name='default_tab',
            field=models.CharField(default=b'Public', max_length=20, choices=[(b'Instructor', b'Instructor'), (b'My Notes', b'MyNotes'), (b'Public', b'Public')]),
            preserve_default=True,
        ),
    ]
