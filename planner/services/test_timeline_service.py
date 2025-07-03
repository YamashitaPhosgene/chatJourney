import os
import django
import datetime as dt

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatJourney.settings')
django.setup()

from talker.models import TalkSession, POIItem, POISession
from planner.services.timeline_service import TimelineService
from hunter.api.amap_api import AmapPlaceAPI, AmapDirectionAPI

# 请根据实际情况填写API KEY
AMAP_KEY = os.environ.get('AMAP_KEY', 'your_amap_key_here')

# 构造模拟会话和POI
user_profile = {"兴趣爱好": ["美食", "自驾游"]}

# 假设数据库已有POIItem，或你可以手动创建几个POIItem
# 这里只演示如何调用服务

def test_timeline_with_transfer():
    # 1. 获取一个TalkSession（请替换为实际ID）
    session = TalkSession.objects.first()
    if not session:
        print("请先在数据库中创建TalkSession和POIItem，并建立POISession关联！")
        return
    # 2. 初始化服务
    place_api = AmapPlaceAPI(AMAP_KEY)
    dir_api = AmapDirectionAPI(AMAP_KEY)
    service = TimelineService(place_api, dir_api)
    # 3. 生成timeline
    slots = service.build_timeline(session)
    # 4. 打印结果
    for slot in slots:
        print(f"{slot.start.strftime('%Y-%m-%d %H:%M')} - {slot.end.strftime('%H:%M')} | {slot.type} | {slot.title}")
        if slot.type == 'transfer':
            print("  (交通slot已自动插入)")

if __name__ == '__main__':
    test_timeline_with_transfer() 