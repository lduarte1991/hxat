# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('target_object_database', '0003_auto_20150702_1614'),
        ('hx_lti_initializer', '0005_auto_20150610_1612'),
    ]

    operations = [
        migrations.CreateModel(
            name='Assignment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('assignment_id', models.CharField(default=uuid.uuid4, unique=True, max_length=100, blank=True)),
                ('assignment_name', models.CharField(default=b'No Assignment Name Given', max_length=255)),
                ('annotation_database_url', models.CharField(max_length=255)),
                ('annotation_database_apikey', models.CharField(max_length=255)),
                ('annotation_database_secret_token', models.CharField(max_length=255)),
                ('include_instructor_tab', models.BooleanField(default=False, help_text=b'Include a tab for instructor annotations.')),
                ('allow_highlights', models.BooleanField(default=False, help_text=b'Allow predetermined tags with colors.')),
                ('highlights_options', models.CharField(max_length=255, blank=True)),
                ('allow_touch', models.BooleanField(default=False, help_text=b'Allow touch devices to use tool (warning, still experimental).')),
                ('pagination_limit', models.IntegerField(help_text=b"How many annotations should show up when you hit the 'More' button?")),
                ('allow_flags', models.BooleanField(default=False, help_text=b'Allow users to flag items as inappropriate/offensive.')),
                ('default_tab', models.CharField(default=b'Public', max_length=20, choices=[(b'Instructor', b'Instructor'), (b'MyNotes', b'My Notes'), (b'Public', b'Public')])),
                ('hidden', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AssignmentTargets',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField(max_length=255, verbose_name=b'Order')),
                ('assignment', models.ForeignKey(verbose_name=b'Assignment', to='hx_lti_assignment.Assignment')),
                ('target_object', models.ForeignKey(verbose_name=b'Source Material', to='target_object_database.TargetObject')),
            ],
            options={
                'ordering': ['order'],
                'verbose_name': 'Assignment Target',
                'verbose_name_plural': 'Assignment Targets',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='assignment',
            name='assignment_objects',
            field=models.ManyToManyField(to='target_object_database.TargetObject', through='hx_lti_assignment.AssignmentTargets'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assignment',
            name='course',
            field=models.ForeignKey(to='hx_lti_initializer.LTICourse'),
            preserve_default=True,
        ),
    ]
