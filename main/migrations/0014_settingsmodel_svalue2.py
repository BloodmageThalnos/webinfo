# Generated by Django 3.1 on 2020-09-15 12:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0013_category_hidden'),
    ]

    operations = [
        migrations.AddField(
            model_name='settingsmodel',
            name='sValue2',
            field=models.TextField(blank=True, null=True),
        ),
    ]
