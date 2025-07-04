# Updated amap_api.py with helper methods added

import requests
import threading
import time

class AmapAPIError(Exception):
    """Custom exception for Amap API errors."""
    pass

class AmapDirectionAPI:
    BASE_URL = "https://restapi.amap.com"

    def __init__(self, key, session=None, timeout=10):
        self.key = key
        self.session = session or requests.Session()
        self.timeout = timeout

    def walking(self, origin, destination, origin_id=None, destination_id=None, **kwargs):
        """步行路径规划，返回完整 JSON."""
        output = kwargs.pop("output", "JSON")
        params = {
            "key": self.key,
            "origin": origin,
            "destination": destination,
            "output": output,
        }
        if origin_id is not None: params["origin_id"] = origin_id
        if destination_id is not None: params["destination_id"] = destination_id
        params.update(kwargs)

        resp = self.session.get(
            f"{self.BASE_URL}/v3/direction/walking",
            params=params,
            timeout=self.timeout
        )
        j = resp.json()
        if j.get("status") != "1":
            raise AmapAPIError(f"Walking error: {j.get('info')}")
        if "route" not in j or "paths" not in j["route"]:
            raise AmapAPIError("Walking response missing 'route.paths'")
        return j

    def walking_paths(self, origin, destination, origin_id=None, destination_id=None, **kwargs):
        """直接返回步行方案列表 route.paths."""
        data = self.walking(origin, destination, origin_id=origin_id, destination_id=destination_id, **kwargs)
        return data["route"]["paths"]

    def transit(self, origin, destination, city, **kwargs):
        """公交路径规划，返回完整 JSON."""
        output = kwargs.pop("output", "JSON")
        params = {
            "key": self.key,
            "origin": origin,
            "destination": destination,
            "city": city,
            "output": output,
        }
        params.update(kwargs)

        resp = self.session.get(
            f"{self.BASE_URL}/v3/direction/transit/integrated",
            params=params,
            timeout=self.timeout
        )
        j = resp.json()
        if j.get("status") != "1":
            raise AmapAPIError(f"Transit error: {j.get('info')}")
        if "route" not in j or "transits" not in j["route"]:
            raise AmapAPIError("Transit response missing 'route.transits'")
        return j

    def transit_plans(self, origin, destination, city, **kwargs):
        """直接返回公交换乘方案列表 route.transits."""
        data = self.transit(origin, destination, city, **kwargs)
        return data["route"]["transits"]

    def driving(self, origin, destination, **kwargs):
        """驾车路径规划，返回完整 JSON."""
        kwargs.pop("output", None)  # avoid duplicates
        extensions = kwargs.pop("extensions", "base")
        params = {
            "key": self.key,
            "origin": origin,
            "destination": destination,
            "extensions": extensions,
        }
        params.update(kwargs)

        resp = self.session.get(
            f"{self.BASE_URL}/v3/direction/driving",
            params=params,
            timeout=self.timeout
        )
        j = resp.json()
        if j.get("status") != "1":
            raise AmapAPIError(f"Driving error: {j.get('info')}")
        if "route" not in j or "paths" not in j["route"]:
            raise AmapAPIError("Driving response missing 'route.paths'")
        return j

    def driving_paths(self, origin, destination, **kwargs):
        """直接返回驾车方案列表 route.paths."""
        data = self.driving(origin, destination, **kwargs)
        return data["route"]["paths"]

    def bicycling(self, origin, destination, **kwargs):
        """骑行路径规划，返回完整 JSON."""
        params = {
            "key": self.key,
            "origin": origin,
            "destination": destination,
        }
        params.update(kwargs)

        resp = self.session.get(
            f"{self.BASE_URL}/v4/direction/bicycling",
            params=params,
            timeout=self.timeout
        )
        j = resp.json()
        if j.get("errcode") != 0:
            raise AmapAPIError(f"Bicycling error: {j.get('errmsg')}")
        if "data" not in j or "paths" not in j["data"]:
            raise AmapAPIError("Bicycling response missing 'data.paths'")
        return j

    def bicycling_paths(self, origin, destination, **kwargs):
        """直接返回骑行方案列表 data.paths."""
        data = self.bicycling(origin, destination, **kwargs)
        return data["data"]["paths"]

    def distance(self, origins, destination, type_=1, **kwargs):
        """距离测量 API，返回完整 JSON."""
        origins_param = "|".join(origins) if isinstance(origins, (list, tuple)) else origins
        params = {
            "key": self.key,
            "origins": origins_param,
            "destination": destination,
            "type": type_,
        }
        params.update(kwargs)

        resp = self.session.get(
            f"{self.BASE_URL}/v3/distance",
            params=params,
            timeout=self.timeout
        )
        j = resp.json()
        if j.get("status") != "1":
            raise AmapAPIError(f"Distance error: {j.get('info')}")
        if "results" not in j:
            raise AmapAPIError("Distance response missing 'results'")
        return j

    def distance_results(self, origins, destination, type_=1, **kwargs):
        """直接返回距离测量结果列表 results."""
        data = self.distance(origins, destination, type_, **kwargs)
        return data["results"]

    # 最短耗时工具方法
    def shortest_walking_duration(self, origin, destination, **kwargs) -> int:
        """返回起点→终点的步行最短耗时（秒）。"""
        paths = self.walking_paths(origin, destination, **kwargs)
        return min(int(p["duration"]) for p in paths)

    def shortest_transit_duration(self, origin, destination, city, **kwargs) -> int:
        """返回起点→终点的公交换乘最短耗时（秒）。"""
        plans = self.transit_plans(origin, destination, city, **kwargs)
        return min(int(t["duration"]) for t in plans)

    def shortest_driving_duration(self, origin, destination, **kwargs) -> int:
        """返回起点→终点的驾车最短耗时（秒）。"""
        paths = self.driving_paths(origin, destination, **kwargs)
        return min(int(p["duration"]) for p in paths)

    def shortest_bicycling_duration(self, origin, destination, **kwargs) -> int:
        """返回起点→终点的骑行最短耗时（秒）。"""
        paths = self.bicycling_paths(origin, destination, **kwargs)
        return min(int(p["duration"]) for p in paths)

    # 可选：通用接口，你也可以用一个方法根据 mode 调用上面任意一种
    def shortest_duration(self, mode, *args, **kwargs) -> int:
        """
        通用方法，mode 可为 'walking'、'transit'、'driving'、'bicycling'
        其它参数与对应接口一致。
        """
        if mode == "walking":
            return self.shortest_walking_duration(*args, **kwargs)
        elif mode == "transit":
            return self.shortest_transit_duration(*args, **kwargs)
        elif mode == "driving":
            return self.shortest_driving_duration(*args, **kwargs)
        elif mode == "bicycling":
            return self.shortest_bicycling_duration(*args, **kwargs)
        else:
            raise ValueError(f"Unsupported mode: {mode}")


