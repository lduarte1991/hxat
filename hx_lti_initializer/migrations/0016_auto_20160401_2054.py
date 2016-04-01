# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hx_lti_initializer', '0015_ltiprofile_scope'),
    ]

    operations = [
        migrations.CreateModel(
            name='LTICourseAdmin',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('admin_unique_identifier', models.CharField(max_length=255)),
                ('new_admin_course_id', models.CharField(max_length=255)),
            ],
            options={
                'verbose_name': 'Pending Admin',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='lticourseadmin',
            unique_together=set([('admin_unique_identifier', 'new_admin_course_id')]),
        ),
    ]
