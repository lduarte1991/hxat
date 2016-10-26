# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hx_lti_initializer', '0016_auto_20160401_2054'),
    ]

    operations = [
        migrations.CreateModel(
            name='LTIResourceLinkConfig',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('resource_link_id', models.CharField(max_length=255)),
                ('object_id', models.CharField(max_length=255)),
                ('collection_id', models.CharField(max_length=255)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
