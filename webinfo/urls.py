from django.contrib import admin
from django.urls import path, re_path
from main import views as mainViews
from article import views as articleViews

urlpatterns = [
    path('django$$admin/', admin.site.urls),
    path('static/<path:path>', mainViews.showBin),
    path('s/<path:path>', mainViews.showImages),
    path('', mainViews.showHome),
    path('info', mainViews.showInfo),
    path('login_', mainViews.showLogin),
    path('dologin', mainViews.doLogin),
    path('login_admin', mainViews.showLoginAdmin),
    path('dologin_admin', mainViews.doLoginAdmin),
    path('admin', mainViews.showAdmin),
    path('admin_action', mainViews.doAdminAction),

    # 文章相关
    re_path(r'^article-(?P<id_>[0-9]+)/$', articleViews.showArticlePage),
    path('post-article', articleViews.showWriteArticlePage),
    path('edit-article', articleViews.showEditArticlePage),
    path('action', articleViews.createArticle),
    path('delete-article', articleViews.deleteArticle),
    path('list-article', articleViews.showArticleList),
    path('uploadimg', articleViews.uploadImg),
    

]
