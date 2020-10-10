from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Category(models.Model):
    name = models.TextField()
    name_en = models.TextField()
    desc = models.TextField(default="", blank=True)
    coverimg = models.TextField(default="banner-1.png")
    title_white = models.IntegerField(default=0)
    hidden = models.IntegerField(default=0)
    extra = models.TextField(default="", blank=True)   # 第一位1表示显示用户检索；第二位1表示非会员可访问；第三位1表示开放评论。

    def __str__(self):
        return self.name

class UsersModel(models.Model):
    username = models.TextField()
    password = models.TextField()
    trial_date = models.DateTimeField(blank=True, null=True)
    vip = models.IntegerField(default=0)
    extra = models.TextField(blank=True, null=True)

class ArticleModel(models.Model):
    title = models.TextField()
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    excerpt = models.TextField(default="", blank=True)
    create_date = models.DateTimeField(auto_now_add=True, db_index=True)
    edit_date = models.DateTimeField(auto_now=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, blank=True, null=True)
    cover_img = models.CharField(max_length=64)
    # Mcover_img_thumb = models.CharField(max_length=64, default="")
    type = models.IntegerField(default=1) # 1为正常文章，2为待审核，3为已删除
    comment_type = models.IntegerField(default=0) # 0为任何人可评论，1为关闭评论区（不显示）
    comment = models.ManyToManyField(User, through="ArticleCommentModel", related_name="article_comment_set")
    extra = models.TextField(default="", blank=True)
    file = models.TextField(default="", blank=True)

    def __str__(self):
        return '【' + (self.title if len(self.title)<=20 else (self.title[:21]+'...')) + '】 ' + self.content[:min(len(self.content),30)]

class ArticleCommentModel(models.Model):
    article = models.ForeignKey(ArticleModel, on_delete=models.CASCADE, related_name="comment_article_set")
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    create_date = models.DateTimeField(auto_now_add=True)
    content = models.TextField()

class PA40CommentModel(models.Model):
    username = models.TextField()
    content = models.TextField()
    extra = models.TextField(blank=True, null=True)

class ArticleVisitModel(models.Model):
    article_id = models.IntegerField()
    visit_count = models.IntegerField()

class SettingsModel(models.Model):
    key = models.TextField()
    sValue = models.TextField(blank=True, null=True)
    sValue2 = models.TextField(blank=True, null=True)
    iValue = models.IntegerField(blank=True, null=True)