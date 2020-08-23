import logging
import json
import datetime
import time
import pytz
from django.shortcuts import render
from django.http import HttpResponse, Http404, JsonResponse, HttpResponseRedirect
from django.template import loader
from django.contrib.auth.models import User

from main.models import ArticleModel, Category, ArticleVisitModel

logger = logging.getLogger(__name__)
def showArticlePage(request, id_):
    logger.info(f'Accessed {request.get_full_path()} with showArticlePage')

    try:
        articleId = int(id_)
        article = ArticleModel.objects.get(id=articleId)
    except:
        raise Http404('文章不存在。')
    if article.type != 1:
        raise Http404('文章已被删除或还未发表。')

    if not canReadArticle(request.user, article):
        template = loader.get_template('showArticle.html')
        context = {
            'no_access': True,
        }
        return HttpResponse(template.render(context, request))


    visit = ArticleVisitModel.objects.filter(article_id=articleId)
    if len(visit)==0:
        visit = ArticleVisitModel(article_id=articleId, visit_count = 1)
        visit.save()
    else:
        visit[0].visit_count += 1
        visit[0].save()

    categories = Category.objects.all()
    cats = []
    for _ in categories:
        cats.append({
            'id': _.id,
            'name': _.name
        })
    cats = cats[::-1]

    date_str = article.edit_date.strftime("%Y-%b-%d")

    has_comment = article.comment_type==0
    if has_comment:
        pass

    hotest_articles = getHotestArticles()
    newest_articles = getNewestArticles()

    category = article.category
    showuser = (category.extra[0]=='1')
    canread = (category.extra[1]=='1')
    if showuser:
        forum_id = category.id
        author_ids = getAuthorList(forum_id)
        author_list = []
        for i in author_ids:
            author = User.objects.get(id=i)
            author_list.append({
                'name': author.username,
                'url': '/list-article?fid='+str(forum_id)+'&aid='+str(author.id),
            })
    else:
        author_list = None

    can_edit = canEditArticle(article.author, request.user)
    has_fujian = False

    template = loader.get_template('showArticle.html')
    context = {
        'author': article.author.username,
        'title': article.title,
        'excerpt': article.excerpt,
        'category': article.category.name,
        'cat_img': '/s/'+article.category.coverimg,
        'cat_name_white': bool(article.category.title_white),
        'content': article.content,
        'cover_img': article.cover_img,
        'date': date_str,
        'cats': cats,
        'cat_id': article.category.id,
        'a_id': article.id,
        'username': request.user.username,
        'can_edit': can_edit,
        'has_fujian': has_fujian,
        'has_comment': has_comment,
        'hotest_articles': hotest_articles,
        'newest_articles': newest_articles,
        'show_user': showuser,
        'author_list': author_list,
    }
    return HttpResponse(template.render(context, request))

def showWriteArticlePage(request):
    logger.info(f'Accessed {request.get_full_path()} with showWriteArticlePage')

    user_id = request.user.id
    forum_id = int(request.GET.get('fid'))
    if not canWriteArticle(user_id, forum_id):
        raise Http404('你没有权限在该板块发表文章。')
    
    template = loader.get_template('postArticle.html')
    context = {
        'cat_id': forum_id,
    }
    return HttpResponse(template.render(context, request))

def showEditArticlePage(request):
    logger.info(f'Accessed {request.get_full_path()} with showEditArticlePage')

    user_id = request.user.id
    forum_id = int(request.GET.get('fid'))
    article_id = int(request.GET.get('aid'))
    if not canWriteArticle(user_id, forum_id):
        raise Http404('你没有权限在该板块发表文章。')
    
    article = ArticleModel.objects.get(id=article_id)
    if not canEditArticle(article.author, request.user):
        raise Http404('你没有权限编辑该文章。')
    
    template = loader.get_template('postArticle.html')
    context = {
        'cat_id': forum_id,
        'article_id': article_id,
        'text': article.content,
        'title': article.title,
        'cimg': article.cover_img,
    }
    return HttpResponse(template.render(context, request))


