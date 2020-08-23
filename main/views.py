#! encoding: utf-8
import logging
from django.shortcuts import render
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import loader
from django.contrib.auth import *
from django.contrib.auth.models import User

from main.models import ArticleModel, Category, SettingsModel, UsersModel

logger = logging.getLogger(__name__)

def showMain(request):
    return HttpResponse('<h1>抱歉，页面正在维护中，请稍后再试。</h1>')

def showHome(request):
    logger.info(f'Accessed {request.get_full_path()} with showHome')

    categories = Category.objects.all()
    cats = []
    for category in categories:
        cats.append({
            'id': category.id,
            'name': category.name
        })
    cats = cats[::-1]
    
    template = loader.get_template('home.html')
    context = {
        'cats': cats,
        'username': request.user.username,
    }
    return HttpResponse(template.render(context, request))

def showInfo(request):
    logger.info(f'Accessed {request.get_full_path()} with showInfo')

    categories = Category.objects.all()
    cats = []
    for category in categories:
        cats.append({
            'id': category.id,
            'name': category.name
        })
    cats = cats[::-1]
    
    template = loader.get_template('info.html')
    context = {
        'cats': cats,
        'username': request.user.username,
    }
    return HttpResponse(template.render(context, request))
    
def showLogin(request, alert=""):
    logger.info(f'Accessed {request.get_full_path()} with showLogin')

    if request.user.is_authenticated:
        return HttpResponseRedirect('/home')

    categories = Category.objects.all()
    cats = []
    for category in categories:
        cats.append({
            'id': category.id,
            'name': category.name
        })
    cats = cats[::-1]
    
    template = loader.get_template('login.html')
    context = {
        'hashcode': "5328f58ffb2425b2749701f281cbf21f9b776417f06cc35ba4511861a1cc0670",
        'cats': cats,
        'alert': alert,
    }
    return HttpResponse(template.render(context, request))

def showLoginAdmin(request, alert=""):
    if request.session.get("admin", ""):
        return HttpResponseRedirect('/admin')

    template = loader.get_template('login_admin.html')
    context = {
        'alert': alert,
    }
    return HttpResponse(template.render(context, request))

def doLogin(request):
    logger.info(f'Accessed {request.get_full_path()} with doLogin')

    username = request.GET.get('username')
    password = request.GET.get('password')
    hashcode = request.GET.get('hashcode')
    if not username or not password or hashcode!="5328f58ffb2425b2749701f281cbf21f9b776417f06cc35ba4511861a1cc0670":
        return None
    
    user = authenticate(request, username=username, password=password)
    if user:
        login(request, user)

        return HttpResponseRedirect('/home')
    else:
        return showLogin(request, "用户名或密码错误，请重试。")

def doLogout(request):
    logger.info(f'Accessed {request.get_full_path()} with doLogout')

    logout(request)

    return HttpResponseRedirect('/home')
        
def doLoginAdmin(request):
    password = request.GET.get('password')
    hashcode = request.GET.get('hashcode')
    if password and SettingsModel.objects.get(key='adminpassword').sValue==password:
        request.session["admin"] = 1
        return HttpResponseRedirect('/admin')
    else:
        return showLoginAdmin(request, "用户名或密码错误，请重试。")

def showAdmin(request):
    if not request.session.get("admin", ""):
        return HttpResponseRedirect('/login_admin')

    template = loader.get_template('admin.html')

    main_bg = SettingsModel.objects.filter(key='main-bg')
    main_bg_list = []
    for _ in main_bg:
        main_bg_list.append({
            'src': '/s/'+_.sValue,
            'id': _.id,
        })
    
    main_text = SettingsModel.objects.filter(key='main-text')[0].sValue

    users = UsersModel.objects.all()
    user_list = []
    for _ in users:
        login_date = (User.objects.get(username=_.username)).last_login
        login_date_str = "最近未登录" if not login_date else login_date.strftime("%Y/%m/%d")
        user_list.append({
            'id': _.id,
            'username': _.username,
            'password': _.password,
            'last_login_date': login_date_str,
        })
    
    categories = Category.objects.all()
    category_list = []
    for _ in categories:
        if not _.extra:
            _.extra='10'
            _.save()
        showuser = (_.extra[0]=='1')
        canread = (_.extra[1]=='1')
        category_list.append({
            'id': _.id,
            'name': _.name,
            'show_user': showuser,
            'can_read_anonymous': canread,
            'coverimg': '/s/'+_.coverimg,
            'name_white': _.title_white,
        })

    context = {
        'main_bg_list': main_bg_list,
        'main_text': main_text,
        'user_list': user_list,
        'category_list': category_list,

    }
    return HttpResponse(template.render(context, request))

