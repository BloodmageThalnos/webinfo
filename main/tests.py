from django.test import TestCase
from django.conf import settings
from main.views import *

class TestEmail(TestCase):
    def setUp(self):
        pass
    '''
    def test_send_mail(self):
        settings.EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
        from django.core.mail import send_mail
        try:
            succ = send_mail(
                subject = '该邮件仅用于网站测试，请忽略。',
                message = 'Here is the message.',
                from_email = 'GMA Admin <gma@gm-associates.cn>',
                recipient_list = ['cy1818cy@163.com', 'cy1818cy@bupt.edu.cn'],
                auth_user = 'gma@gm-associates.cn',
                auth_password = 'Huyin603',
                fail_silently = False)

            print('Successfully sent %d mail.'%succ)
        except Exception as e:
            print(e)
    '''

    def test_send_wechat(self):
        sendAlertToWechat('[WEBINFO] 微信报警测试。')
