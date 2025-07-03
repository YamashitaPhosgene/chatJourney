import logging
from typing import Dict, List, Optional, Any
from difflib import SequenceMatcher
from talker.models import TalkSession, POIItem, POISession
from hunter.api.amap_api import AmapPlaceAPI, AmapAPIError
from chatJourney import settings

logger = logging.getLogger(__name__)

class POIManagementService:
    """POI管理服务，统一处理POI基础信息和会话关联"""
    
    def __init__(self):
        self.amap_client = AmapPlaceAPI(key=settings.AMAP_KEY)
    
    def add_poi_from_search_result(self, session: TalkSession, poi_data: Dict[str, Any], source: str = 'keyword_search') -> bool:
        """
        添加POI到全局POIItem表，并建立POISession关联
        """
        try:
            name = poi_data.get('name', '')
            poi_id = poi_data.get('id', '')
            if not name or not poi_id:
                logger.warning("POI数据缺少名称或ID")
                return False
            # 1. 查找或新建POIItem
            poi_item, created = POIItem.objects.get_or_create(
                poi_id=poi_id,
                defaults={
                    'name': name,
                    'address': poi_data.get('address', ''),
                    'location': poi_data.get('location', ''),
                    'type': poi_data.get('type', ''),
                    'tel': poi_data.get('tel', ''),
                    'distance': poi_data.get('distance', ''),
                    'raw_data': poi_data
                }
            )
            # 2. 建立会话关联（去重）
            rel, rel_created = POISession.objects.get_or_create(
                session=session,
                poi=poi_item,
                defaults={'source': source}
            )
            if rel_created:
                logger.info(f"成功添加POI: {name} (来源: {source})")
            else:
                logger.info(f"POI已存在于会话: {name}")
            return True
        except Exception as e:
            logger.error(f"添加POI失败: {e}")
            return False
    
    def add_poi_from_locations(self, session: TalkSession) -> List[str]:
        """
        从session.locations逆搜索添加POI到数据库
        """
        added_pois = []
        locations = session.locations or []
        for location in locations:
            try:
                data = self.amap_client.text_search(keywords=location, page_size=1)
                poi_list = data.get("pois", []) if data else []
                if poi_list:
                    poi_data = poi_list[0]
                    if self.add_poi_from_search_result(session, poi_data, 'reverse_search'):
                        added_pois.append(poi_data.get('name', location))
            except AmapAPIError as e:
                logger.warning(f"高德API查询失败（{location}）：{e}")
            except Exception as e:
                logger.error(f"处理location失败（{location}）：{e}")
        return added_pois
    
    def get_session_pois(self, session: TalkSession, source: Optional[str] = None) -> List[POIItem]:
        """
        获取会话的所有POIItem（通过POISession关联）
        """
        rels = POISession.objects.filter(session=session)
        if source:
            rels = rels.filter(source=source)
        return [rel.poi for rel in rels.select_related('poi').order_by('-created_at')]
    
    def get_poi_by_name(self, session: TalkSession, name: str) -> Optional[POIItem]:
        """
        根据名称获取会话下的POIItem
        """
        rel = POISession.objects.filter(session=session, poi__name=name).select_related('poi').first()
        return rel.poi if rel else None
    
    def remove_poi(self, session: TalkSession, poi_id: int) -> bool:
        """
        删除会话下的POI关联（不删除全局POIItem）
        """
        try:
            rel = POISession.objects.filter(session=session, poi_id=poi_id).first()
            if rel:
                rel.delete()
                logger.info(f"成功删除POI关联: {rel.poi.name}")
                return True
            return False
        except Exception as e:
            logger.error(f"删除POI关联失败: {e}")
            return False
    
    def is_poi_similar(self, name1: str, name2: str, threshold: float = 0.7) -> bool:
        return SequenceMatcher(None, name1, name2).ratio() > threshold
    
    def get_poi_statistics(self, session: TalkSession) -> Dict[str, int]:
        total = POISession.objects.filter(session=session).count()
        manual = POISession.objects.filter(session=session, source='manual').count()
        reverse_search = POISession.objects.filter(session=session, source='reverse_search').count()
        keyword_search = POISession.objects.filter(session=session, source='keyword_search').count()
        return {
            'total': total,
            'manual': manual,
            'reverse_search': reverse_search,
            'keyword_search': keyword_search
        } 