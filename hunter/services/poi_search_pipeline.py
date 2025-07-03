#!/usr/bin/env python
# encoding: utf-8

"""
Pipeline:
1. 调用 LLM prompt -> 关键词 JSON (使用 talker.services.poi_keywords_service)
2. 根据 city_keywords -> adcode (AmapDistrictAPI)
3. interest_keywords -> typecode (hunter_typeresolver)
4. keywords+typecode+adcode -> AmapPlaceAPI.text_search()

返回结构：
{
  "query": {...LLM 输出...},
  "adcode": "110108",
  "types": "050118|050000",
  "pois": {
      "小笼包": [ {name, location, ...}, ... ],
      ...
  }
}
"""

from __future__ import annotations
import json
import logging
import time
from typing import Dict, List, Any, Optional
from collections import defaultdict

from django.conf import settings
from hunter.api.amap_api import (
    AmapDistrictAPI,
    AmapPlaceAPI,
    AmapAPIError,
)
from hunter.services.hunter_typeresolver import interest_to_typecodes, resolve_typecode
from talker.services.poi_keywords_service import POIKeywordsService


def first_or_none(seq):
    """安全获取列表第一个元素，如果列表为空返回None"""
    return seq[0] if seq else None


def build_code_map(int_keywords: List[str]) -> Dict[str, List[str]]:
    """
    构建兴趣关键词到分类码的映射
    
    Args:
        int_keywords: 兴趣关键词列表
        
    Returns:
        分类码到关键词列表的映射，例如 {"050100": ["龙抄手","钟水饺"], "110205": ["道教圣地"]}
    """
    code_map = defaultdict(list)
    for word in int_keywords:
        code = resolve_typecode(word)
        if code:
            code_map[code].append(word)
            logging.debug(f"兴趣关键词 '{word}' 映射到分类码: {code}")
        else:
            logging.warning(f"兴趣关键词 '{word}' 未找到匹配的分类码")
    
    logging.info(f"构建分类码映射: {dict(code_map)}")
    return code_map


