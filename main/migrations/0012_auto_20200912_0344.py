# Generated by Django 3.1 on 2020-09-12 03:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0011_category_name_en'),
    ]

    operations = [
        migrations.AddField(
            model_name='usersmodel',
            name='trial_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='usersmodel',
            name='vip',
            field=models.IntegerField(default=0),
        ),
    ]