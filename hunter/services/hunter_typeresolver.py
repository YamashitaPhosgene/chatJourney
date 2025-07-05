#!/usr/bin/env python
# encoding: utf-8

import functools
import json
import pickle
import random
import string
import time
from collections import Counter
from pathlib import Path
from typing import Optional
import logging

import numpy as np
import requests
from django.conf import settings
from django.db.models import Q

from hunter.api.amap_api import AmapAPIError, AmapPlaceAPI
from hunter.models import POICategory, POIKeywordAlias
from chatJourney.utils.auth import AuthUtils

# ──────────────────────────────────────────────────────────────
# ==========  配置  ============================================
# ──────────────────────────────────────────────────────────────
APP_ID: str = settings.VIVO_APP_ID
APP_KEY: str = settings.VIVO_APP_KEY
EMB_MODEL = "m3e-base"                   # vivo 推荐中文模型
EMB_URL = "https://api-ai.vivo.com.cn/embedding-model-api/predict/batch"
TIMEOUT = 8                              # s

VECTOR_FILE = Path("vector_cache/poi_vec.pkl")
VECTOR_FILE.parent.mkdir(exist_ok=True, parents=True)

EMB_THRESHOLD = getattr(settings, "POI_EMB_THRESHOLD", 0.70)
EMB_DIM_EXPECT = 768                     # m3e-base 输出 768 维

# ──────────────────────────────────────────────────────────────
# ==========  加载本地向量缓存  =================================
# ──────────────────────────────────────────────────────────────
try:
    with VECTOR_FILE.open("rb") as f:
        VEC_MAP: dict[str, np.ndarray] = pickle.load(f)
        _dim = next(iter(VEC_MAP.values())).shape[0]
        if _dim != EMB_DIM_EXPECT:       # 维度不匹配说明旧模型缓存，清空
            print(f"[TypeSolver] 旧向量维度 {_dim} 与 m3e-base 不兼容，忽略缓存")
            VEC_MAP = {}
except FileNotFoundError:
    VEC_MAP = {}

# ──────────────────────────────────────────────────────────────
# ==========  高德 API & 数据  =================================
# ──────────────────────────────────────────────────────────────
PLACE_API = AmapPlaceAPI(key=settings.AMAP_KEY)

OFFICIAL_NAMES = list(
    POICategory.objects.values_list("big_cn", "mid_cn", "sub_cn", "code")
)

# 精确匹配字典（常用词快速匹配）
EXACT_DICT = {
    # ——— 美食类 ———
    "小笼包": "050100",
    "火锅":   "050117",
    "烧烤":   "050120",
    "奶茶":   "050500",
    "咖啡":   "050504",
    "甜品":   "050900",
    "小吃":   "050800",
    "餐厅":   "050100",
    "饭店":   "050100",
    "快餐":   "050800",

    # ——— 购物类 ———
    "商场":     "060100",
    "购物中心": "060100",
    "百货":     "060102",
    "超市":     "060400",
    "便利店":   "060200",
    "专卖店":   "060901",

    # ——— 娱乐类 ———
    "电影院": "080601",
    "KTV":   "080302",
    "游戏厅": "080305",
    "网吧":   "080308",
    "酒吧":   "080304",
    "夜店":   "080300",

    # ——— 景点类 ———
    "公园":   "110101",
    "博物馆": "110102",
    "美术馆": "110103",
    "动物园": "110104",
    "游乐园": "110108",
    "景区":   "110000",
    "古迹":   "110205",
    "寺庙":   "110205",
    "道观":   "110205",
    
    # ——— 植物园/园林类 ———
    "植物园": "110103",    # 园区景点（明确）
    "花园":   "110103",    # 园区景点（明确）
    "园林":   "110103",    # 园区景点（明确）
    "绿化":   "110103",    # 园区景点（明确）
    "温室":   "110103",    # 园区景点（明确）
    "苗圃":   "110103",    # 园区景点（明确）

    # ——— 交通类 ———
    "地铁站": "150500",
    "公交站": "150500",
    "火车站": "150500",
    "汽车站": "150500",
    "机场":   "150100",

    # ——— 住宿类 ———
    "酒店": "100100",
    "宾馆": "100100",
    "民宿": "980100",
    "旅馆": "070202",
    "客栈": "980100",

    # ——— 生活服务类 ———
    "银行":   "160000",
    "医院":   "090100",
    "药店":   "090200",
    "学校":   "140000",
    "图书馆": "140400",
    "健身房": "080306",
    "美容院": "070204",
    "理发店": "070201",

    # ——— 英文别名 ———
    "citywalk":   "110101",
    "city walk":  "110101",
    "restaurant": "050100",
    "cafe":       "050504",
    "coffee":     "050504",
    "mall":       "060100",
    "shopping":   "060100",
    "hotel":      "100100",
    "park":       "110101",
    "museum":     "110102",
    "cinema":     "080601",
    "movie":      "080601",
    "bar":        "080304",
    "bank":       "160000",
    "hospital":   "090100",
    "school":     "140000",
    "gym":        "080306",
}

# 歧义词黑名单 - 这些词语有多种含义，拒绝自动映射
AMBIGUOUS_WORDS = {
    "花卉",      # 可能是花卉店、花卉园区、花卉市场
    "植物",      # 可能是植物园、植物店、植物市场
    "园区",      # 可能是工业园区、景点园区、住宅园区
    "广场",      # 可能是购物广场、公园广场、交通广场
    "中心",      # 可能是购物中心、商务中心、文化中心
    "市场",      # 可能是菜市场、商品市场、景点市场
    "城",        # 可能是购物城、古城景点、住宅城
    "店",        # 太泛化，需要具体店铺类型
    "馆",        # 太泛化，需要具体馆类型
    "场",        # 太泛化，需要具体场地类型
}

