import logging
import json
import datetime
import time
import pytz
from django.shortcuts import render
from django.http import HttpResponse, Http404, JsonResponse, HttpResponseRedirect
from django.template import loader
from django.contrib.auth.models import User
from django.core.cache import cache

from main.models import ArticleModel, Category, ArticleVisitModel, ArticleCommentModel, UsersModel, SettingsModel, PA40CommentModel
from main.views import sendAlertToWechat, getGlobalConfig, is_pa40

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
        if not is_pa40(_.id):
            cats.append({
                'id': _.id,
                'name': _.name,
                'name_en': _.name_en,
            })
    cats = cats[::-1]

    date_str = article.edit_date.strftime("%Y-%b-%d")

    has_comment = True
    comments = []
    comment_len = 0
    if has_comment:
        article_comment = article.comment_article_set.all()
        for i in article_comment:
            comments.append({
                'author': i.author.username,
                'content': i.content,
            })
        comment_len = len(comments)

    hotest_articles = getHotestArticles()
    newest_articles = getNewestArticles()

    lang = request.session.get('language', '')
    if not lang:
        request.session['language'] = 'ch'
        lang = 'ch'

    category = article.category
    showuser = (category.extra[0]=='1')
    canread = (category.extra[1]=='1')
    can_comment = (category.extra[2]=='1')
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

    can_edit = canEditArticle(request.user, article)
    filename = article.file
    if filename:
        has_fujian = True
        filename = filename[3:] # 前三个字符为防止重复用的随机数字，跳过
    else:
        has_fujian = False

    template = loader.get_template('showArticle.html')
    context = {
        'aid': article.id,
        'author': article.author.username,
        'title': article.title,
        'excerpt': article.excerpt,
        'category': article.category.name_en if lang=='en' else article.category.name,
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
        'filename': filename,
        'has_comment': has_comment,
        'can_comment': can_comment,
        'comments': comments,
        'comment_len': comment_len,
        'hotest_articles': hotest_articles,
        'newest_articles': newest_articles,
        'show_user': showuser,
        'author_list': author_list,
        'language_en': lang=='en',
    }
    getGlobalConfig(context)
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
    getGlobalConfig(context)
    return HttpResponse(template.render(context, request))

def showEditArticlePage(request):
    logger.info(f'Accessed {request.get_full_path()} with showEditArticlePage')

    user_id = request.user.id
    forum_id = int(request.GET.get('fid'))
    article_id = int(request.GET.get('aid'))
    if not canWriteArticle(user_id, forum_id):
        raise Http404('你没有权限在该板块发表文章。')
    
    article = ArticleModel.objects.get(id=article_id)
    if not canEditArticle(request.user, article):
        raise Http404('你没有权限编辑该文章。')
    
    template = loader.get_template('postArticle.html')
    context = {
        'cat_id': forum_id,
        'article_id': article_id,
        'text': article.content,
        'title': article.title,
        'cimg': article.cover_img,
    }
    getGlobalConfig(context)
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
                monthday = (month+'-01') if '-' in month else (month+'01')
                month_start =datetime.datetime.fromisoformat(monthday)
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

    NUM_PER_PAGE = 2
    page_start = page_no
    

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
        if not is_pa40(_.id):
            cats.append({
                'id': _.id,
                'name': _.name,
                'name_en': _.name_en,
            })
    cats = cats[::-1]
    
    lang = request.session.get('language', '')
    if not lang:
        request.session['language'] = 'ch'
        lang = 'ch'
    

    template = loader.get_template('listArticle.html')
    context = {
        'cats': cats,
        'cat_id': forum_id,
        'cat_name': category.name,
        'cat_name_en': category.name_en,
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
        'language_en': lang=='en',
    }
    getGlobalConfig(context)
    return HttpResponse(template.render(context, request))

def canReadArticle(user, article):
    if user.is_authenticated:
        if user.username == 'root':return True # spj for root
        try:
            userm = UsersModel.objects.get(username=user.username)
        except:
            sendAlertToWechat('发现UsersModel与Users数据库不匹配：id=%d, username=%s'%(user.id, user.username))
            return True
        return userm.vip==1 or (userm.trial_date and userm.trial_date > datetime.datetime.now().replace(tzinfo=pytz.timezone('UTC')))
    
    canread = article.category.extra[1]=='1'
    return canread

