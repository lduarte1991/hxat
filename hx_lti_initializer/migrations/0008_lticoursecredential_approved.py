from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hx_lti_initializer', '0007_lticoursecredential'),
    ]

    operations = [
        migrations.AddField(
            model_name='lticoursecredential',
            name='approved',
            field=models.BooleanField(default=False),
        ),
    ]