def showArticleList(request):
    logger.info(f'Accessed {request.get_full_path()} with showArticlePage')

    try:
        forum_id = int(request.GET.get('fid'))
        user_id = request.user.id
        page_no = int(request.GET.get('page', '1'))
        search_keyword = request.GET.get('keyword', '')
        author_id = int(request.GET.get('aid', 0))

        day = request.POST.get('day', '')
        if day:
            month_start = datetime.datetime.fromisoformat(day)
            month_end = month_start + datetime.timedelta(days=1)
            time_str = str(month_start.year)+'年'+str(month_start.month)+'月'+str(month_start.day)+'日'
        else:
            month = request.POST.get('month', '')
            if month:
                month_start =datetime.datetime.fromisoformat(month+'-01')
                month_end = datetime.datetime(month_start.year + (month_start.month==12), month_start.month%12+1, 1, 0, 0, 0)
                time_str = str(month_start.year)+'年'+str(month_start.month)+'月'
            else:
                month_start = None
                time_str = None
        if author_id:
            author_name = User.objects.get(id=author_id).username
        else:
            author_name = None
    except Exception as e:
        logger.error(str(e))
        raise Http404('缺少参数或格式错误。')

    import re
    pattern = re.compile(r'<.*?>')
    search_keywords = search_keyword.split()

    category = Category.objects.get(id=forum_id)
    articleModel = ArticleModel.objects.filter(category=category)
    articles = []
    for article in articleModel[::-1]:
        if search_keywords:
            has = True
            for keyword in search_keywords:
                if keyword not in article.title and keyword not in article.content:
                    has = False
                    break
            if not has:
                continue
        elif author_id:
            if article.author.id != author_id:
                continue
        elif month_start:
            logger.info(article.create_date)
            logger.info(month_start)
            logger.info(month_end)
            if article.create_date.replace(tzinfo=None) < month_start or article.create_date.replace(tzinfo=None) > month_end:
                continue

        articles.append({
            'title': article.title,
            'excerpt': pattern.sub('', article.content)[:160]+"...",
            'author': article.author.username,
            'date_day': article.edit_date.day,
            'date_month': ["","JAN","FEB","MAR","APR","MAY","JUL","JUN","AUG","SEPT","OCT","NOV","DEC"][article.edit_date.month],
            'url': '/article-'+str(article.id),
        })
    # print(articles)
    # date_str = article.edit_date.strftime("%Y-%b-%d")

    hotest_articles = getHotestArticles()
    newest_articles = getNewestArticles()

    showuser = (category.extra[0]=='1')
    canread = (category.extra[1]=='1')
    if showuser:
        author_ids = getAuthorList(forum_id)
        author_list = []
        for i in author_ids:
            author = User.objects.get(id=i)
            author_list.append({
                'name': author.username,
                'url': '/list-article?fid='+str(forum_id)+'&aid='+str(author.id),
            })
    else:
        author_list = None

    categories = Category.objects.all()
    cats = []
    for _ in categories:
        cats.append({
            'id': _.id,
            'name': _.name
        })
    cats = cats[::-1]

    template = loader.get_template('listArticle.html')
    context = {
        'cats': cats,
        'cat_id': forum_id,
        'cat_name': category.name,
        'cat_img': '/s/'+category.coverimg,
        'cat_name_white': bool(category.title_white),
        'cat_desc': category.desc.replace('\n', '<br/>'),
        'articles': articles,
        'keyword': search_keyword,
        'author_name': author_name,
        'username': request.user.username,
        'hotest_articles': hotest_articles,
        'newest_articles': newest_articles,
        'show_user': showuser,
        'author_list': author_list,
        'time_str': time_str,
    }
    return HttpResponse(template.render(context, request))

def canReadArticle(user, article):
    if not user.is_authenticated:
        return False
    return True

def canWriteArticle(user_id, forum_id):
    return True