def canWriteArticle(user_id, forum_id):
    return True

def canEditArticle(user, article):
    return article.author.id==user.id or user.username=='root'

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
            resp["alert"]="用户权限不足。\n（为防止编辑的文章丢失，请在别的窗口中登录后再试）"
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
        file = request.FILES.get('file')
        if file:
            filename = str(int(time.time()*1000)%900+100) + file.name
            with open('./uploads/' + filename, "wb") as fPic:
                for chunk in file.chunks():
                    fPic.write(chunk)
        else:
            filename = ""
        type = 1
        comment_type = 1
        article_id = request.POST.get("aid")
        if article_id and len(article_id):
            article_id = int(article_id)
            article = ArticleModel.objects.get(id=article_id)
            article.title = title
            article.content = content
            article.cover_img = cover_img
            if filename:
                article.file = filename
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
                file=filename,
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

    if canEditArticle(request.user, article):
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

def postComment(request):
    user = request.user
    if not user.is_authenticated:
        return HttpResponseRedirect('/login')
    content = request.POST.get('content')
    article_id = request.POST.get('aid')
    try:
        article_id = int(article_id)
        article = ArticleModel.objects.get(id=article_id)
    except Exception as e:
        return JsonResponse({'success':'0', 'msg':str(e)})
    if len(content)<2 and content != '6':
        return HttpResponseRedirect('/article-'+str(article_id))
    
    comment = ArticleCommentModel(
        author = user,
        article = article,
        content = content,
    )
    comment.save()
    return HttpResponseRedirect('/article-'+str(article_id))
    
def getHotestArticles():
    hotest_articles = cache.get('hotest-articles')
    if not hotest_articles:
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
        cache.set('hotest-articles', hotest_articles, 60)
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

def getAuthorList(forum_id):
    data = cache.get('article_author_'+str(forum_id), {})
    if not data:
        s = {}
        articles = ArticleModel.objects.all()
        for article in articles:
            if article.type == 1 and article.category.id == forum_id:
                aid = article.author.id
                if s.get(aid, 0):
                    s[aid] += 1
                else:
                    s[aid] = 1
        l = [(s[x], x) for x in s.keys()]
        l.sort()
        data = [x[1] for x in l]

        cache.set('article_author_'+str(forum_id), data, 60)
    return data

