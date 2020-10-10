from django.contrib import admin
from .models import ArticleModel, Category, SettingsModel, UsersModel, ArticleVisitModel, PA40CommentModel

# Register your models here.
@admin.register(ArticleModel)
class ArticleModel(admin.ModelAdmin):
    list_display=('id', 'author', 'category', 'title', 'content', 'excerpt', 'type', 'comment_type', 'extra')
    list_editable=('title', 'content', 'excerpt', 'type', 'comment_type', 'extra')

@admin.register(Category)
class CategoryModel(admin.ModelAdmin):
    list_display=('id', 'name', 'desc', 'extra', 'coverimg')
    list_editable=('desc', 'extra', 'coverimg')

@admin.register(SettingsModel)
class SettingsModelAdmin(admin.ModelAdmin):
    list_display=('id', 'key','iValue','sValue', 'sValue2')
    list_editable=('key','iValue','sValue', 'sValue2')

@admin.register(UsersModel)
class UsersModelAdmin(admin.ModelAdmin):
    list_display=('id', 'username', 'password', 'vip', 'trial_date', 'extra')
    list_editable=('username', 'password', 'vip', 'trial_date', 'extra')

@admin.register(ArticleVisitModel)
class ArticleVisitModelAdmin(admin.ModelAdmin):
    list_display=('article_id', 'visit_count')
    list_editable=('visit_count', )

@admin.register(PA40CommentModel)
class PA40CommentModelAdmin(admin.ModelAdmin):
    list_display=('id', 'username', 'content')
    list_editable=('username', 'content')