class POISearchPipeline:
    """POI搜索管道 - 集成LLM关键词生成和高德API搜索"""
    
    def __init__(self, amap_key: str | None = None, qps_limit: int = 2):
        """
        初始化POI搜索管道
        
        Args:
            amap_key: 高德地图API密钥
            qps_limit: QPS限制，默认2次/秒（间隔0.5秒）
        """
        self.amap_key = amap_key or settings.AMAP_KEY
        if not self.amap_key:
            raise ValueError("高德地图API密钥未配置")
        
        self.place_api = AmapPlaceAPI(self.amap_key)
        self.district_api = AmapDistrictAPI(self.amap_key)
        self.poi_keywords_service = POIKeywordsService()
        
        # QPS控制 - 平衡设置
        self.qps_limit = qps_limit
        self.request_interval = 1.0 / qps_limit  # 请求间隔（秒）
        self.last_request_time = 0  # 上次请求时间
        
        logging.info(f"POI搜索管道初始化完成，QPS限制: {qps_limit} (间隔: {self.request_interval:.2f}秒)")

    def _rate_limit(self):
        """QPS控制：确保请求间隔符合限制"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_interval:
            sleep_time = self.request_interval - time_since_last
            logging.info(f"QPS控制：等待 {sleep_time:.3f} 秒 (限制: {self.qps_limit}/秒)")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()

    # ------------ Step-1 LLM 生成关键词 ------------
    def _call_llm(self, conversation: List[Dict[str, str]], session_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        调用大模型生成POI关键词
        
        Args:
            conversation: 对话历史
            session_info: 会话信息
            
        Returns:
            关键词JSON字典
        """
        try:
            # 使用项目中已有的POI关键词生成服务
            keywords = self.poi_keywords_service._generate_keywords(conversation, session_info or {})
            
            if not keywords:
                # 如果生成失败，返回默认结构
                return {
                    "primary_keywords": [],
                    "secondary_keywords": [],
                    "city_keywords": [],
                    "interest_keywords": [],
                    "search_suggestions": [],
                    "avoid_keywords": []
                }
            
            return keywords
            
        except Exception as e:
            logging.error(f"LLM关键词生成失败: {e}")
            return {
                "primary_keywords": [],
                "secondary_keywords": [],
                "city_keywords": [],
                "interest_keywords": [],
                "search_suggestions": [],
                "avoid_keywords": []
            }

    # ------------ Step-2 城市 → adcode ------------
    def _get_adcode(self, city_keywords: List[str]) -> str | None:
        """
        根据城市关键词获取行政区划代码
        
        Args:
            city_keywords: 城市关键词列表
            
        Returns:
            行政区划代码或None
        """
        for word in city_keywords:
            try:
                self._rate_limit()  # QPS控制
                data = self.district_api.query(keywords=word, subdistrict=0)
                if data["status"] == "1" and data["districts"]:
                    # 安全访问第一个元素
                    first_district = first_or_none(data["districts"])
                    if first_district:
                        adcode = first_district["adcode"]
                        logging.info(f"找到城市 '{word}' 的adcode: {adcode}")
                        return adcode
                    else:
                        logging.warning(f"城市 '{word}' 返回的districts数据格式异常")
                else:
                    logging.warning(f"城市 '{word}' 未找到匹配的行政区信息")
            except AmapAPIError as e:
                logging.warning(f"查询城市 '{word}' 失败: {e}")
                if "QPS" in str(e) or "10021" in str(e):
                    logging.warning(f"QPS超限，等待更长时间...")
                    time.sleep(2.0)  # 额外等待2秒
                    try:
                        # 重试一次
                        self._rate_limit()
                        data = self.district_api.query(keywords=word, subdistrict=0)
                        if data["status"] == "1" and data["districts"]:
                            first_district = first_or_none(data["districts"])
                            if first_district:
                                adcode = first_district["adcode"]
                                logging.info(f"重试成功，找到城市 '{word}' 的adcode: {adcode}")
                                return adcode
                    except Exception as retry_e:
                        logging.error(f"重试失败: {retry_e}")
            except Exception as e:
                logging.error(f"查询城市 '{word}' 时发生错误: {e}")
                continue
        
        logging.warning(f"未找到任何城市关键词的adcode: {city_keywords}")
        return None

    # ------------ Step-3 兴趣词 → typecodes ------------
    def _get_types(self, interest_keywords: List[str]) -> str | None:
        """
        根据兴趣关键词获取POI分类码
        
        Args:
            interest_keywords: 兴趣关键词列表
            
        Returns:
            POI分类码字符串，用|分隔，或None
        """
        if not interest_keywords:
            return None
        
        types_param = interest_to_typecodes(interest_keywords)
        if types_param:
            logging.info(f"兴趣关键词 {interest_keywords} 解析为分类码: {types_param}")
        else:
            logging.warning(f"兴趣关键词 {interest_keywords} 未找到匹配的分类码")
        
        return types_param

    # ------------ Step-4 关键词检索 ------------
    def _search_pois(
        self, primary_keywords: List[str], types: str | None, adcode: str | None,
        *, avoid_keywords: List[str] | None = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        根据关键词搜索POI
        
        Args:
            primary_keywords: 主要搜索关键词列表
            types: POI分类码
            adcode: 行政区划代码
            avoid_keywords: 避雷关键词列表，来自LLM的avoid_keywords
            
        Returns:
            POI搜索结果字典
        """
        avoid_keywords = avoid_keywords or []
        # 如果你想同时按 typecode 排除火锅，可写：
        avoid_codes = ["050117"]  # 火锅店
        result = {}
        
        for kw in primary_keywords:
            try:
                kwargs = dict(keywords=kw, page_size=3)
                if types:
                    kwargs["types"] = types
                if adcode:
                    kwargs.update(region=adcode, city_limit=True)
                
                logging.info(f"搜索POI: {kwargs}")
                self._rate_limit()
                data = self.place_api.text_search(**kwargs)
                
                # 安全获取POI列表
                pois = data.get("pois", []) if data else []
                
                # --- 结果后过滤 ---
                pois = filter_by_avoid_words(
                    pois,
                    avoid_words=avoid_keywords,
                    avoid_codes=avoid_codes
                )
                
                result[kw] = pois
                logging.info(f"关键词 '{kw}' 找到 {len(result[kw])} 个POI (过滤后)")
                
            except AmapAPIError as e:
                logging.error(f"搜索关键词 '{kw}' 失败: {e}")
                result[kw] = [{"error": str(e)}]
            except Exception as e:
                logging.error(f"搜索关键词 '{kw}' 时发生错误: {e}")
                result[kw] = [{"error": f"搜索失败: {str(e)}"}]
        
        return result

    # ------------ Step-4 双循环搜索：关键词 × 兴趣类别 ------------
    def search_by_kw_and_code(
        self, 
        primary_keywords: List[str], 
        code_map: Dict[str, List[str]], 
        adcode: str | None = None,
        *, 
        avoid_keywords: List[str] | None = None
    ) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        """
        双循环搜索：关键词 × 兴趣类别
        
        Args:
            primary_keywords: 主要搜索关键词列表
            code_map: 分类码到关键词列表的映射
            adcode: 行政区划代码
            avoid_keywords: 避雷关键词列表
            
        Returns:
            双层嵌套的搜索结果：{keyword: {typecode: [poi_list]}}
        """
        avoid_keywords = avoid_keywords or []
        avoid_codes = ["050117"]  # 火锅店分类码
        results = {}
        
        for kw in primary_keywords:
            logging.info(f"搜索关键词: {kw}")
            bucket = {}
            
            for code, words in code_map.items():
                try:
                    kwargs = dict(
                        keywords=kw,
                        types=code,  # 单一typecode
                        page_size=3  # 减少单次请求数据量
                    )
                    if adcode:
                        kwargs.update(region=adcode, city_limit=True)
                    
                    logging.info(f"  搜索分类码 {code} ({', '.join(words)}): {kwargs}")
                    self._rate_limit()  # QPS控制
                    data = self.place_api.text_search(**kwargs)
                    
                    pois = data.get("pois", []) if data else []
                    
                    # 结果过滤
                    pois = filter_by_avoid_words(
                        pois,
                        avoid_words=avoid_keywords,
                        avoid_codes=avoid_codes
                    )
                    
                    if pois:  # 只保存非空结果
                        bucket[code] = pois
                        logging.info(f"    找到 {len(pois)} 个POI")
                    else:
                        logging.debug(f"    未找到POI")
                        
                except AmapAPIError as e:
                    logging.error(f"  搜索分类码 {code} 失败: {e}")
                    if "QPS" in str(e) or "10021" in str(e):
                        logging.warning(f"  QPS超限，等待更长时间...")
                        time.sleep(2.0)  # 额外等待2秒
                        try:
                            # 重试一次
                            self._rate_limit()
                            data = self.place_api.text_search(**kwargs)
                            pois = data.get("pois", []) if data else []
                            pois = filter_by_avoid_words(pois, avoid_words=avoid_keywords, avoid_codes=avoid_codes)
                            if pois:
                                bucket[code] = pois
                                logging.info(f"    重试成功，找到 {len(pois)} 个POI")
                            else:
                                logging.debug(f"    重试后仍未找到POI")
                        except Exception as retry_e:
                            logging.error(f"    重试失败: {retry_e}")
                            bucket[code] = [{"error": f"QPS超限重试失败: {str(retry_e)}"}]
                    else:
                        bucket[code] = [{"error": str(e)}]
                except Exception as e:
                    logging.error(f"  搜索分类码 {code} 时发生错误: {e}")
                    bucket[code] = [{"error": f"搜索失败: {str(e)}"}]
            
            results[kw] = bucket
            logging.info(f"关键词 '{kw}' 搜索完成，找到 {len(bucket)} 个分类")
        
        return results

    # ------------ 对外总入口 ------------
    def run(
        self,
        conversation: List[Dict[str, str]],
        session_info: Dict[str, Any] = None,
        llm_keywords: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """
        POI搜索管道主入口
        
        Args:
            conversation: 用户与 AI 的对话历史 (role/user/assistant结构)
            session_info: 会话信息，用于LLM上下文
            llm_keywords: 如果已经得到大模型 JSON，可直接传入，跳过 Step-1
            
        Returns:
            搜索结果字典
        """
        try:
            # 1) LLM 生成关键词
            keywords_json = llm_keywords or self._call_llm(conversation, session_info)
            logging.info(f"LLM生成的关键词: {keywords_json}")

            # 2) 获取行政区划代码
            adcode = self._get_adcode(keywords_json.get("city_keywords", []))
            if not adcode:
                logging.warning("未找到有效的行政区划代码，将进行全国范围搜索")

            # 3) 构建分类码映射
            code_map = build_code_map(keywords_json.get("interest_keywords", []))
            if not code_map:
                logging.warning("未找到匹配的POI分类码，将进行全类型搜索")

            # 4) 双循环POI搜索：关键词 × 兴趣类别
            pois = self.search_by_kw_and_code(
                keywords_json.get("primary_keywords", []), 
                code_map, 
                adcode,
                avoid_keywords=keywords_json.get("avoid_keywords", [])
            )

            result = {
                "query": keywords_json,
                "adcode": adcode,
                "code_map": code_map,
                "pois": pois,
            }
            
            # 计算总POI数量，忽略错误结果
            total_pois = 0
            for keyword_bucket in pois.values():
                for code_pois in keyword_bucket.values():
                    if code_pois and "error" not in code_pois[0]:
                        total_pois += len(code_pois)
            
            logging.info(f"POI搜索管道完成: adcode={adcode}, 分类数={len(code_map)}, 找到POI数量={total_pois}")
            
            return result
            
        except Exception as e:
            logging.error(f"POI搜索管道执行失败: {e}")
            return {
                "query": keywords_json if 'keywords_json' in locals() else {},
                "adcode": adcode if 'adcode' in locals() else None,
                "code_map": code_map if 'code_map' in locals() else {},
                "pois": pois if 'pois' in locals() else {},
                "error": str(e)
            }

    # ------------ 便捷方法 ------------
    def search_by_conversation(self, conversation: List[Dict[str, str]], session_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        根据对话历史搜索POI（便捷方法）
        
        Args:
            conversation: 对话历史
            session_info: 会话信息
            
        Returns:
            搜索结果
        """
        return self.run(conversation, session_info)
    
    def search_by_keywords(self, keywords: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据已生成的关键词搜索POI（便捷方法）
        
        Args:
            keywords: 已生成的关键词字典
            
        Returns:
            搜索结果
        """
        return self.run([], None, keywords)
    
    def get_search_summary(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取搜索结果摘要
        
        Args:
            result: 搜索结果
            
        Returns:
            摘要信息
        """
        summary = {
            "total_pois": 0,
            "keyword_results": {},
            "category_results": {},
            "success_rate": 0.0
        }
        
        pois = result.get("pois", {})
        code_map = result.get("code_map", {})
        total_keywords = len(pois)
        successful_keywords = 0
        
        # 按关键词统计
        for keyword, keyword_bucket in pois.items():
            keyword_total = 0
            keyword_valid = 0
            keyword_categories = {}
            
            for code, code_pois in keyword_bucket.items():
                # 过滤掉错误结果
                valid_pois = [poi for poi in code_pois if "error" not in poi]
                category_name = code_map.get(code, [code])[0] if code in code_map else code
                
                keyword_categories[code] = {
                    "name": category_name,
                    "total": len(code_pois),
                    "valid": len(valid_pois),
                    "sample_names": [poi.get("name", "未知") for poi in valid_pois[:2]]
                }
                
                keyword_total += len(code_pois)
                keyword_valid += len(valid_pois)
                summary["total_pois"] += len(valid_pois)
            
            summary["keyword_results"][keyword] = {
                "total": keyword_total,
                "valid": keyword_valid,
                "categories": keyword_categories
            }
            
            if keyword_valid > 0:
                successful_keywords += 1
        
        # 按分类统计
        for code, words in code_map.items():
            category_total = 0
            category_valid = 0
            
            for keyword_bucket in pois.values():
                if code in keyword_bucket:
                    code_pois = keyword_bucket[code]
                    valid_pois = [poi for poi in code_pois if "error" not in poi]
                    category_total += len(code_pois)
                    category_valid += len(valid_pois)
            
            summary["category_results"][code] = {
                "name": words[0] if words else code,
                "keywords": words,
                "total": category_total,
                "valid": category_valid
            }
        
        if total_keywords > 0:
            summary["success_rate"] = successful_keywords / total_keywords
        
        return summary


# ---------------- 结果过滤器 ----------------
def filter_by_avoid_words(
        pois: list[dict],
        avoid_words: list[str],
        avoid_codes: list[str] | None = None
) -> list[dict]:
    """
    根据避雷关键词 / typecode 过滤 POI 列表
    :param pois:  高德返回的 poi dict 列表
    :param avoid_words:  ["火锅", "hotpot", ...]
    :param avoid_codes:  ["050117", ...]   可选
    """
    avoid_words_lower = [w.lower() for w in avoid_words]
    avoid_codes = set(avoid_codes or [])
    keep: list[dict] = []

    for p in pois:
        name   = (p.get("name", "") or "").lower()
        tcodes = p.get("typecode", "")  # 可能是 "050117|110201..."
        # A. 名称中含避雷词？
        if any(w in name for w in avoid_words_lower):
            continue
        # B. typecode 命中避雷 code？
        if any(code for code in tcodes.split("|") if code in avoid_codes):
            continue
        keep.append(p)
    return keep 