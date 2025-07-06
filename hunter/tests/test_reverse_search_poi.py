from django.test import TestCase
from unittest.mock import patch

from hunter.api.amap_api import AmapPlaceAPI
from talker.models import POIItem, POIKeywordCache


class ReverseSearchPOITestCase(TestCase):
    """验证 reverse_search_poi 首次调用写库、二次调用命中缓存"""

    @patch.object(AmapPlaceAPI, "text_search")
    def test_reverse_search_poi_cached(self, mock_text_search):
        # 准备伪造的高德返回数据
        mock_text_search.return_value = {
            "status": "1",
            "pois": [
                {
                    "id": "B_TEST_123",
                    "name": "测试酒店",
                    "address": "测试路 1 号",
                    "location": "116.1,39.2",
                    "type": "酒店",
                    "tel": "010-123456",
                    "distance": "100",
                }
            ],
        }

        api = AmapPlaceAPI(key="dummy-key")

        # 第一次调用：应创建 POIItem 与 POIKeywordCache
        poi_db_id_first = api.reverse_search_poi("测试酒店")
        self.assertIsNotNone(poi_db_id_first)
        self.assertEqual(POIItem.objects.count(), 1)
        self.assertEqual(POIKeywordCache.objects.count(), 1)
        cache = POIKeywordCache.objects.first()
        self.assertEqual(cache.hit_count, 1)

        # 重置 mock 调用次数
        mock_text_search.reset_mock()

        # 第二次调用：应命中缓存，不再调用 text_search，hit_count+1
        poi_db_id_second = api.reverse_search_poi("测试酒店")
        self.assertEqual(poi_db_id_first, poi_db_id_second)
        self.assertEqual(POIItem.objects.count(), 1)  # 不新增
        cache.refresh_from_db()
        self.assertEqual(cache.hit_count, 2)
        mock_text_search.assert_not_called() 