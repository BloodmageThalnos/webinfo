#! encoding: utf-8
import logging
from django.shortcuts import render
from django.http import HttpResponse, Http404, HttpResponseRedirect, JsonResponse
from django.template import loader
from django.contrib.auth import *
from django.contrib.auth.models import User

from main.models import ArticleModel, Category, SettingsModel, UsersModel, PA40CommentModel

import datetime
import pytz
import requests

logger = logging.getLogger(__name__)

def is_pa40(cat_id):
    return 5<=cat_id<=13

def getGlobalConfig(context):
    pa40_tag = Category.objects.get(id=5).name
    pa40_tag_en = Category.objects.get(id=5).name_en
    context['config_pa40_tag'] = pa40_tag
    context['config_pa40_tag_en'] = pa40_tag_en

def showMain(request):
    return showHome(request)
    #return HttpResponse('<h1>抱歉，页面正在维护中，请稍后再试。</h1>')

def showHome(request):
    logger.info(f'Accessed {request.get_full_path()} with showHome')

    categories = Category.objects.all()
    cats = []
    for category in categories:
        if not is_pa40(category.id):
            cats.append({
                'id': category.id,
                'name': category.name,
                'name_en': category.name_en,
            })
    cats = cats[::-1]

    try:
        import random
        from django.core.cache import cache
        main_text = random.choice(SettingsModel.objects.filter(key="main-text")).sValue
        while main_text == cache.get('main-text'):
            main_text = random.choice(SettingsModel.objects.filter(key="main-text")).sValue
        title, subtitle, link_text, link_src = main_text.split('嗄')
        cache.set('main-text', main_text)

        bg_pics = []
        for i in SettingsModel.objects.filter(key="main-bg"):
            bg_pics.append(i.sValue)
        bg_pic_id = random.randint(0, len(bg_pics)-1)
        try_times = 100
        while try_times and bg_pic_id == cache.get('bg_pic_id'):
            bg_pic_id = random.randint(0, len(bg_pics)-1)
        cache.set('bg_pic_id', bg_pic_id)
        bg_pics = '"' + bg_pics[bg_pic_id] + '"'
    except Exception as e:
        logger.error(e)
        main_text = "提供全球经济与政治洞见"
        bg_pics = '"1-1920.png", "2-1920.png", "3-1920.png", "4-1920.png"'
    
    lang = request.session.get('language', '')
    if not lang:
        request.session['language'] = 'ch'
        lang = 'ch'
    
    template = loader.get_template('home.html')
    context = {
        'cats': cats,
        'username': request.user.username,
        'title': title,
        'subtitle': subtitle,
        'link_text': link_text,
        'link_src': link_src,
        'bgpics': bg_pics,
        'language_en': lang=='en',
    }
    getGlobalConfig(context)
    return HttpResponse(template.render(context, request))

def showInfo(request):
    logger.info(f'Accessed {request.get_full_path()} with showInfo')

    categories = Category.objects.all()
    cats = []
    for category in categories:
        if not is_pa40(category.id):
            cats.append({
                'id': category.id,
                'name': category.name,
                'name_en': category.name_en,
            })
    cats = cats[::-1]
    
    lang = request.session.get('language', '')
    if not lang:
        request.session['language'] = 'ch'
        lang = 'ch'
    
    template = loader.get_template('info.html')
    context = {
        'cats': cats,
        'username': request.user.username,
        'language_en': lang=='en',
    }
    getGlobalConfig(context)
    return HttpResponse(template.render(context, request))
    
