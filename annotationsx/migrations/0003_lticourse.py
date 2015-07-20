# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('annotationsx', '0002_ltiprofile_anon_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='LTICourse',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('course_id', models.CharField(default=b'No Course ID', max_length=255)),
                ('course_name', models.CharField(default=b'No Default Name', max_length=255)),
                ('course_admins', models.ManyToManyField(related_name='course_admin_user_profiles', to='annotationsx.LTIProfile')),
                ('course_users', models.ManyToManyField(related_name='course_student_user_profiles', to='annotationsx.LTIProfile')),
            ],
            options={
                'verbose_name': 'Course',
            },
            bases=(models.Model,),
        ),
    ]
