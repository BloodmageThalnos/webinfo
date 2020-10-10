import sys
from urllib.parse import quote
from base64 import b64decode
import requests
import json

corpid = "ww4e45ef61d7851f60"
token_map = {
    "网站报警": ("1000004", "leEVSMiKfgldrXYFEfdOQfcvcbFoBP96OAbE10lz2LU"),
}
url_api_token = "https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=%s&corpsecret=%s"
url_send = "https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=%s"

def get_access_token(corp_id, corp_secret):
    try:
        resp = requests.get(url_api_token%(corp_id, corp_secret), timeout=3.01)
        jsp = json.loads(resp.text)
        if jsp["errcode"]:
            raise Exception(jsp["errmsg"])
        access_token = jsp["access_token"]
    except Exception as e:
        return None, ("Error: "+str(e))
    
    return access_token, None

def send_to_wechat(text, _from="网站报警", _to="@all", dup_check=1, dup_check_interval=60):
    token, err = get_access_token(corp_id=corpid, corp_secret=token_map[_from][1])
    if err:
        print(err)
        return
    params = {
        "touser" : _to,
        "msgtype" : "text",
        "agentid" : token_map[_from][0],
        "text" : {
            "content" : text,
        },
        "enable_duplicate_check": dup_check,
        "duplicate_check_interval": dup_check_interval,
        "debug": 1,
    }
    retry_times = 3
    while retry_times:
        try:
            resp = requests.post(url_send%token, data=json.dumps(params).encode(), timeout=3.01)
            jsp = json.loads(resp.text)
            if jsp["errcode"]:
                raise Exception(jsp["errmsg"])
            print('Send ok.')
            break
        except Exception as e:
            retry_times -= 1
            print('Request error: %s, %d retry left.'%(str(e), retry_times))
            if retry_times:
                continue