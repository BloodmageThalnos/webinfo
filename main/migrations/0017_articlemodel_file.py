# Generated by Django 3.1 on 2020-10-09 04:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0016_pa40commentmodel_username'),
    ]

    operations = [
        migrations.AddField(
            model_name='articlemodel',
            name='file',
            field=models.TextField(blank=True, default=''),
        ),
    ]
