# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hx_lti_initializer', '0003_lticourse'),
    ]

    operations = [
        migrations.CreateModel(
            name='TargetObject',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('target_title', models.CharField(max_length=255)),
                ('target_author', models.CharField(max_length=255)),
                ('target_content', models.TextField()),
                ('target_citation', models.TextField()),
                ('target_created', models.DateTimeField(auto_now_add=True)),
                ('target_updated', models.DateTimeField(auto_now=True)),
                ('target_type', models.CharField(default=b'tx', max_length=2, choices=[(b'tx', b'Text Annotation'), (b'vd', b'Video Annotation'), (b'ig', b'Image Annotation')])),
                ('target_courses', models.ManyToManyField(to='hx_lti_initializer.LTICourse')),
                ('target_creator', models.ForeignKey(to='hx_lti_initializer.LTIProfile')),
            ],
            options={
                'verbose_name': 'Source',
            },
            bases=(models.Model,),
        ),
    ]
