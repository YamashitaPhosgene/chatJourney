#!/usr/bin/env python
# encoding: utf-8

import json
import logging
from typing import Dict, Any, List, Optional
from django.conf import settings
from talker.models import TalkSession, POIItem
from talker.services.chat_service import ChatService
from sklearn.cluster import DBSCAN
from math import radians
import numpy as np
import re

class TimelineService:
    """行程链生成服务，替换route_time_service"""
    
    def __init__(self):
        self.chat_service = ChatService()
        self.logger = logging.getLogger(__name__)
    
    def generate_timeline(self, session: TalkSession) -> Dict[str, Any]:
        """
        生成完整的行程链
        
        Args:
            session: TalkSession对象
            
        Returns:
            Dict包含生成的行程链结构
        """
        try:
            # Stage 1: 用户画像整合
            self.logger.error("Stage 1: 开始用户画像整合")
            profile_data = self._stage_1_profile_consolidation(session)
            
            # 验证 Stage 1 返回的必需字段
            if 'radius_km' not in profile_data:
                raise ValueError("Stage 1 用户画像整合失败：缺少必需字段 'radius_km'")
            if 'user_profile_text' not in profile_data:
                raise ValueError("Stage 1 用户画像整合失败：缺少必需字段 'user_profile_text'")
            
            # Stage 1.5: 地理聚类
            self.logger.error("Stage 1.5: 开始地理聚类")
            clusters = self._stage_1_5_geographic_clustering(session, profile_data['radius_km'])
            
            # Stage 2: 旅行草案生成
            self.logger.error("Stage 2: 开始旅行草案生成")
            daily_itinerary = self._stage_2_itinerary_drafting(
                profile_data['user_profile_text'], 
                clusters
            )
            
            # Stage 3: 结构化行程评审
            self.logger.error("Stage 3: 开始结构化行程评审")
            review_feedback = self._stage_3_itinerary_review(
                profile_data['user_profile_text'],
                daily_itinerary
            )
            
            # Stage 3.5: 草案修订生成
            self.logger.error("Stage 3.5: 开始草案修订生成")
            revised_itinerary = self._stage_3_5_itinerary_revision(
                profile_data['user_profile_text'],
                daily_itinerary,
                review_feedback
            )
            
            # Stage 4: 链式结构生成
            self.logger.error("Stage 4: 开始链式结构生成")
            itinerary_chain = self._stage_4_chain_generation(revised_itinerary)
            
            # 组织返回结果
            result = {
                'success': True,
                'user_profile_text': profile_data['user_profile_text'],
                'radius_km': profile_data['radius_km'],
                'clusters': clusters,
                'daily_itinerary': daily_itinerary,
                'review_feedback': review_feedback,
                'revised_itinerary': revised_itinerary,
                'itinerary_chain': itinerary_chain,
                'final_text': revised_itinerary  # 用于前端显示的最终行程文本
            }
            
            self.logger.error("[TIMELINE] === ✅ Timeline生成成功 ===")
            self.logger.error(f"[TIMELINE] 最终结果包含字段: {list(result.keys())}")
            self.logger.error(f"[TIMELINE] 最终文本长度: {len(result['final_text'])} 字符")
            return result
            
        except Exception as e:
            self.logger.error(f"[TIMELINE] === ❌ Timeline生成失败 ===")
            self.logger.error(f"[TIMELINE] 错误信息: {e}")
            self.logger.error(f"[TIMELINE] 错误类型: {type(e).__name__}")
            import traceback
            self.logger.error(f"[TIMELINE] 完整错误堆栈: {traceback.format_exc()}")
            
            # 根据异常类型返回更具体的错误信息
            error_type = type(e).__name__
            if isinstance(e, RuntimeError):
                error_detail = f"服务调用错误: {str(e)}"
            elif isinstance(e, ValueError):
                error_detail = f"数据验证错误: {str(e)}"
            elif isinstance(e, KeyError):
                error_detail = f"数据字段缺失: {str(e)}"
            elif isinstance(e, json.JSONDecodeError):
                error_detail = f"JSON解析错误: {str(e)}"
            else:
                error_detail = f"未知错误 ({error_type}): {str(e)}"
            
            error_result = {
                'success': False,
                'error_type': error_type,
                'error': error_detail,
                'final_text': f"Timeline生成失败：{error_detail}"
            }
            return error_result
    
    def _stage_1_profile_consolidation(self, session: TalkSession) -> Dict[str, Any]:
        """Stage 1: 用户画像整合"""
        self.logger.error("[STAGE_1] === 用户画像整合阶段开始 ===")
        
        try:
            # 准备输入数据
            self.logger.error("[STAGE_1] 1. 提取会话槽位信息")
            collected_slots = self._extract_collected_slots(session)
            self.logger.error(f"[STAGE_1] 提取的槽位信息: {json.dumps(collected_slots, ensure_ascii=False)}")
            
            self.logger.error("[STAGE_1] 2. 提取官方POI名称")
            official_poi_names = self._extract_official_poi_names(session)
            self.logger.error(f"[STAGE_1] 提取的POI名称: {official_poi_names}")
            
            input_data = {
                "collected_slots": collected_slots,
                "official_poi_names": official_poi_names
            }
            
            self.logger.error(f"[STAGE_1] 3. 准备输入数据完成，数据大小: {len(json.dumps(input_data, ensure_ascii=False))} 字符")
            
            # 调用ChatService处理
            self.logger.error("[STAGE_1] 4. 调用ChatService进行用户画像整合")
            response = self.chat_service.process_chat(
                message="请进行用户画像整合",
                chat_type="profile_consolidation",
                collected_slots_with_official_names=json.dumps(input_data, ensure_ascii=False)
            )
            
            self.logger.error(f"[STAGE_1] 5. ChatService响应结构: {list(response.keys())}")
            
            # 检查是否为错误响应
            if 'error' in response:
                error_msg = response.get('message', '未知错误')
                error_code = response.get('code', -1)
                raise RuntimeError(f"ChatService调用失败 (code: {error_code}): {error_msg}")
            
            # 解析响应
            content = response.get('data', {}).get('content', '')
            self.logger.error(f"[STAGE_1] 6. 原始响应内容: {content}")
            
            if not content or content.strip() == '{}':
                raise RuntimeError("ChatService返回空内容或无效JSON")
            
            try:
                result = json.loads(content)
            except json.JSONDecodeError as e:
                raise RuntimeError(f"ChatService返回内容无法解析为JSON: {e}")
            
            self.logger.error(f"[STAGE_1] 7. 解析后的结果: {json.dumps(result, ensure_ascii=False)}")
            
            # 验证结果结构
            missing_fields = []
            if 'user_profile_text' not in result:
                missing_fields.append('user_profile_text')
            if 'radius_km' not in result:
                missing_fields.append('radius_km')
            
            if missing_fields:
                raise RuntimeError(f"ChatService返回数据缺少必需字段: {', '.join(missing_fields)}")
            
            self.logger.error("[STAGE_1] === 用户画像整合阶段完成 ===")
            return result
            
        except Exception as e:
            self.logger.error(f"[STAGE_1] ❌ 用户画像整合失败: {e}")
            self.logger.error(f"[STAGE_1] 错误类型: {type(e).__name__}")
            import traceback
            self.logger.error(f"[STAGE_1] 完整错误堆栈: {traceback.format_exc()}")
            # 重新抛出异常，不使用默认值
            raise
    
    def _stage_1_5_geographic_clustering(self, session: TalkSession, radius_km_text: str) -> List[Dict[str, Any]]:
        """Stage 1.5: 地理聚类"""
        self.logger.error("[STAGE_1.5] === 地理聚类阶段开始 ===")
        self.logger.error(f"[STAGE_1.5] 输入半径范围: {radius_km_text}")
        
        try:
            # 提取POI数据
            self.logger.error("[STAGE_1.5] 1. 从会话中提取POI数据")
            pois = self._extract_pois_from_session(session)
            self.logger.error(f"[STAGE_1.5] 提取到的POI数量: {len(pois)}")
            
            for i, poi in enumerate(pois):
                self.logger.error(f"[STAGE_1.5] POI {i+1}: 名称={poi['name']}, 坐标=({poi['lng']:.6f}, {poi['lat']:.6f})")
            
            if not pois:
                self.logger.error("[STAGE_1.5] ❌ 没有找到POI数据，无法进行地理聚类")
                raise ValueError("Stage 1.5 地理聚类失败：会话中没有找到有效的POI数据")
            
            if len(pois) == 1:
                # 只有一个POI，直接返回
                self.logger.error("[STAGE_1.5] 只有1个POI，直接返回单聚类")
                single_cluster = {
                    "id": 1,
                    "centroid": f"{pois[0]['lng']:.6f},{pois[0]['lat']:.6f}",
                    "places": [pois[0]['name']]
                }
                self.logger.error(f"[STAGE_1.5] 单聚类结果: {json.dumps(single_cluster, ensure_ascii=False)}")
                return [single_cluster]
            
            # 执行地理聚类
            self.logger.error("[STAGE_1.5] 2. 执行DBSCAN地理聚类算法")
            clusters = self._cluster_pois_stage_1_5(pois, radius_km_text)
            
            self.logger.error(f"[STAGE_1.5] 3. 聚类完成，生成{len(clusters)}个聚类")
            
            for i, cluster in enumerate(clusters):
                self.logger.error(f"[STAGE_1.5] 聚类 {i+1}: ID={cluster['id']}, 中心点={cluster['centroid']}, 包含{len(cluster['places'])}个地点")
                for place in cluster['places']:
                    self.logger.error(f"[STAGE_1.5]   - {place}")
            
            self.logger.error("[STAGE_1.5] === 地理聚类阶段完成 ===")
            return clusters
            
        except Exception as e:
            self.logger.error(f"[STAGE_1.5] ❌ 地理聚类失败: {e}")
            self.logger.error(f"[STAGE_1.5] 错误类型: {type(e).__name__}")
            import traceback
            self.logger.error(f"[STAGE_1.5] 错误堆栈: {traceback.format_exc()}")
            # 重新抛出异常，不返回空数组
            raise RuntimeError(f"Stage 1.5 地理聚类失败: {e}")
    
    def _stage_2_itinerary_drafting(self, user_profile_text: str, clusters: List[Dict[str, Any]]) -> str:
        """Stage 2: 旅行草案生成"""
        try:
            # 格式化聚类为每日分组
            daily_place_groups = self._format_clusters_to_daily_groups(clusters)
            
            # 调用ChatService处理
            response = self.chat_service.process_chat(
                message="请根据以下信息生成旅行草案",
                chat_type="itinerary_drafting",
                user_profile_text=user_profile_text,
                daily_place_groups=daily_place_groups
            )
            
            # 解析响应
            content = response.get('data', {}).get('content', '暂无行程安排')
            
            self.logger.info(f"旅行草案生成完成，长度: {len(content)}")
            return content
            
        except Exception as e:
            self.logger.error(f"旅行草案生成失败: {e}")
            import traceback
            self.logger.error(f"旅行草案生成失败，完整错误堆栈: {traceback.format_exc()}")
            raise RuntimeError(f"Stage 2 旅行草案生成失败: {e}")
    
    def _stage_3_itinerary_review(self, user_profile_text: str, daily_itinerary: str) -> str:
        """Stage 3: 结构化行程评审"""
        self.logger.error("[STAGE_3] === 结构化行程评审阶段开始 ===")
        self.logger.error(f"[STAGE_3] 输入用户画像长度: {len(user_profile_text)} 字符")
        self.logger.error(f"[STAGE_3] 输入行程草案长度: {len(daily_itinerary)} 字符")
        
        try:
            # 调用ChatService处理
            self.logger.error("[STAGE_3] 1. 调用ChatService进行结构化行程评审")
            self.logger.error(f"[STAGE_3] 待评审的行程草案预览: {daily_itinerary[:300]}...")
            
            response = self.chat_service.process_chat(
                daily_itinerary,
                chat_type="itinerary_review_structured",
                user_profile_text=user_profile_text,
                daily_itinerary=daily_itinerary
            )
            
            self.logger.error(f"[STAGE_3] 2. ChatService响应结构: {list(response.keys())}")
            
            # 解析响应
            content = response.get('data', {}).get('content', '行程评审暂无问题')
            self.logger.error(f"[STAGE_3] 3. 评审反馈内容长度: {len(content)} 字符")
            self.logger.error(f"[STAGE_3] 评审反馈内容预览: {content[:200]}...")
            
            # 分析评审反馈内容
            if '问题' in content or '建议' in content or '修改' in content:
                self.logger.error("[STAGE_3] 检测到评审建议，需要进行草案修订")
            else:
                self.logger.error("[STAGE_3] 评审通过，无明显改进建议")
            
            if len(content) < 20:
                self.logger.error("[STAGE_3] ⚠️ 警告: 评审反馈内容过短")
            
            self.logger.error("[STAGE_3] === 结构化行程评审阶段完成 ===")
            return content
            
        except Exception as e:
            self.logger.error(f"[STAGE_3] ❌ 结构化行程评审失败: {e}")
            self.logger.error(f"[STAGE_3] 错误类型: {type(e).__name__}")
            import traceback
            self.logger.error(f"[STAGE_3] 错误堆栈: {traceback.format_exc()}")
            # 重新抛出异常，不使用默认内容
            raise RuntimeError(f"Stage 3 结构化行程评审失败: {e}")
    
    def _stage_3_5_itinerary_revision(self, user_profile_text: str, original_itinerary: str, review_feedback: str) -> str:
        """Stage 3.5: 草案修订生成"""
        try:
            # 调用ChatService处理
            response = self.chat_service.process_chat(
                message="请根据评审反馈修订旅行草案",
                chat_type="itinerary_revision",
                user_profile_text=user_profile_text,
                original_itinerary=original_itinerary,
                review_feedback=review_feedback
            )
            
            # 解析响应
            content = response.get('data', {}).get('content', original_itinerary)
            
            self.logger.info(f"草案修订生成完成，长度: {len(content)}")
            return content
            
        except Exception as e:
            self.logger.error(f"草案修订生成失败: {e}")
            import traceback
            self.logger.error(f"草案修订生成失败，完整错误堆栈: {traceback.format_exc()}")
            raise RuntimeError(f"Stage 3.5 草案修订生成失败: {e}")
    
    def _stage_4_chain_generation(self, confirmed_itinerary: str) -> List[Dict[str, Any]]:
        """Stage 4: 链式结构生成"""
        try:
            # 调用ChatService处理
            response = self.chat_service.process_chat(
                message="请将以下旅行草案转换为链式结构",
                chat_type="itinerary_chain_generation",
                confirmed_itinerary=confirmed_itinerary
            )
            
            # 解析响应
            content = response.get('data', {}).get('content', '[]')

            # 若返回以 ``` 包裹，先去除代码块
            if isinstance(content, str) and content.strip().startswith('```'):
                # 删除开头的 ```json 或 ``` 以及结尾的 ```，保留中间 JSON
                content = re.sub(r'^```[a-zA-Z]*\n', '', content.strip())
                content = re.sub(r'\n```$', '', content).strip()

            result = json.loads(content)
            
            self.logger.info(f"链式结构生成完成，生成{len(result)}天行程")
            return result
            
        except Exception as e:
            self.logger.error(f"链式结构生成失败: {e}")
            import traceback
            self.logger.error(f"链式结构生成失败，完整错误堆栈: {traceback.format_exc()}")
            raise RuntimeError(f"Stage 4 链式结构生成失败: {e}")
    
    def _extract_collected_slots(self, session: TalkSession) -> Dict[str, Any]:
        """从TalkSession中提取槽位信息"""
        self.logger.error("[EXTRACT] === 提取会话槽位信息 ===")
        slots = {}
        
        # 提取目的地
        if session.locations:
            slots['locations'] = session.locations
            self.logger.error(f"[EXTRACT] 目的地: {session.locations}")
        else:
            self.logger.error("[EXTRACT] 目的地: 未设置")
        
        # 提取预算
        if session.budget:
            slots['budget'] = session.budget
            self.logger.error(f"[EXTRACT] 预算: {session.budget}")
        else:
            self.logger.error("[EXTRACT] 预算: 未设置")
        
        # 提取日期
        if session.start_date and session.end_date:
            # 安全处理日期类型，避免 isoformat 错误
            def safe_isoformat(date_val):
                if hasattr(date_val, 'isoformat'):
                    return date_val.isoformat()
                return str(date_val)
            
            start_iso = safe_isoformat(session.start_date)
            end_iso = safe_isoformat(session.end_date)
            
            slots['dates'] = {
                'start_date': start_iso,
                'end_date': end_iso
            }
            self.logger.error(f"[EXTRACT] 日期: {start_iso} 至 {end_iso}")
        else:
            self.logger.error("[EXTRACT] 日期: 未设置")
        
        # 提取用户画像
        if session.user_profile:
            slots['user_profile'] = session.user_profile
            self.logger.error(f"[EXTRACT] 用户画像: {str(session.user_profile)[:100]}...")
        else:
            self.logger.error("[EXTRACT] 用户画像: 未设置")
        
        self.logger.error(f"[EXTRACT] 总计提取到 {len(slots)} 个槽位")
        return slots
    
    def _extract_official_poi_names(self, session: TalkSession) -> List[str]:
        """提取官方POI名称列表"""
        poi_names = []
        
        # 从POISession关联中提取POI数据
        from talker.models import POISession
        poi_sessions = POISession.objects.filter(session=session).select_related('poi')
        
        for poi_session in poi_sessions:
            poi_item = poi_session.poi
            if poi_item.name:
                poi_names.append(poi_item.name)
        
        # 从locations中提取
        if session.locations:
            if isinstance(session.locations, list):
                poi_names.extend(session.locations)
            else:
                poi_names.append(str(session.locations))
        
        # 去重
        return list(set(poi_names))
    
    def _extract_pois_from_session(self, session: TalkSession) -> List[Dict[str, Any]]:
        """从TalkSession中提取POI数据"""
        self.logger.error("[EXTRACT_POI] === 提取POI数据 ===")
        pois = []
        
        # 从POISession关联中提取POI数据
        from talker.models import POISession
        poi_sessions = POISession.objects.filter(session=session).select_related('poi')
        self.logger.error(f"[EXTRACT_POI] 找到 {poi_sessions.count()} 个POISession关联")
        
        for i, poi_session in enumerate(poi_sessions):
            poi_item = poi_session.poi
            self.logger.error(f"[EXTRACT_POI] POI {i+1}: 名称={poi_item.name}, 位置={poi_item.location}")
            
            if poi_item.location:
                try:
                    # location字段格式为"lng,lat"
                    lng_str, lat_str = poi_item.location.split(',')
                    poi_data = {
                        'name': poi_item.name,
                        'lng': float(lng_str),
                        'lat': float(lat_str)
                    }
                    pois.append(poi_data)
                    self.logger.error(f"[EXTRACT_POI] ✅ 成功解析: {poi_data}")
                except (ValueError, AttributeError) as e:
                    self.logger.error(f"[EXTRACT_POI] ❌ POI {poi_item.name} 位置信息格式错误: {poi_item.location}, 错误: {e}")
        
        # 如果没有POI坐标数据，从locations创建模拟数据
        if not pois and session.locations:
            self.logger.error("[EXTRACT_POI] 没有找到有效POI数据，使用locations创建模拟数据")
            locations = session.locations if isinstance(session.locations, list) else [session.locations]
            self.logger.error(f"[EXTRACT_POI] locations数据: {locations}")
            
            for i, dest in enumerate(locations):
                # 创建模拟坐标（实际应用中应从地图API获取）
                mock_poi = {
                    'name': str(dest),
                    'lng': 104.06 + i * 0.01,  # 成都市中心附近的模拟坐标
                    'lat': 30.67 + i * 0.01
                }
                pois.append(mock_poi)
                self.logger.error(f"[EXTRACT_POI] 📍 创建模拟POI: {mock_poi}")
        
        self.logger.error(f"[EXTRACT_POI] === 总计提取到 {len(pois)} 个POI数据 ===")
        return pois
    
    def _parse_radius_range(self, text: str) -> tuple:
        """解析半径范围"""
        if "-" in text:
            low, high = map(float, text.split("-"))
            return low, high
        val = float(text)
        return val * 0.8, val * 1.2
    
    def _dbscan_haversine(self, pois: List[Dict[str, Any]], eps_km: float) -> np.ndarray:
        """使用DBSCAN进行地理聚类"""
        coords = np.array([[radians(p['lat']), radians(p['lng'])] for p in pois])
        model = DBSCAN(
            eps=eps_km / 6371.0,  # 地球半径
            min_samples=1,
            metric='haversine'
        ).fit(coords)
        return model.labels_
    
    def _build_clusters(self, pois: List[Dict[str, Any]], labels: np.ndarray) -> List[Dict[str, Any]]:
        """构建聚类结果"""
        clusters = {}
        for idx, label in enumerate(labels):
            p = pois[idx]
            if label not in clusters:
                clusters[label] = {"places": [], "lngs": [], "lats": []}
            clusters[label]["places"].append(p["name"])
            clusters[label]["lngs"].append(p["lng"])
            clusters[label]["lats"].append(p["lat"])
        
        result = []
        cid = 1
        for c in clusters.values():
            avg_lng = sum(c["lngs"]) / len(c["lngs"])
            avg_lat = sum(c["lats"]) / len(c["lats"])
            result.append({
                "id": cid,
                "centroid": f"{avg_lng:.6f},{avg_lat:.6f}",
                "places": c["places"]
            })
            cid += 1
        return result
    
    def _cluster_pois_stage_1_5(self, pois: List[Dict[str, Any]], radius_km_text: str, 
                               target_min: int = 2, target_max: int = 5, max_iter: int = 5) -> List[Dict[str, Any]]:
        """Stage 1.5的地理聚类实现"""
        self.logger.error(f"[CLUSTER] === 开始自适应地理聚类 ===")
        self.logger.error(f"[CLUSTER] POI数量: {len(pois)}")
        self.logger.error(f"[CLUSTER] 目标聚类范围: {target_min}-{target_max}")
        
        low, high = self._parse_radius_range(radius_km_text)
        radius = (low + high) / 2
        self.logger.error(f"[CLUSTER] 半径范围解析: {low}-{high} km，初始半径: {radius:.2f} km")
        
        iteration = 0
        for iteration in range(max_iter):
            self.logger.error(f"[CLUSTER] 迭代 {iteration+1}/{max_iter}, 当前半径: {radius:.2f} km")
            
            labels = self._dbscan_haversine(pois, radius)
            n_clusters = len(set(labels))
            unique_labels = set(labels)
            
            self.logger.error(f"[CLUSTER] DBSCAN结果: {n_clusters} 个聚类, 标签: {unique_labels}")
            
            if target_min <= n_clusters <= target_max:
                self.logger.error(f"[CLUSTER] ✅ 找到最优聚类数: {n_clusters}")
                break
            
            if n_clusters < target_min:
                old_radius = radius
                radius = max(low, radius * 0.7)
                self.logger.error(f"[CLUSTER] 聚类数过少 ({n_clusters} < {target_min}), 减小半径: {old_radius:.2f} → {radius:.2f}")
            elif n_clusters > target_max:
                old_radius = radius
                radius = min(high, radius * 1.5)
                self.logger.error(f"[CLUSTER] 聚类数过多 ({n_clusters} > {target_max}), 增大半径: {old_radius:.2f} → {radius:.2f}")
        
        final_clusters = self._build_clusters(pois, labels)
        self.logger.error(f"[CLUSTER] === 聚类完成，{iteration+1}次迭代，生成{len(final_clusters)}个聚类 ===")
        
        return final_clusters
    
    def _format_clusters_to_daily_groups(self, clusters: List[Dict[str, Any]]) -> str:
        """格式化聚类为每日分组文本"""
        lines = []
        for i, cluster in enumerate(clusters, start=1):
            lines.append(f"Day {i}:")
            for place in cluster["places"]:
                lines.append(f"  - {place}")
        return "\n".join(lines)
    
    def format_timeline_for_display(self, timeline_data: Dict[str, Any]) -> str:
        """格式化timeline数据用于前端显示"""
        if not timeline_data.get('success'):
            return timeline_data.get('final_text', '行程生成失败')
        
        # 返回最终的行程文本
        return timeline_data.get('final_text', '暂无行程安排')
    
    def get_timeline_chain(self, timeline_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """获取结构化的行程链数据"""
        if not timeline_data.get('success'):
            return []
        
        return timeline_data.get('itinerary_chain', []) 