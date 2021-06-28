from django.contrib import admin
from django.urls import path, re_path
from main import views as mainViews
from article import views as articleViews

urlpatterns = [
    path('', mainViews.showMain),

    path('django$$admin/', admin.site.urls),
    path('static/<path:path>', mainViews.showBin),
    path('s/<path:path>', mainViews.showImages),
    path('favicon.ico', mainViews.showIcon),
    path('home', mainViews.showHome),
    path('info', mainViews.showInfo),
    path('login_', mainViews.showLogin),
    path('logout_', mainViews.doLogout),
    path('dologin', mainViews.doLogin),
    re_path(r'^doreg(?P<action>[0-9]+)/?$', mainViews.doRegister),
    path('cp_', mainViews.showChangePassword),
    path('login_admin', mainViews.showLoginAdmin),
    path('dologin_admin', mainViews.doLoginAdmin),
    path('admin', mainViews.showAdmin),
    path('admin_action', mainViews.doAdminAction),
    path('changeLang', mainViews.changeLanga),
    path('qr-code', mainViews.showQRCode),

    path('pa40', articleViews.pa40Page),

    # 文章相关
    re_path(r'^article-(?P<id_>[0-9]+)/$', articleViews.showArticlePage),
    path('post-article', articleViews.showWriteArticlePage),
    path('edit-article', articleViews.showEditArticlePage),
    path('action', articleViews.createArticle),
    path('delete-article', articleViews.deleteArticle),
    path('list-article', articleViews.showArticleList),
    path('uploadimg', articleViews.uploadImg),
    path('postcomment', articleViews.postComment),
    

]
