import logging
import json
from django.shortcuts import render
from django.http import HttpResponse, Http404, JsonResponse
from django.template import loader

from main.models import ArticleModel, Category

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

    can_edit = canEditArticle(article.author, request.user)
    has_fujian = False

    template = loader.get_template('showArticle.html')
    context = {
        'author': article.author.username,
        'title': article.title,
        'excerpt': article.excerpt,
        'category': article.category.name,
        'content': article.content,
        'date': date_str,
        'cats': cats,
        'cat_id': article.category.id,
        'a_id': article.id,
        'username': request.user.username,
        'can_edit': can_edit,
        'has_fujian': has_fujian,
        'has_comment': has_comment
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
    except:
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
                if keyword not in article.content:
                    has = False
            if not has:
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
        'articles': articles,
        'keyword': search_keyword,
        'username': request.user.username,
    }
    return HttpResponse(template.render(context, request))

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
    