def canEditArticle(author, user):
    return author.id==user.id or user.is_authenticated

def createArticle(request):
    resp = {'success': 0}
    for _ in range(1):
        author = request.user
        category_id = request.POST.get('c')
        if not category_id:
            break
        try:
            category_id = int(category_id)
            category = Category.objects.get(id=category_id)
        except Exception as e:
            resp["alert"]="文章所在分类已被删除或id错误: "+str(e)
            break
        if not author.is_authenticated or not canWriteArticle(author.id, category_id):
            resp["alert"]="用户权限不足。"
            break
        title = request.POST.get('t')
        if not title:
            resp["alert"]="请输入标题。"
            break
        content = request.POST.get('con')
        if not content:
            resp["alert"]="请输入正文。"
            break
        cover_img = request.POST.get('cimg')
        if not cover_img:
            resp["alert"]="请选择封面图片。"
            break
        type = 1
        comment_type = 1
        article_id = request.POST.get("aid")
        if article_id and len(article_id):
            article_id = int(article_id)
            article = ArticleModel.objects.get(id=article_id)
            article.title = title
            article.content = content
            article.cover_img = cover_img
            article.save()
        else:
            article = ArticleModel(
                title=title,
                content=content,
                cover_img=cover_img,
                author=author,
                type=type,
                comment_type=comment_type,
                category=category,
                extra="")
            article.save()
        resp["success"]=1
        resp["url"]="/article-"+str(article.id)

    return JsonResponse(resp)

def deleteArticle(request):
    logger.info(f'Accessed {request.get_full_path()} with showEditArticlePage')

    user_id = request.user.id
    article_id = int(request.GET.get('aid'))
    article = ArticleModel.objects.get(id=article_id)
    forum_id = article.category.id

    if canEditArticle(article.author, request.user):
        article.delete()
        return HttpResponseRedirect('/list-article?fid='+str(forum_id))

def uploadImg(request):
    import time
    import os
    try:
        pic = request.FILES.get("pic")
        filename = str(int(time.time()*1000)%1000000007) + os.path.splitext(pic.name)[1]
        cimg = '/s/' + filename
        with open('./images/' + filename, "wb") as fPic:
            for chunk in pic.chunks():
                fPic.write(chunk)
    except Exception as e:
        return JsonResponse({'success':'0', 'msg':str(e)})
    return JsonResponse({'success':'1', 'cimg':cimg})
    
hotest_articles = []
last_update = -1
def getHotestArticles():
    global last_update
    global hotest_articles

    import time
    if time.time() - last_update < 60: # 每分钟计算一次，避免重复访问数据库
        return hotest_articles

    last_update = time.time()
    
    hot_visits = ArticleVisitModel.objects.order_by('-visit_count')[:5]
    hotest_articles = []
    for i in hot_visits:
        try:
            article = ArticleModel.objects.get(id=i.article_id)
        except:
            i.delete()
            continue
        hotest_articles.append({
            'title': article.title,
            'url': '/article-'+str(article.id),
        })
    return hotest_articles

def getNewestArticles():
    articles = ArticleModel.objects.all()[::-1]
    newest_articles = []
    for article in articles[:5]:
        newest_articles.append({
            'title': article.title,
            'url': '/article-'+str(article.id),
        })
    return newest_articles

article_author_data = {}
# 1: ([作者id], 时间戳)
def getAuthorList(forum_id):
    global article_author_data
    import time

    data = article_author_data.get(forum_id, {})
    if not data or time.time() - data[1] > 60: # 每60秒更新一次
        s = {}
        articles = ArticleModel.objects.all()
        for article in articles:
            if article.category.id == forum_id:
                aid = article.author.id
                if s.get(aid, 0):
                    s[aid] += 1
                else:
                    s[aid] = 1
        l = [(s[x], x) for x in s.keys()]
        l.sort()
        data = ([x[1] for x in l], time.time())

        article_author_data[forum_id] = data
    return data[0]