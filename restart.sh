\cp /root/webinfo/nginx.ini /etc/nginx/conf.d/webinfo.conf
pkill -f uwsgi -9
systemctl restart nginx.service
uwsgi --ini /root/webinfo/uwsgi.ini
