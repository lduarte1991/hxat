import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hx_lti_initializer', '0006_alter_ltiprofile_unique_together'),
    ]

    operations = [
        migrations.CreateModel(
            name='LTICourseCredential',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('course', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='credential',
                    to='hx_lti_initializer.lticourse',
                )),
                ('lti_key', models.CharField(max_length=255)),
                ('lti_secret', models.CharField(default=uuid.uuid4, max_length=36)),
                ('allowed_rerun', models.BooleanField(default=False)),
                ('deactivated', models.BooleanField(default=False)),
            ],
        ),
    ]
