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
    
    def add_poi_from_search_result(self, session: TalkSession, poi_data: Dict[str, Any], source: str = 'keyword_search') -> Dict[str, Any]:
        """
        添加POI到全局POIItem表，并建立POISession关联
        
        Returns:
            Dict[str, Any]: 包含操作结果的字典
            {
                'success': bool,  # 操作是否成功
                'exists': bool,   # POI是否已存在
                'message': str,   # 结果消息
                'poi_name': str   # POI名称
            }
        """
        try:
            logger.info(f"POI管理服务开始处理: poi_data={poi_data}, source={source}")
            
            name = poi_data.get('name', '')
            poi_id = poi_data.get('id', '')
            logger.info(f"提取POI基本信息: name={name}, poi_id={poi_id}")
            
            if not name or not poi_id:
                logger.warning(f"POI数据缺少名称或ID: name={name}, poi_id={poi_id}")
                return {
                    'success': False,
                    'exists': False,
                    'message': 'POI数据缺少名称或ID',
                    'poi_name': name
                }
            # 1. 查找或新建POIItem
            # 对于手动添加的POI，跳过搜索补全以避免不必要的API调用
            # 检查是否需要补全POI信息（缺少评分、图片或业务信息）
            photos = poi_data.get('photos', [])
            business = poi_data.get('business', {})
            score = poi_data.get('score')
            business_rating = business.get('rating') if business else None
            
            # 检查是否有评分信息（score字段或business.rating字段）
            # 注意：score可能为0，所以不能用 or 判断
            has_rating = (score is not None) or business_rating
            
            needs_completion = (
                source != 'manual' and 
                (not photos or not business or not has_rating)
            )
            
            if needs_completion:
                try:
                    logger.info(f"补全POI信息: {name} (来源: {source})")
                    detail = self.amap_client.text_search(
                        keywords=name,
                        page_size=1,
                        show_fields="children,business,indoor,navi,photos"
                    )
                    pois = detail.get('pois', [])
                    if pois:
                        poi_data = pois[0]
                        poi_data['__amap_raw_response__'] = detail
                        logger.info(f"补全POI信息成功: {name}, 评分: {poi_data.get('score', 'N/A')}, 图片数: {len(poi_data.get('photos', []))}")
                except Exception as e:
                    logger.warning(f"补全POI show_fields失败: {e}")
            elif source == 'manual':
                logger.info(f"手动添加POI，跳过搜索补全: {name}")
            else:
                logger.info(f"POI信息已完整，跳过补全: {name}")
            
            # 清理poi_data以避免循环引用
            clean_poi_data = self._clean_poi_data(poi_data)
            
            # 2. 查找或新建POIItem
            poi_item, created = POIItem.objects.get_or_create(
                poi_id=poi_id,
                defaults={
                    'name': name,
                    'address': poi_data.get('address', ''),
                    'location': poi_data.get('location', ''),
                    'type': poi_data.get('type', ''),
                    'tel': poi_data.get('tel', ''),
                    'distance': poi_data.get('distance', ''),
                    'raw_data': clean_poi_data
                }
            )
            # 3. 建立会话关联（去重）
            rel, rel_created = POISession.objects.get_or_create(
                session=session,
                poi=poi_item,
                defaults={'source': source}
            )
            if rel_created:
                logger.info(f"成功添加POI: {name} (来源: {source})")
                return {
                    'success': True,
                    'exists': False,
                    'message': f'成功添加POI: {name}',
                    'poi_name': name
                }
            else:
                logger.info(f"POI已存在于会话: {name}")
                return {
                    'success': True,
                    'exists': True,
                    'message': f'POI已存在于会话: {name}',
                    'poi_name': name
                }
        except Exception as e:
            logger.error(f"添加POI失败: {e}")
            return {
                'success': False,
                'exists': False,
                'message': f'添加POI失败: {str(e)}',
                'poi_name': name
            }
    
    def _clean_poi_data(self, poi_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        清理POI数据，移除可能导致循环引用的字段
        """
        import json
        import copy
        
        # 只保留我们需要的字段
        allowed_fields = {
            'id', 'name', 'address', 'location', 'type', 'tel', 'distance',
            'score', 'traffic', 'weather', 'image', 'typecode', 'business_area',
            'photos', 'pcode', 'adcode', 'citycode', 'alias', 'tag', 'website',
            'email', 'postcode', 'biz_type', 'indoor_map', 'indoor_data',
            'shopinfo', 'children', 'business', 'navi', 'timestamp'
        }
        
        try:
            # 创建一个只包含允许字段的字典
            cleaned_data = {}
            for key, value in poi_data.items():
                if key in allowed_fields:
                    # 对于复杂对象，尝试序列化测试
                    try:
                        json.dumps(value)
                        cleaned_data[key] = value
                    except (TypeError, ValueError):
                        # 如果无法序列化，转换为字符串
                        cleaned_data[key] = str(value)
                else:
                    logger.debug(f"跳过POI字段: {key}")
            
            return cleaned_data
        except Exception as e:
            logger.warning(f"清理POI数据失败: {e}")
            # 如果清理失败，返回基本信息
            return {
                'id': poi_data.get('id', ''),
                'name': poi_data.get('name', ''),
                'address': poi_data.get('address', ''),
                'location': poi_data.get('location', ''),
                'type': poi_data.get('type', ''),
                'tel': poi_data.get('tel', ''),
                'distance': poi_data.get('distance', '')
            }
    
    def add_poi_from_single_location(self, session: TalkSession, location: str) -> bool:
        """
        从单个location逆搜索添加POI到数据库
        """
        try:
            # 检查是否已经存在同名POI
            existing_poi = self.get_poi_by_name(session, location)
            if existing_poi:
                logger.info(f"POI已存在于会话中: {location}")
                return True
            
            # 直接使用完整的show_fields搜索，确保获取评分和图片信息
            data = self.amap_client.text_search(
                keywords=location, 
                page_size=1,
                show_fields="children,business,indoor,navi,photos"
            )
            poi_list = data.get("pois", []) if data else []
            if poi_list:
                poi_data = poi_list[0]
                result = self.add_poi_from_search_result(session, poi_data, 'reverse_search')
                if result['success']:
                    logger.info(f"成功逆搜索并添加POI: {poi_data.get('name', location)}")
                    return True
            logger.warning(f"未找到POI: {location}")
            return False
        except AmapAPIError as e:
            logger.warning(f"高德API查询失败（{location}）：{e}")
            return False
        except Exception as e:
            logger.error(f"处理location失败（{location}）：{e}")
            return False
    
    def add_poi_from_locations(self, session: TalkSession) -> List[str]:
        """
        从session.locations逆搜索添加POI到数据库
        """
        added_pois = []
        locations = session.locations or []
        for location in locations:
            try:
                # 直接使用完整的show_fields搜索，确保获取评分和图片信息
                data = self.amap_client.text_search(
                    keywords=location, 
                    page_size=1,
                    show_fields="children,business,indoor,navi,photos"
                )
                poi_list = data.get("pois", []) if data else []
                if poi_list:
                    poi_data = poi_list[0]
                    result = self.add_poi_from_search_result(session, poi_data, 'reverse_search')
                    if result['success']:
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