def showLogin(request, alert=""):
    logger.info(f'Accessed {request.get_full_path()} with showLogin')

    if request.user.is_authenticated:
        return HttpResponseRedirect('/home')

    categories = Category.objects.all()
    cats = []
    for category in categories:
        if not is_pa40(category.id):
            cats.append({
                'id': category.id,
                'name': category.name,
                'name_en': category.name_en,
            })
    cats = cats[::-1]

    lang = request.session.get('language', '')
    if not lang:
        request.session['language'] = 'ch'
        lang = 'ch'
    
    template = loader.get_template('login.html')
    context = {
        'hashcode': "5328f58ffb2425b2749701f281cbf21f9b776417f06cc35ba4511861a1cc0670",
        'cats': cats,
        'alert': alert,
        'language_en': lang=='en',
    }
    getGlobalConfig(context)
    return HttpResponse(template.render(context, request))

def showLoginAdmin(request, alert=""):
    if request.session.get("admin", ""):
        return HttpResponseRedirect('/admin')

    template = loader.get_template('login_admin.html')
    context = {
        'alert': alert,
    }
    getGlobalConfig(context)
    return HttpResponse(template.render(context, request))

def changeLanga(request):
    lang = request.GET.get('to')
    if lang!='ch' and lang!='en':return None
    request.session['language']=lang
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/home'))

def doLogin(request):
    logger.info(f'Accessed {request.get_full_path()} with doLogin')

    username = request.GET.get('username')
    password = request.GET.get('password')
    hashcode = request.GET.get('hashcode')
    if hashcode!="5328f58ffb2425b2749701f281cbf21f9b776417f06cc35ba4511861a1cc0670":
        sendAlertToWechat('出现异常登录请求。')

    if not username or not password:
        return None
    
    user = authenticate(request, username=username, password=password)
    if user:
        login(request, user)

        return HttpResponseRedirect('/home')
    else:
        return showLogin(request, "用户名或密码错误，请重试。")
    
def showChangePassword(request):
    template = loader.get_template('login_changePassword.html')

    categories = Category.objects.all()
    cats = []
    for category in categories:
        if not is_pa40(category.id):
            cats.append({
                'id': category.id,
                'name': category.name,
                'name_en': category.name_en,
            })
    cats = cats[::-1]
    
    lang = request.session.get('language', '')
    if not lang:
        request.session['language'] = 'ch'
        lang = 'ch'

    context = {
        'cats': cats,
        'language_en': lang=='en',
    }
    getGlobalConfig(context)
    return HttpResponse(template.render(context, request))


def doRegister(request, action):
    if action=='0':
        template = loader.get_template('register.html')

        categories = Category.objects.all()
        cats = []
        for category in categories:
            if not is_pa40(category.id):
                cats.append({
                    'id': category.id,
                    'name': category.name,
                    'name_en': category.name_en,
                })
        cats = cats[::-1]
        
        lang = request.session.get('language', '')
        if not lang:
            request.session['language'] = 'ch'
            lang = 'ch'

        context = {
            'cats': cats,
            'language_en': lang=='en',
        }
        return HttpResponse(template.render(context, request))
    
    if action=='1':
        email = request.GET.get('e')
        if email:
            import random
            captcha = request.session['captcha'] = random.choice(['6666', '8888', '8688', '8868', '1234', '2345', '3456', '4567', '5678', '6789', '7890', '2333'])
            sendEmailCaptcha(captcha, email, request.session['language'])
            return HttpResponse('{"success": true}')
    
    if action=='2':
        email = request.GET.get('e')
        username = request.GET.get('u')
        password = request.GET.get('p')
        captcha = request.GET.get('c')

        if not captcha or captcha != request.session['captcha']:
            return JsonResponse({'success': False, 'msg': '验证码错误！'})
        
        try:
            UsersModel.objects.get(username=username)
            return JsonResponse({'success': False, 'msg': '用户名已被占用！'})
        except: pass
    
        user = User.objects.create_user(username, email, password)
        user.save()
        UsersModel.objects.create(username=username, password=password)
        return JsonResponse({'success': True})
    
    if action=='3':
        nowp = request.GET.get('nowp')
        newp = request.GET.get('newp')
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'success': False, 'msg': '请登录后再修改密码！'})
        if not nowp or not newp:
            return JsonResponse({'success': False})
        if len(newp)<6:
            return JsonResponse({'success': False, 'msg': '密码过于简单。'})
        try:
            um = UsersModel.objects.get(username=user.username)
            if nowp != um.password:
                return JsonResponse({'success': False, 'msg': '原密码错误！'})
            um.password = newp
            user.set_password(newp)
            um.save()
            user.save()
        except Exception as e:
            sendAlertToWechat('/reg3修改密码接口出现异常：'+str(e))
            logger.error(str(e))
            return JsonResponse({'success': False, 'msg': '未知错误，请联系管理员。'})

    return HttpResponse({'success': True})

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

