import sys
import os
import traceback
import json
import requests

# 获取当前文件所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatJourney.settings')
import django
django.setup()
from django.conf import settings

from hunter.api.amap_api import (
    AmapDirectionAPI,
    AmapPlaceAPI,
    AmapDistrictAPI,
    AmapAPIError
)

# 从 settings 中读取 Key
AMAP_KEY = getattr(settings, 'AMAP_KEY', None)
if not AMAP_KEY:
    raise ValueError("请在 .env 文件中配置 AMAP_KEY 环境变量")

# 实例化 API 客户端
direction_api = AmapDirectionAPI(key=AMAP_KEY)
place_api = AmapPlaceAPI(key=AMAP_KEY)
district_api = AmapDistrictAPI(key=AMAP_KEY)

# —— 在这里统一定义所有坐标 —— #
ORIGIN      = "116.233120,40.217515"
WAYPOINTS   = "116.303969,39.982066"
DESTINATION = "116.419387,39.928353"

# 简化调用并捕获异常
def debug_call(name, func, *args, **kwargs):
    print(f"→ 调用 {name}，args={args}, kwargs={kwargs}")
    try:
        return func(*args, **kwargs)
    except Exception as e:
        print(f"{name} 调用异常: {e}")
        traceback.print_exc()
        return None

# 持久化结果
def save_json(filename, data):
    with open(os.path.join(project_root, filename), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 时间格式化
def format_duration(sec: int) -> str:
    h, rem = divmod(sec, 3600)
    m, s   = divmod(rem, 60)
    parts = []
    if h:
        parts.append(f"{h}小时")
    if m:
        parts.append(f"{m}分")
    if s or not parts:
        parts.append(f"{s}秒")
    return ''.join(parts)

def get_adcode(place_name: str) -> str:
    """
    返回 place_name 对应的行政区 adcode（如：'110108'）。
    如果未查到，抛出 AmapAPIError 或返回 None。
    """
    try:
        resp = district_api.query(
            keywords=place_name,
            subdistrict=0,      # 不返回下级区域
            extensions="base"   # 不需要边界坐标
        )
        districts = resp.get("districts", [])
        if not districts:
            return None
        return districts[0].get("adcode")
    except AmapAPIError as e:
        print(f"查询失败：{e}")
        return None

def main():
    results = {}

    # —— 路径规划调用 —— #
    results['walking'] = debug_call(
        'walking',
        direction_api.walking,
        origin=ORIGIN,
        destination=DESTINATION
    )
    results['transit'] = debug_call(
        'transit',
        direction_api.transit,
        origin=ORIGIN,
        destination=DESTINATION,
        city='010'
    )
    results['driving'] = debug_call(
        'driving',
        direction_api.driving,
        origin=ORIGIN,
        destination=DESTINATION,
        waypoints=WAYPOINTS,
        extensions='base'
    )
    results['bicycling'] = debug_call(
        'bicycling',
        direction_api.bicycling,
        origin=ORIGIN,
        destination=DESTINATION
    )
    results['distance'] = debug_call(
        'distance',
        direction_api.distance,
        origins=[ORIGIN],
        destination=DESTINATION
    )

    # 保存路径规划结果
    save_json('amap_directions.json', results)

    # —— v5 POI 搜索调用 —— #
    place_results = {}

    # 关键字搜索: 搜索海淀区政府附近的肯德基
    place_results['text_search'] = debug_call(
        'text_search',
        place_api.text_search,
        keywords='肯德基',
        region='110108',
        city_limit=True,
        page_size=5,
        show_fields='business,children'
    )

    # 周边搜索: ORIGIN 周边 2000m 餐饮服务
    place_results['around_search'] = debug_call(
        'around_search',
        place_api.around_search,
        location=ORIGIN,
        types='050000',
        radius=2000,
        page_size=5
    )

    # 多边形搜索: 示例多边形
    place_results['polygon_search'] = debug_call(
        'polygon_search',
        place_api.polygon_search,
        polygon='116.460988,40.006919|116.48231,40.007381|116.47516,39.99713|116.460988,40.006919',
        keywords='咖啡馆',
        page_size=5
    )

    # ID 查询: 单个 POI 详情
    place_results['detail_search'] = debug_call(
        'detail_search',
        place_api.detail_search,
        poi_id='B0FFFAB6J2',
        show_fields='parking_type,indoor_map'
    )

    # 保存 POI 搜索结果
    save_json('amap_places.json', place_results)

    # —— 输出最短耗时 —— #
    try:
        print("最短步行耗时：", format_duration(direction_api.shortest_walking_duration(ORIGIN, DESTINATION)))
        print("最短公交耗时：", format_duration(direction_api.shortest_transit_duration(ORIGIN, DESTINATION, city='010')))
        print("最短驾车耗时：", format_duration(direction_api.shortest_driving_duration(ORIGIN, DESTINATION, waypoints=WAYPOINTS)))
        print("最短骑行耗时：", format_duration(direction_api.shortest_bicycling_duration(ORIGIN, DESTINATION)))
    except AmapAPIError as e:
        print("获取最短耗时时发生错误:", e)

if __name__ == '__main__':
    for name in ["海淀区政府", "天安门", "五道口"]:
        code = get_adcode(name)
        print(f"{name} 的 adcode = {code}")