# Usage examples:
# api = AmapDirectionAPI(key="YOUR_KEY")
# paths = api.walking_paths(origin, destination)
# plans = api.transit_plans(origin, destination, city)
# drive = api.driving_paths(origin, destination)
# cycle = api.bicycling_paths(origin, destination)
# dists = api.distance_results(origins_list, destination)

# —— POI detail 可选字段全集（官方 show_fields=all 的实际展开）——
_AMAP_POI_ALL_FIELDS = ",".join([
    "children",      # 子POI
    "business",      # 商业信息：tel / rating / cost / opentime…
    "indoor",        # 室内地图 / 楼层
    "navi",          # 导航入口/出口
    "photos"         # 图片
])

class AmapPlaceAPI:
    BASE_URL = "https://restapi.amap.com/v5/place"
    _last_call = 0
    _lock = threading.Lock()
    _min_interval = 0.6  # 默认QPS≤1.6

    def __init__(self, key, session=None, timeout=10):
        self.key = key
        self.session = session or requests.Session()
        self.timeout = timeout

    @classmethod
    def _rate_limit(cls):
        with cls._lock:
            now = time.time()
            wait = cls._last_call + cls._min_interval - now
            if wait > 0:
                time.sleep(wait)
            cls._last_call = time.time()

    def _request(self, path, params):
        self._rate_limit()  # 全局QPS控制
        url = f"{self.BASE_URL}/{path}"
        params.update({"key": self.key})
        resp = self.session.get(url, params=params, timeout=self.timeout)
        data = resp.json()
        if data.get("status") != "1":
            raise AmapAPIError(f"{path} error: {data.get('info')} (code: {data.get('infocode')})")
        return data

    def text_search(self, keywords=None, types=None, region=None, city_limit=False,
                    page_size=10, page_num=1, show_fields=None, **kwargs):
        """
        关键字搜索
        :param keywords: POI 关键字文本（str）
        :param types: POI 类型编码或多值管道分割（str）
        :param region: citycode/adcode/cityname（str）
        :param city_limit: 是否严格限制在region内（bool）
        :param page_size: 每页返回条数（int，1-25）
        :param page_num: 页码（int）
        :param show_fields: 扩展字段列表，如 "children,business,indoor"（str）
        """
        params = {
            "keywords": keywords,
            "types": types,
            "region": region,
            "city_limit": str(city_limit).lower(),
            "page_size": page_size,
            "page_num": page_num,
        }
        if show_fields:
            params["show_fields"] = show_fields
        params.update(kwargs)
        return self._request("text", params)

    def around_search(self, location, keywords=None, types=None, radius=5000,
                      sortrule="weight", region=None, city_limit=False,
                      page_size=10, page_num=1, show_fields=None, **kwargs):
        """
        周边搜索
        :param location: 中心点经纬度 'lng,lat'（str）
        :param radius: 搜索半径（单位米，<=50000）（int）
        """
        params = {
            "location": location,
            "keywords": keywords,
            "types": types,
            "radius": radius,
            "sortrule": sortrule,
            "region": region,
            "city_limit": str(city_limit).lower(),
            "page_size": page_size,
            "page_num": page_num,
        }
        if show_fields:
            params["show_fields"] = show_fields
        params.update(kwargs)
        return self._request("around", params)

    def polygon_search(self, polygon, keywords=None, types=None,
                       page_size=10, page_num=1, show_fields=None, **kwargs):
        """
        多边形区域搜索
        :param polygon: 坐标串，首尾相连，多点'lng,lat|...|lng,lat'
        """
        params = {
            "polygon": polygon,
            "keywords": keywords,
            "types": types,
            "page_size": page_size,
            "page_num": page_num,
        }
        if show_fields:
            params["show_fields"] = show_fields
        params.update(kwargs)
        return self._request("polygon", params)

    def detail_search(self, poi_id, show_fields=None, **kwargs):
        """
        ID 查询
        :param poi_id: 单个或管道分割的多个POI ID（最多10个）
        """
        params = {"id": poi_id}
        if show_fields:
            params["show_fields"] = show_fields
        params.update(kwargs)
        return self._request("detail", params)

    def get_poi_detail(self, poi_id: str, fields: str | list[str] | None = "all", **kwargs) -> dict:
        """
        一次查询单个 POI 的完整信息（默认带所有可选字段）。
        :param poi_id: 单个 POI ID（str）
        :param fields: 
            - "all" : 返回所有可选字段（默认）
            - "basic": 仅返回官方基础字段
            - 逗号分隔字符串 / 列表: 自定义字段集  (如 ["business","photos"])
        :return: dict，对应高德返回的 pois[0]；如果未找到则抛 AmapAPIError
        """
        show_fields = None
        if isinstance(fields, (list, tuple)):
            show_fields = ",".join(fields)
        elif fields == "all":
            show_fields = _AMAP_POI_ALL_FIELDS
        elif fields == "basic":
            show_fields = None  # 不传 → 只要基础字段
        elif fields is not None:
            show_fields = fields
        data = self.detail_search(poi_id, show_fields=show_fields, **kwargs)
        pois = data.get("pois", [])
        if not pois:
            raise AmapAPIError(f"POI {poi_id} not found")
        return pois[0]

    def get_pois_detail(self, poi_ids: list[str], fields: str | list[str] | None = "all", **kwargs) -> list[dict]:
        """
        批量查询（<=10个）POI 详情，返回 list[dict]；顺序与输入 id 顺序一致。
        :param poi_ids: POI ID 列表 (len<=10)
        :param fields: 同 get_poi_detail
        """
        if len(poi_ids) == 0:
            return []
        if len(poi_ids) > 10:
            raise ValueError("最多一次查 10 个 POI id，已超限")
        ids_param = "|".join(poi_ids)
        show_fields = None
        if isinstance(fields, (list, tuple)):
            show_fields = ",".join(fields)
        elif fields == "all":
            show_fields = _AMAP_POI_ALL_FIELDS
        elif fields == "basic":
            show_fields = None
        elif fields is not None:
            show_fields = fields
        data = self.detail_search(ids_param, show_fields=show_fields, **kwargs)
        return data.get("pois", [])

