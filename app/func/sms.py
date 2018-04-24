#encoding: utf-8
import json
import requests

'''
    使用leancloud
    1、发送短信验证码
    2、核对验证码
    （同一个手机号一天有发送数量的限制）
'''

# 请求的头部内容
headers = {
    "X-LC-Id": "MsoTLkEDGiaXit5ChRbcOFSs-gzGzoHsz",
    "X-LC-Key": "MOpKyRxgFpkQs9jMpbz2zAx7",
    "Content-Type": "application/json",
}

# 请求发送验证码 API
REQUEST_SMS_CODE_URL = 'https://api.leancloud.cn/1.1/requestSmsCode'

# 请求校验验证码 API
VERIFY_SMS_CODE_URL = 'https://api.leancloud.cn/1.1/verifySmsCode/'


def send_message(phone):
    print u"准备请求号码：",phone
    data = {
        "mobilePhoneNumber": phone,
    }
    r = requests.post(REQUEST_SMS_CODE_URL, data=json.dumps(data), headers=headers)
    print u'请求结果：',r.text
    print u'请求状态：',r.status_code
    if r.status_code == 200:
        return True
    else:
        return False

def verify(phone, code):
    target_url = VERIFY_SMS_CODE_URL + "%s?mobilePhoneNumber=%s" % (code, phone)
    r = requests.post(target_url, headers=headers)
    if r.status_code == 200:
        return True
    else:
        return False