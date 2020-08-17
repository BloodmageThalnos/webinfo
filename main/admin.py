from django.contrib import admin
from .models import ArticleModel, Category, SettingsModel, UsersModel

# Register your models here.
@admin.register(ArticleModel)
class ArticleModel(admin.ModelAdmin):
    list_display=('id', 'author', 'category', 'title', 'content', 'excerpt', 'type', 'comment_type', 'extra')
    list_editable=('title', 'content', 'excerpt', 'type', 'comment_type', 'extra')

@admin.register(Category)
class CategoryModel(admin.ModelAdmin):
    list_display=('id', 'name', 'desc', 'extra')
    list_editable=('desc', 'extra')

@admin.register(SettingsModel)
class SettingsModelAdmin(admin.ModelAdmin):
    list_display=('id', 'key','iValue','sValue')
    list_editable=('key','iValue','sValue')

@admin.register(UsersModel)
class UsersModelAdmin(admin.ModelAdmin):
    list_display=('id', 'username', 'password', 'extra')
    list_editable=('username', 'password', 'extra')