# Generated by Django 3.1 on 2020-09-15 13:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0014_settingsmodel_svalue2'),
    ]

    operations = [
        migrations.CreateModel(
            name='PA40CommentModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
                ('extra', models.TextField(blank=True, null=True)),
            ],
        ),
    ]