# Usage Example:
# api = AmapPlaceAPI(key="YOUR_KEY")
# result = api.text_search(keywords="肯德基", region="110108", city_limit=True, show_fields="business,children")
# around = api.around_search(location="116.481488,39.990464", types="050300", radius=2000)
# poly = api.polygon_search(polygon="116.460988,40.006919|116.48231,40.007381|116.47516,39.99713|116.460988,40.006919")
# detail = api.detail_search(poi_id="B0FFFAB6J2")

class AmapDistrictAPI:
    BASE_URL = "https://restapi.amap.com/v3/config"

    def __init__(self, key, session=None, timeout=10):
        self.key = key
        self.session = session or requests.Session()
        self.timeout = timeout

    def _request(self, params):
        url = f"{self.BASE_URL}/district"
        params.update({"key": self.key})
        resp = self.session.get(url, params=params, timeout=self.timeout)
        data = resp.json()
        if data.get("status") != "1":
            raise AmapAPIError(f"district error: {data.get('info')} (code: {data.get('infocode')})")
        return data

    def query(self, keywords=None, subdistrict=1, extensions="base",
              filter_adcode=None, page=1, offset=20, output="JSON", **kwargs):
        """
        行政区域查询
        :param keywords: 行政区名称、citycode 或 adcode
        :param subdistrict: 返回下级行政区级数（0-3+）
        :param extensions: base 不含边界；all 含当前级边界
        :param filter_adcode: 指定 adcode 过滤，仅返回匹配项
        :param page: 分页页码
        :param offset: 每页条数
        :param output: JSON 或 XML
        """
        params = {
            "keywords": keywords,
            "subdistrict": subdistrict,
            "extensions": extensions,
            "page": page,
            "offset": offset,
            "output": output,
        }
        if filter_adcode:
            params["filter"] = filter_adcode
        params.update(kwargs)
        return self._request(params)

    def districts(self, **kwargs):
        """
        仅返回列表的 districts 部分
        """
        data = self.query(**kwargs)
        return data.get("districts", [])

