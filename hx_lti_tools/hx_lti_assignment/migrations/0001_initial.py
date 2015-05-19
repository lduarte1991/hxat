# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('target_object_database', '0002_auto_20150519_1734'),
        ('hx_lti_initializer', '0003_lticourse'),
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
                ('highlights_options', models.CharField(max_length=255)),
                ('allow_touch', models.BooleanField(default=False, help_text=b'Allow touch devices to use tool (warning, still experimental).')),
                ('pagination_limit', models.IntegerField(help_text=b"How many annotations should show up when you hit the 'More' button?")),
                ('allow_flags', models.BooleanField(default=False, help_text=b'Allow users to flag items as inappropriate/offensive.')),
                ('default_tab', models.CharField(default=b'Public', max_length=20, choices=[(b'Instructor', b'Instructor'), (b'MyNotes', b'My Notes'), (b'Public', b'Public')])),
                ('hidden', models.BooleanField(default=False)),
                ('assignment_objects', models.ManyToManyField(to='target_object_database.TargetObject')),
                ('course', models.ForeignKey(to='hx_lti_initializer.LTICourse')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