def doAdminAction(request):
    if not request.session.get("admin", ""):
        return HttpResponseRedirect('/login_admin')

    try:
        actionid = request.GET.get('aid')
        if actionid=='1': # 首页图片移除
            pid = request.GET.get('pid')
            key = SettingsModel.objects.get(id=int(pid))
            if key.key == 'main-bg':
                key.delete()
        elif actionid=='2': # 首页图片添加
            import time
            import os
            pic = request.FILES.get("pic")
            filename = 'bg-' + str(int(time.time()*1000)%1000000007) + os.path.splitext(pic.name)[1]
            cimg = '/s/' + filename
            with open('./images/' + filename, "wb") as fPic:
                for chunk in pic.chunks():
                    fPic.write(chunk)
            key = SettingsModel(key='main-bg', sValue=filename)
            key.save()
        elif actionid=='3':
            key = SettingsModel.objects.get(key="main-text")
            key.sValue = request.GET.get("txt", "")
            key.save()
        elif actionid=='4':
            id = request.GET.get('pid')
            User.objects.get(username=UsersModel.objects.get(id=int(id)).username).delete()
            UsersModel.objects.get(id=int(id)).delete()
        elif actionid=='5':
            id = request.GET.get('pid')
            password = str(random.randint(10000000, 99999999))
            um = UsersModel.objects.get(id=int(id))
            um.password = password
            um.save()
            u = User.objects.get(username = um.username)
            u.set_password(password)
            u.save()
        elif actionid=='6':
            usernames = request.GET.get("txt")
            for username in usernames.split('\n'):
                if username:
                    if len(User.objects.filter(username=username)):
                        continue
                    import random
                    password = str(random.randint(10000000, 99999999))
                    user = User.objects.create_user(username, 'lennon@thebeatles.com', password)
                    user.save()
                    UsersModel.objects.create(username=username, password=password)
        elif actionid=='7':
            oldp = request.GET.get("old")
            newp = request.GET.get("newp")
            s = SettingsModel.objects.get(key='adminpassword')
            if oldp == s.sValue:
                if newp and len(newp)>=10:
                    s.sValue = newp
                    s.save()
            else:
                del request.session["admin"]
                return showLoginAdmin(request, "管理员口令错误，请重试。")
        elif actionid=='del_ban':
            pid = int(request.GET.get('pid'))
            category = Category.objects.get(id=pid)
            category.delete()
        elif actionid=='rename_ban':
            pid = int(request.GET.get('pid'))
            txt = request.GET.get('txt')
            category = Category.objects.get(id=pid)
            if txt and 1<=len(txt)<=10:
                category.name = txt
                category.save()
        elif actionid=='add_ban':
            name = request.GET.get('name')
            canread = request.GET.get('canread')
            showuser = request.GET.get('showuser')
            if not canread in '01' or not showuser in '01':
                return None
            extra = (showuser) + (canread)
            category = Category(name=name, desc='', extra=extra)
            category.save()
        elif actionid=='cha_ban':
            pid = int(request.GET.get('pid'))
            ind = int(request.GET.get('ind'))
            val = request.GET.get('val')
            if len(val)==1:
                c = Category.objects.get(id=pid)
                c.extra = c.extra[:ind] + val + (c.extra[ind+1:] if ind<len(c.extra)-1 else "")
                c.save()
        elif actionid=='rep_cat':
            cid = int(request.GET.get('cid'))
            category = Category.objects.get(id=cid)
            import time
            import os
            pic = request.FILES.get("pic")
            name_white = request.POST.get("name_white")
            if pic:
                filename = 'cbg-' + str(time.time()%100007) + os.path.splitext(pic.name)[1]
                with open('./images/' + filename, "wb") as fPic:
                    for chunk in pic.chunks():
                        fPic.write(chunk)
                category.coverimg = filename
            if name_white=="on":
                category.title_white = 1
            category.save()
            

        return HttpResponseRedirect('/admin')
    except Exception as e:
        logger.error('Exception at doAdminAction: '+str(e))



def showBin(request, path):
    try:
        suf2typ = {
            'ttf': 'application/x-font-ttf',
            'woff': 'application/x-font-woff',
            'svg': 'text/xml',
            'js': 'application/x-javascript',
            'css': 'text/css'
        }
        for suffix in suf2typ.keys():
            if path.endswith(suffix):
                with open('./static/'+path, mode="r", encoding="utf-8") as f:
                    html = f.read()
                return HttpResponse(html, content_type=suf2typ[suffix])
    except FileNotFoundError:
        logger.error(f'File not found: {path}')

    logger.error(f'Accessed {request.get_full_path()} with showBin matched nothing.' % path)
    return HttpResponse(None)


def showImages(request, path):
    try:
        suf2typ = {
            'jpg': 'image/jpeg',
            'jpe': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'gif': 'image/gif', 
            'ico': 'image/x-icon',
            'tiff': 'image/tiff',
            'tif': 'image/tiff',
            'net': 'image/pnetvue',
            'png': 'image/png',
            'wbmp': 'image/vnd.wap.wbmp',
            'pdf': 'application/pdf',
            'ttf': 'application/x-font-ttf',
            'woff': 'application/x-font-woff',
            'svg': 'text/xml',
            'mpeg': 'video/mpeg',
            'mpg': 'video/mpeg',
            'mp4': 'video/mpeg4',
            'mp3': 'audio/mp3'
        }
        for suffix in suf2typ.keys():
            if path.endswith(suffix):
                with open('./images/'+path, mode="rb") as f:
                    html = f.read()
                return HttpResponse(html, content_type=suf2typ[suffix])
    except FileNotFoundError:
        logger.error(f'File not found: {path}')

    logger.error(f'Accessed {request.get_full_path()} with showImages matched nothing.' % path)
    return HttpResponse(None)