# Usage Example:
# from hunter.api.amap_api import AmapDistrictAPI
# district_api = AmapDistrictAPI(key="YOUR_KEY")
# res = district_api.query(keywords="海淀区", subdistrict=1, extensions="all")
# print(res["districts"][0]["adcode"])


class AmapGeocodeAPI:
    BASE_URL = "https://restapi.amap.com/v3/geocode"

    def __init__(self, key, session=None, timeout=10):
        self.key = key
        self.session = session or requests.Session()
        self.timeout = timeout

    def _request(self, path, params):
        url = f"{self.BASE_URL}/{path}"
        params.update({"key": self.key, "output": "JSON"})
        resp = self.session.get(url, params=params, timeout=self.timeout)
        data = resp.json()
        if data.get("status") != "1":
            raise AmapAPIError(f"{path} error: {data.get('info')} (code: {data.get('infocode')})")
        return data

    def geocode(self, address, city=None, **kwargs):
        """
        地理编码：结构化地址 -> 坐标
        :param address: 结构化地址字符串
        :param city: 指定城市（中文/拼音/citycode/adcode）
        """
        params = {"address": address, "city": city}
        params.update(kwargs)
        return self._request("geo", params)

    def geocode_location(self, address, city=None, **kwargs):
        """
        直接返回 location 字段："lng,lat"
        """
        data = self.geocode(address, city=city, **kwargs)
        geocodes = data.get("geocodes", [])
        if not geocodes:
            raise AmapAPIError("Geocode response missing 'geocodes'")
        return geocodes[0].get("location")

    def reverse(self, location, extensions="base", radius=1000,
                poitype=None, roadlevel=None, homeorcorp=None, **kwargs):
        """
        逆地理编码：坐标 -> 结构化地址 + 周边信息
        :param location: "lng,lat"
        :param extensions: base 或 all
        :param radius: 查询半径（米）
        :param poitype: POI typecode 列表，用 "|" 分隔
        """
        params = {"location": location,
                  "extensions": extensions,
                  "radius": radius}
        if poitype:
            params["poitype"] = poitype
        if roadlevel is not None:
            params["roadlevel"] = roadlevel
        if homeorcorp is not None:
            params["homeorcorp"] = homeorcorp
        params.update(kwargs)
        return self._request("regeo", params)

    def reverse_address(self, location, **kwargs):
        """
        直接返回结构化地址描述
        """
        data = self.reverse(location, **kwargs)
        regeocode = data.get("regeocode")
        if not regeocode:
            raise AmapAPIError("Reverse response missing 'regeocode'")
        return regeocode.get("formatted_address")

# Usage Example:
# from hunter.api.amap_api import AmapGeocodeAPI
# geo_api = AmapGeocodeAPI(key="YOUR_KEY")
# res = geo_api.geocode(address="北京市朝阳区阜通东大街6号")
# loc = geo_api.geocode_location("北京市朝阳区阜通东大街6号")
# rev = geo_api.reverse(location="116.480881,39.989410", extensions="all")
# addr = geo_api.reverse_address("116.480881,39.989410")