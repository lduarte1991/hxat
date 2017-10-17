# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Annotation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('context_id', models.CharField(max_length=1024, db_index=True)),
                ('collection_id', models.CharField(max_length=1024)),
                ('uri', models.CharField(max_length=2048)),
                ('media', models.CharField(max_length=24)),
                ('user_id', models.CharField(max_length=1024)),
                ('user_name', models.CharField(max_length=1024)),
                ('is_private', models.BooleanField(default=False)),
                ('is_deleted', models.BooleanField(default=False)),
                ('text', models.TextField(default=b'', blank=True)),
                ('quote', models.TextField(default=b'', blank=True)),
                ('json', models.TextField(default=b'{}', blank=True)),
                ('total_comments', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('parent', models.ForeignKey(to='annotation_store.Annotation', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AnnotationTags',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=128)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserStats',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('context_id', models.CharField(max_length=1024, db_index=True)),
                ('collection_id', models.CharField(max_length=1024)),
                ('uri', models.CharField(max_length=2048)),
                ('user_id', models.CharField(max_length=1024)),
                ('user_name', models.CharField(max_length=1024)),
                ('total_annotations', models.PositiveIntegerField(default=0)),
                ('total_comments', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='annotation',
            name='tags',
            field=models.ManyToManyField(related_name='annotations', to='annotation_store.AnnotationTags'),
            preserve_default=True,
        ),
    ]
