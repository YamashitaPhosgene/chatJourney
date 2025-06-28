import time
import random
import string
import requests
import hashlib
import hmac
import urllib.parse
from typing import Dict, Any, Optional
from chatJourney.utils.auth import AuthUtils
from django.conf import settings

# 签名头生成工具
def gen_sign_headers(app_id: str, app_key: str, method: str, uri: str, params: Dict[str, Any]) -> Dict[str, str]:
    timestamp = str(int(time.time()))
    nonce = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    signed_headers = 'x-ai-gateway-app-id;x-ai-gateway-timestamp;x-ai-gateway-nonce'
    # 构造待签名字符串
    param_str = '&'.join(f'{k}={urllib.parse.quote(str(v))}' for k, v in sorted(params.items()))
    sign_str = f'{method}\n{uri}\n{param_str}\n{app_id}\n{timestamp}\n{nonce}\n'
    signature = hmac.new(app_key.encode('utf-8'), sign_str.encode('utf-8'), hashlib.sha256).hexdigest()
    return {
        'Content-Type': 'application/json',
        'X-AI-GATEWAY-APP-ID': app_id,
        'X-AI-GATEWAY-TIMESTAMP': timestamp,
        'X-AI-GATEWAY-NONCE': nonce,
        'X-AI-GATEWAY-SIGNED-HEADERS': signed_headers,
        'X-AI-GATEWAY-SIGNATURE': signature
    }

# POI搜索主函数
def poi_search(app_id: Optional[str] = None, app_key: Optional[str] = None, keywords: str = '', city: str = '', page_num: int = 1, page_size: int = 10) -> Dict:
    """
    地理编码（POI搜索）服务
    :param app_id: vivo平台分配的app_id（可选，默认读取settings.VIVO_APP_ID）
    :param app_key: vivo平台分配的app_key（可选，默认读取settings.VIVO_APP_KEY）
    :param keywords: 搜索关键词
    :param city: 城市名或行政区划编码
    :param page_num: 页码
    :param page_size: 每页条数
    :return: POI搜索结果
    """
    app_id = app_id or getattr(settings, 'VIVO_APP_ID', None)
    app_key = app_key or getattr(settings, 'VIVO_APP_KEY', None)
    if not app_id or not app_key:
        raise ValueError('请在settings.py配置VIVO_APP_ID和VIVO_APP_KEY，或通过参数传入')
    method = 'GET'
    domain = 'api-ai.vivo.com.cn'
    uri = '/search/geo'
    params = {
        'keywords': keywords,
        'city': city,
        'page_num': page_num,
        'page_size': page_size
    }
    headers = AuthUtils.gen_sign_headers(app_id, app_key, method, uri, params)
    headers['Content-Type'] = 'application/json'
    url = f'https://{domain}{uri}'
    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return {'error': response.text, 'status_code': response.status_code} 