def sendEmailCaptcha(captcha, to_email, language='ch'):
    from django.core.mail import send_mail
    try:
        succ = send_mail(
            subject = '【光华茂源】会员注册验证码' if language=='ch' else '[GMA]Verification code for registration',
            message = ('您的注册验证码是：' if language=='ch' else 'Your verification code is ') + captcha,
            from_email = 'GMA Admin <gma@gm-associates.cn>',
            recipient_list = [to_email],
            auth_user = 'gma@gm-associates.cn',
            auth_password = 'Huyin603',
            fail_silently = False)
        if succ<1: raise 'send_mail返回值小于预期发送邮件数量。'
        logger.info('Successfully sent %d mail to %s: %s'%(succ, to_email, captcha))
    except Exception as e:
        sendAlertToWechat('发送验证邮件失败：'+str(e))
        logger.error('sendEmailCaptcha error: \n'+str(e))

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
    
    main_text = SettingsModel.objects.filter(key='main-text')
    main_text_list = []
    for _ in main_text:
        title, subtitle, link_text, link_src = _.sValue.split('嗄')
        main_text_list.append({
            'tid': _.id,
            'title': title,
            'subtitle': subtitle,
            'link_text': link_text,
            'link_src': link_src,
        })

    users = UsersModel.objects.all()
    user_list = []
    for _ in users:
        user = User.objects.get(username=_.username)
        login_date = user.last_login
        login_date_str = "最近未登录" if not login_date else login_date.strftime("%Y/%m/%d")
        vip_time = '-'
        if _.vip:
            vip_status = '会员'
            vip_time = '永久'
        elif _.trial_date and datetime.datetime.now().replace(tzinfo=pytz.timezone('UTC')) < _.trial_date:
            vip_status = '试用中'
            vip_time = _.trial_date.strftime("%Y-%m-%d")
        else:
            vip_status = '非会员'
            
        user_list.append({
            'id': _.id,
            'username': _.username,
            'email': user.email,
            'last_login_date': login_date_str,
            'vip_status': vip_status,
            'vip_timestr': vip_time,
        })
    
    pa40_records = SettingsModel.objects.filter(key='pa40_comment')
    pa40_comments = []
    for i in pa40_records:
        pa40_comments.append({
            'id': i.id,
            'title': i.sValue,
            'content': i.sValue2
        })
    
    pa40_all_r = PA40CommentModel.objects.all()
    pa40_commentall = []
    for i in pa40_all_r:
        pa40_commentall.append({
            'id': i.id,
            'username': i.username,
            'content': i.content,
        })
    
    categories = Category.objects.all()
    category_list = []
    for _ in categories:
        if not _.extra:
            _.extra='100'
            _.save()
        if len(_.extra)==2:
            _.extra+='0'
            _.save()
        showuser = (_.extra[0]=='1')
        canread = (_.extra[1]=='1')
        cancomment = (_.extra[2]=='1')
        category_list.append({
            'id': _.id,
            'name': _.name,
            'name_en': _.name_en,
            'show_user': showuser,
            'can_read_anonymous': canread,
            'can_comment': cancomment,
            'coverimg': '/s/'+_.coverimg,
            'name_white': _.title_white,
        })

    context = {
        'main_bg_list': main_bg_list,
        'main_text_list': main_text_list,
        'user_list': user_list,
        'category_list': category_list,
        'pa40_comments': pa40_comments,
        'pa40_commentall': pa40_commentall,
    }
    getGlobalConfig(context)
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
        elif actionid=='3': # 首页标题
            key = SettingsModel.objects.get(id=int(request.GET.get('tid')))
            key.sValue = request.POST.get("title", "") + "嗄" + request.POST.get("subtitle", "") + "嗄" +request.POST.get("link_text", "") + "嗄" + request.POST.get("link_src", "")
            key.save()
        elif actionid=='4':
            id = request.GET.get('pid')
            User.objects.get(username=UsersModel.objects.get(id=int(id)).username).delete()
            UsersModel.objects.get(id=int(id)).delete()
        elif actionid=='5':
            id = request.GET.get('pid')
            password = "123456"
            um = UsersModel.objects.get(id=int(id))
            um.password = password
            um.save()
            u = User.objects.get(username = um.username)
            u.set_password(password)
            u.save()
        elif actionid=='5.1':
            id = int(request.GET.get('uid'))
            um = UsersModel.objects.get(id=id)
            um.vip = 1
            um.save()
        elif actionid=='5.7':
            id = int(request.GET.get('uid'))
            um = UsersModel.objects.get(id=id)
            um.trial_date = datetime.datetime.now() + datetime.timedelta(days=7)
            um.save()
        elif actionid=='5.30':
            id = int(request.GET.get('uid'))
            um = UsersModel.objects.get(id=id)
            um.trial_date = datetime.datetime.now() + datetime.timedelta(days=30)
            um.save()
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
            if txt and 1<=len(txt)<=20:
                category.name = txt
                category.save()
        elif actionid=='rename_en_ban':
            pid = int(request.GET.get('pid'))
            txt = request.GET.get('txt')
            category = Category.objects.get(id=pid)
            if txt and 1<=len(txt)<=36:
                category.name_en = txt
                category.save()
        elif actionid=='add_ban':
            name = request.GET.get('name')
            name_en = request.GET.get('name_en')
            canread = request.GET.get('canread')
            showuser = request.GET.get('showuser')
            if not canread in '01' or not showuser in '01':
                return None
            extra = (showuser) + (canread)
            category = Category(name=name, desc='', extra=extra, name_en=name_en)
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
        elif actionid=='pa40c':
            cid = int(request.GET.get('cid'))
            comment_record = SettingsModel.objects.get(id=cid)
            if comment_record.iValue != -1:
                raise 'PA40 Comment record error, possibly attack.'
            title = request.POST.get('title')
            content = request.POST.get('content')
            if not title or not content:
                raise 'Comment value should not be null.'
            comment_record.sValue = title
            comment_record.sValue2 = content
            comment_record.save()
        elif actionid=='pa40d':
            cid = int(request.GET.get('cid'))
            comment_record = PA40CommentModel.objects.get(id=cid)
            comment_record.delete()
            

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

def showIcon(request):
    with open('./favicon.ico', mode="rb") as f:
        icon = f.read()
    return HttpResponse(icon, content_type='image/x-icon')

def showQRCode(request):
    url = request.GET.get('url')
    try:
        resp = requests.get('https://api.pwmqr.com/qrcode/create/?url='+url, timeout=3)
        if resp.status_code != 200 or len(resp.content)<32:
            raise Exception('返回值%d, 返回长度%d.'%(resp.status_code, len(resp.content)))
    except Exception as e:
        sendAlertToWechat('QRCode 接口异常'+str(e))
        return None
    return HttpResponse(resp.content, content_type='image/png')

def sendAlertToWechat(msg):
    from django.core.cache import cache
    from .wechat import send_to_wechat
    if cache.get('wechat_alert'):
        logger.info('Tried to send wechat but too busy:\n'+msg)
        return
    cache.set('wechat_alert', True, 120) # 每120秒最多一条报警
    send_to_wechat('[WEBINFO] '+msg)