# ──────────────────────────────────────────────────────────────
# ==========  远程向量请求  ====================================
# ──────────────────────────────────────────────────────────────
def call_embedding_api(texts: list[str]) -> list[np.ndarray]:
    """
    批量获取文本向量；出错直接抛异常
    """
    payload = {"model_name": EMB_MODEL, "sentences": texts}
    
    # 使用项目现有的AuthUtils进行鉴权
    uri = "/embedding-model-api/predict/batch"
    query = {}
    headers = AuthUtils.gen_sign_headers(APP_ID, APP_KEY, "POST", uri, query)
    headers["Content-Type"] = "application/json"
    
    url = f"https://api-ai.vivo.com.cn{uri}"
    url_with_params = f"{url}?{AuthUtils.gen_canonical_query_string(query)}"
    
    resp = requests.post(url_with_params, json=payload, headers=headers, timeout=TIMEOUT)
    resp.raise_for_status()
    vec_list: list[list[float]] = resp.json()["data"]
    return [np.array(v, dtype=np.float32) for v in vec_list]

# ──────────────────────────────────────────────────────────────
# ==========  句向量比对入口  ==================================
# ──────────────────────────────────────────────────────────────
def resolve_by_vec(keyword: str) -> Optional[str]:
    """
    1. 若 keyword 向量已在本地缓存 → 直接点积
    2. 否则调用 vivo API 获取向量 → 补进缓存 → 点积
    """
    if not keyword:
        return None

    # (1) 获取当前关键词向量
    if keyword not in VEC_MAP:
        try:
            vec = call_embedding_api([keyword])[0]
            if vec.shape[0] != EMB_DIM_EXPECT:
                print(f"[TypeSolver] 向量维度异常：{vec.shape}")
                return None
            VEC_MAP[keyword] = vec
            with VECTOR_FILE.open("wb") as f:
                pickle.dump(VEC_MAP, f)
        except Exception as e:
            print(f"[TypeSolver] 远程向量请求失败: {e}")
            return None

    q_vec = VEC_MAP[keyword]
    best_code, best_sim = None, 0.0

    for code, vec in VEC_MAP.items():
        if code == keyword:   # 跳过自身
            continue
        sim = float(np.dot(q_vec, vec))
        if sim > best_sim:
            best_code, best_sim = code, sim
    return best_code if best_sim >= EMB_THRESHOLD else None

# ──────────────────────────────────────────────────────────────
# ==========  其余函数（未改变或略微整理）  =====================
# ──────────────────────────────────────────────────────────────
def probe_by_place(keyword: str) -> str | None:
    try:
        data = PLACE_API.text_search(keywords=keyword, page_size=5)
        codes = [c for p in data.get("pois", [])
                 for c in p["typecode"].split("|")
                 if c[-2:] != "00"]
        return Counter(codes).most_common(1)[0][0] if codes else None
    except Exception:
        return None


@functools.lru_cache(maxsize=4096)
def resolve_typecode(keyword: str) -> str | None:
    kw = keyword.strip()
    if not kw:
        return None
    
    # 检查歧义词黑名单 - 直接拒绝映射
    if kw in AMBIGUOUS_WORDS:
        logging.info(f"关键词 '{kw}' 是歧义词，拒绝自动映射，建议用户提供更具体的描述")
        return None
    
    # 1. 别名表
    alias = POIKeywordAlias.objects.filter(alias__iexact=kw).first()
    if alias:
        return alias.code
    if kw in EXACT_DICT:
        return EXACT_DICT[kw]
    # 2. 句向量
    code = resolve_by_vec(kw)
    if code:
        return code
    # 3. 动态探测兜底
    return probe_by_place(kw)


def interest_to_typecodes(int_keywords: list[str]) -> Optional[str]:
    codes = {resolve_typecode(w) for w in int_keywords}
    codes.discard(None)
    return "|".join(sorted(codes)) if codes else None


def get_poi_category_info(code: str) -> Optional[dict]:
    try:
        cat = POICategory.objects.get(code=code)
        return {
            "code": cat.code,
            "big_cn": cat.big_cn,
            "mid_cn": cat.mid_cn,
            "sub_cn": cat.sub_cn,
            "big_en": cat.big_en,
            "mid_en": cat.mid_en,
            "sub_en": cat.sub_en,
        }
    except POICategory.DoesNotExist:
        return None


def search_poi_by_keywords(keywords: str, region: str | None = None,
                           city_limit: bool = True,
                           page_size: int = 20, page: int = 1) -> dict:
    types_param = interest_to_typecodes([keywords])
    try:
        return PLACE_API.text_search(
            keywords=keywords,
            types=types_param,
            region=region,
            city_limit=city_limit,
            page_size=page_size,
            page_num=page
        )
    except AmapAPIError as e:
        return {"error": True, "message": str(e)}
    except Exception as e:
        return {"error": True, "message": f"搜索失败: {e}"}


def clear_cache():
    resolve_typecode.cache_clear()


def reload_official_names():
    global OFFICIAL_NAMES
    OFFICIAL_NAMES = list(
        POICategory.objects.values_list("big_cn", "mid_cn", "sub_cn", "code")
    ) 