def pa40Page(request):
    content = request.POST.get('content', '')
    if content:
        pa40commentModel = PA40CommentModel(username=request.user.username or '游客', content=content)
        pa40commentModel.save()

    try:
        pa40cat = Category.objects.get(id=5)
    except:
        pa40cat = Category(id=5,name='PA40俱乐部',name_en='PA40 Forum',coverimg='cbg-73734.34347963333.jpg')
        pa40cat.save()
    cat_img = pa40cat.coverimg

    categories = Category.objects.all()
    cats = []
    for _ in categories:
        if not is_pa40(_.id):
            cats.append({
                'id': _.id,
                'name': _.name,
                'name_en': _.name_en,
            })
    cats = cats[::-1]
    
    import re
    pattern = re.compile(r'<.*?>')

    show_word_num = 40

    main_article_models = ArticleModel.objects.filter(category=5)
    main_articles = []
    for article in main_article_models[::-1]:
        main_articles.append({
            'title': article.title,
            'excerpt': pattern.sub('', article.content)[:show_word_num]+"...",
            'url': '/article-'+str(article.id),
        })
    main_articles = main_articles[:3]

    main_article_models2 = ArticleModel.objects.filter(category=6)
    main_articles2 = []
    for article in main_article_models2[::-1]:
        main_articles2.append({
            'title': article.title,
            'excerpt': pattern.sub('', article.content)[:show_word_num]+"...",
            'url': '/article-'+str(article.id),
        })
    main_articles2 = main_articles2[:3]
    title2 = Category.objects.get(id=6).name
    title2_en = Category.objects.get(id=6).name_en

    main_article_models3 = ArticleModel.objects.filter(category=7)
    main_articles3 = []
    for article in main_article_models3[::-1]:
        main_articles3.append({
            'title': article.title,
            'excerpt': pattern.sub('', article.content)[:show_word_num]+"...",
            'url': '/article-'+str(article.id),
        })
    main_articles3 = main_articles3[:3]
    title3 = Category.objects.get(id=7).name
    title3_en = Category.objects.get(id=7).name_en
    
    main_article_models4 = ArticleModel.objects.filter(category=8)
    main_articles4 = []
    for article in main_article_models4[::-1]:
        main_articles4.append({
            'title': article.title,
            'excerpt': pattern.sub('', article.content)[:show_word_num]+"...",
            'url': '/article-'+str(article.id),
        })
    main_articles4 = main_articles4[:3]
    title4 = Category.objects.get(id=8).name
    title4_en = Category.objects.get(id=8).name_en

    # 保持三个小组中内容数量相同，少于3条时取min显示
    min_main_article_count = min(len(main_articles2), len(main_articles3), len(main_articles4))
    main_articles2 = main_articles2[:min_main_article_count]
    main_articles3 = main_articles3[:min_main_article_count]
    main_articles4 = main_articles4[:min_main_article_count]

    # 扩展的三个小组
    main_article_models5 = ArticleModel.objects.filter(category=11)
    main_articles5 = []
    for article in main_article_models5[::-1]:
        main_articles5.append({
            'title': article.title,
            'excerpt': pattern.sub('', article.content)[:show_word_num]+"...",
            'url': '/article-'+str(article.id),
        })
    main_articles5 = main_articles5[:3]
    title5 = Category.objects.get(id=11).name
    title5_en = Category.objects.get(id=11).name_en

    main_article_models6 = ArticleModel.objects.filter(category=12)
    main_articles6 = []
    for article in main_article_models6[::-1]:
        main_articles6.append({
            'title': article.title,
            'excerpt': pattern.sub('', article.content)[:show_word_num]+"...",
            'url': '/article-'+str(article.id),
        })
    main_articles6 = main_articles6[:3]
    title6 = Category.objects.get(id=12).name
    title6_en = Category.objects.get(id=12).name_en

    main_article_models7 = ArticleModel.objects.filter(category=13)
    main_articles7 = []
    for article in main_article_models7[::-1]:
        main_articles7.append({
            'title': article.title,
            'excerpt': pattern.sub('', article.content)[:show_word_num]+"...",
            'url': '/article-'+str(article.id),
        })
    main_articles7 = main_articles7[:3]
    title7 = Category.objects.get(id=13).name
    title7_en = Category.objects.get(id=13).name_en

    pa40_records = SettingsModel.objects.filter(key='pa40_comment')
    pa40_comments = []
    for i in pa40_records:
        if len(i.sValue2)<2 or len(i.sValue)<2: # 留空则不显示
            continue
        pa40_comments.append({
            'id': i.id,
            'title': i.sValue,
            'content': i.sValue2
        })
    
    lang = request.session.get('language', '')
    if not lang:
        request.session['language'] = 'ch'
        lang = 'ch'

    template = loader.get_template('pa40.html')
    context = {
        'cats': cats,
        'cat_img': '/s/'+cat_img,
        'language_en': lang=='en',
        'username': request.user.username,
        'main_articles': main_articles,
        'main_articles2': main_articles2,
        'main_articles3': main_articles3,
        'main_articles4': main_articles4,
        'main_articles5': main_articles5,
        'main_articles6': main_articles6,
        'main_articles7': main_articles7,
        'title2': title2,
        'title3': title3,
        'title4': title4,
        'title5': title5,
        'title6': title6,
        'title7': title7,
        'title2_en': title2_en,
        'title3_en': title3_en,
        'title4_en': title4_en,
        'title5_en': title5_en,
        'title6_en': title6_en,
        'title7_en': title7_en,
        'pa40_comments': pa40_comments,
        'pa40_comment_num': len(pa40_comments),
    }
    getGlobalConfig(context)
    return HttpResponse(template.render(context, request))