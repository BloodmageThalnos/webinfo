# Generated by Django 3.1 on 2020-08-30 04:22

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('main', '0009_category_title_white'),
    ]

    operations = [
        migrations.CreateModel(
            name='ArticleCommentModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_date', models.DateTimeField(auto_now_add=True)),
                ('content', models.TextField()),
                ('article', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comment_article_set', to='main.articlemodel')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='articlemodel',
            name='comment',
            field=models.ManyToManyField(related_name='article_comment_set', through='main.ArticleCommentModel', to=settings.AUTH_USER_MODEL),
        ),
    ]