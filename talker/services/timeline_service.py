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
            self.logger.info("Stage 1: 开始用户画像整合")
            profile_data = self._stage_1_profile_consolidation(session)
            
            # Stage 1.5: 地理聚类
            self.logger.info("Stage 1.5: 开始地理聚类")
            clusters = self._stage_1_5_geographic_clustering(session, profile_data['radius_km'])
            
            # Stage 2: 旅行草案生成
            self.logger.info("Stage 2: 开始旅行草案生成")
            daily_itinerary = self._stage_2_itinerary_drafting(
                profile_data['user_profile_text'], 
                clusters
            )
            
            # Stage 3: 结构化行程评审
            self.logger.info("Stage 3: 开始结构化行程评审")
            review_feedback = self._stage_3_itinerary_review(
                profile_data['user_profile_text'],
                daily_itinerary
            )
            
            # Stage 3.5: 草案修订生成
            self.logger.info("Stage 3.5: 开始草案修订生成")
            revised_itinerary = self._stage_3_5_itinerary_revision(
                profile_data['user_profile_text'],
                daily_itinerary,
                review_feedback
            )
            
            # Stage 4: 链式结构生成
            self.logger.info("Stage 4: 开始链式结构生成")
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
            
            self.logger.info("Timeline生成成功")
            return result
            
        except Exception as e:
            self.logger.error(f"Timeline生成失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'final_text': f"行程生成过程中遇到问题: {e}"
            }
    
    def _stage_1_profile_consolidation(self, session: TalkSession) -> Dict[str, Any]:
        """Stage 1: 用户画像整合"""
        try:
            # 准备输入数据
            collected_slots = self._extract_collected_slots(session)
            official_poi_names = self._extract_official_poi_names(session)
            
            input_data = {
                "collected_slots": collected_slots,
                "official_poi_names": official_poi_names
            }
            
            # 调用ChatService处理
            response = self.chat_service.process_chat(
                json.dumps(input_data, ensure_ascii=False),
                chat_type="profile_consolidation"
            )
            
            # 解析响应
            content = response.get('data', {}).get('content', '{}')
            result = json.loads(content)
            
            self.logger.info(f"用户画像整合完成: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"用户画像整合失败: {e}")
            # 返回默认值
            return {
                "user_profile_text": "用户计划进行一次旅行，希望体验当地文化和美食。",
                "radius_km": "3-5"
            }
    
    def _stage_1_5_geographic_clustering(self, session: TalkSession, radius_km_text: str) -> List[Dict[str, Any]]:
        """Stage 1.5: 地理聚类"""
        try:
            # 提取POI数据
            pois = self._extract_pois_from_session(session)
            
            if not pois:
                self.logger.warning("没有找到POI数据，跳过地理聚类")
                return []
            
            if len(pois) == 1:
                # 只有一个POI，直接返回
                return [{
                    "id": 1,
                    "centroid": f"{pois[0]['lng']:.6f},{pois[0]['lat']:.6f}",
                    "places": [pois[0]['name']]
                }]
            
            # 执行地理聚类
            clusters = self._cluster_pois_stage_1_5(pois, radius_km_text)
            
            self.logger.info(f"地理聚类完成，生成{len(clusters)}个聚类")
            return clusters
            
        except Exception as e:
            self.logger.error(f"地理聚类失败: {e}")
            return []
    
    def _stage_2_itinerary_drafting(self, user_profile_text: str, clusters: List[Dict[str, Any]]) -> str:
        """Stage 2: 旅行草案生成"""
        try:
            # 格式化聚类为每日分组
            daily_place_groups = self._format_clusters_to_daily_groups(clusters)
            
            # 调用ChatService处理
            response = self.chat_service.process_chat(
                daily_place_groups,
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
            return "行程草案生成过程中遇到问题，请稍后重试。"
    
    def _stage_3_itinerary_review(self, user_profile_text: str, daily_itinerary: str) -> str:
        """Stage 3: 结构化行程评审"""
        try:
            # 调用ChatService处理
            response = self.chat_service.process_chat(
                daily_itinerary,
                chat_type="itinerary_review_structured",
                user_profile_text=user_profile_text,
                daily_itinerary=daily_itinerary
            )
            
            # 解析响应
            content = response.get('data', {}).get('content', '行程评审暂无问题')
            
            self.logger.info(f"结构化行程评审完成，长度: {len(content)}")
            return content
            
        except Exception as e:
            self.logger.error(f"结构化行程评审失败: {e}")
            return "行程评审过程中遇到问题，建议保持原方案。"
    
    def _stage_3_5_itinerary_revision(self, user_profile_text: str, original_itinerary: str, review_feedback: str) -> str:
        """Stage 3.5: 草案修订生成"""
        try:
            # 调用ChatService处理
            response = self.chat_service.process_chat(
                review_feedback,
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
            return original_itinerary  # 返回原始草案
    
    def _stage_4_chain_generation(self, confirmed_itinerary: str) -> List[Dict[str, Any]]:
        """Stage 4: 链式结构生成"""
        try:
            # 调用ChatService处理
            response = self.chat_service.process_chat(
                confirmed_itinerary,
                chat_type="itinerary_chain_generation",
                confirmed_itinerary=confirmed_itinerary
            )
            
            # 解析响应
            content = response.get('data', {}).get('content', '[]')
            result = json.loads(content)
            
            self.logger.info(f"链式结构生成完成，生成{len(result)}天行程")
            return result
            
        except Exception as e:
            self.logger.error(f"链式结构生成失败: {e}")
            return []
    
    def _extract_collected_slots(self, session: TalkSession) -> Dict[str, Any]:
        """从TalkSession中提取槽位信息"""
        slots = {}
        
        # 提取目的地
        if session.locations:
            slots['locations'] = session.locations
        
        # 提取预算
        if session.budget:
            slots['budget'] = session.budget
        
        # 提取日期
        if session.start_date and session.end_date:
            slots['dates'] = {
                'start_date': session.start_date.isoformat(),
                'end_date': session.end_date.isoformat()
            }
        
        # 提取用户画像
        if session.user_profile:
            slots['user_profile'] = session.user_profile
        
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
        pois = []
        
        # 从POISession关联中提取POI数据
        from talker.models import POISession
        poi_sessions = POISession.objects.filter(session=session).select_related('poi')
        
        for poi_session in poi_sessions:
            poi_item = poi_session.poi
            if poi_item.location:
                try:
                    # location字段格式为"lng,lat"
                    lng_str, lat_str = poi_item.location.split(',')
                    pois.append({
                        'name': poi_item.name,
                        'lng': float(lng_str),
                        'lat': float(lat_str)
                    })
                except (ValueError, AttributeError):
                    self.logger.warning(f"POI {poi_item.name} 位置信息格式错误: {poi_item.location}")
        
        # 如果没有POI坐标数据，从locations创建模拟数据
        if not pois and session.locations:
            locations = session.locations if isinstance(session.locations, list) else [session.locations]
            for i, dest in enumerate(locations):
                # 创建模拟坐标（实际应用中应从地图API获取）
                pois.append({
                    'name': str(dest),
                    'lng': 104.06 + i * 0.01,  # 成都市中心附近的模拟坐标
                    'lat': 30.67 + i * 0.01
                })
        
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
        low, high = self._parse_radius_range(radius_km_text)
        radius = (low + high) / 2
        
        for _ in range(max_iter):
            labels = self._dbscan_haversine(pois, radius)
            n_clusters = len(set(labels))
            
            if target_min <= n_clusters <= target_max:
                break
            
            if n_clusters < target_min:
                radius = max(low, radius * 0.7)
            elif n_clusters > target_max:
                radius = min(high, radius * 1.5)
        
        return self._build_clusters(pois, labels)
    
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