# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hx_lti_assignment', '0002_auto_20150716_2013'),
    ]

    operations = [
        migrations.AddField(
            model_name='assignmenttargets',
            name='target_external_css',
            field=models.CharField(default='', help_text=b'(Optional) Please only input a URL to an externally hosted CSS file.', max_length=255, blank=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='assignmenttargets',
            name='order',
            field=models.IntegerField(verbose_name=b'Order'),
            preserve_default=True,
        ),
    ]
