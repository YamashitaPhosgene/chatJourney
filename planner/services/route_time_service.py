import re
from typing import List, Tuple, Dict

from django.conf import settings
from hunter.api.amap_api import (
    AmapAPIError,
    AmapGeocodeAPI,
    AmapDirectionAPI,
)

class RouteTimeService:
    """
    业务流程：
    1. 解析地址串 → [(addr1, mode), (addr2, mode), ... , addrN]
       约定"地址 —— 交通方式 —— 地址" 形式，中间用中文顿号/长横或英文连字符皆可。
    2. 每个地址用地理编码获取经纬度。
    3. 调用路径规划，按指定 mode 计算耗时（秒）。
    4. 返回整条线路的分段明细和总耗时；可选持久化。
    """

    # 支持的交通方式关键字映射到 AmapDirectionAPI 方法名
    MODE_MAP = {
        "步行":    "walking",
        "walking": "walking",
        "驾车":    "driving",
        "driving": "driving",
        "公交":    "transit",
        "transit": "transit",
        "骑行":    "bicycling",
        "bicycling":"bicycling",
    }

    def __init__(self, amap_key: str | None = None):
        self.key = amap_key or getattr(settings, "AMAP_KEY")
        if not self.key:
            raise ValueError("AMAP_KEY 未配置")
        self.geo_api = AmapGeocodeAPI(self.key)
        self.dir_api = AmapDirectionAPI(self.key)

    # ---------- 解析 ----------
    def parse_route(self, raw: str) -> List[Tuple[str, str]]:
        """
        将 'A——步行——B——公交——C' 解析成
        [('A', '步行'), ('B', '公交'), ('C', '')]
        末尾地址 mode 设为空串，后续不用。
        """
        segs = re.split(r"[—－–—]+", raw)     # 兼容多种破折号
        result: List[Tuple[str, str]] = []
        for i, seg in enumerate(segs):
            seg = seg.strip()
            if i % 2 == 0:      # 地址
                mode = segs[i+1].strip() if i+1 < len(segs) else ""
                result.append((seg, mode))
        return result

    # ---------- 核心入口 ----------
    def compute(self, route_str: str, city_hint: str | None = None
                ) -> Dict[str, object]:
        """
        :param route_str: 形如 'A——步行——B——公交——C'
        :param city_hint: geocode city 提示，可为空
        :return: {
            'segments': [
                {'from': 'A', 'to': 'B', 'mode': '步行', 'duration': 600},
                ...
            ],
            'total_duration': 1800
        }
        """
        points = self.parse_route(route_str)
        if len(points) < 2:
            raise ValueError("地址段不足两处，无法规划")

        # 1. 地理编码
        coords: Dict[str, str] = {}
        for addr, _ in points:
            if addr in coords:
                continue
            try:
                coords[addr] = self.geo_api.geocode_location(addr, city=city_hint)
            except AmapAPIError as e:
                raise AmapAPIError(f"地理编码失败: {addr}: {e}") from e

        # 2. 逐段规划
        segments, total = [], 0
        for i in range(len(points)-1):
            addr_from, mode_cn = points[i]
            addr_to, _ = points[i+1]
            mode = self.MODE_MAP.get(mode_cn)
            if not mode:
                raise ValueError(f"不支持的交通方式: {mode_cn}")

            origin = coords[addr_from]
            dest   = coords[addr_to]

            # 根据 mode 调用对应快捷耗时方法
            try:
                if mode == "walking":
                    duration = self.dir_api.shortest_walking_duration(origin, dest)
                elif mode == "driving":
                    duration = self.dir_api.shortest_driving_duration(origin, dest)
                elif mode == "bicycling":
                    duration = self.dir_api.shortest_bicycling_duration(origin, dest)
                elif mode == "transit":
                    # 公交换乘需 city 参数；取 city_hint 或 from->geocode 的 citycode
                    city = city_hint or self.geo_api.geocode(addr_from)["geocodes"][0]["citycode"]
                    duration = self.dir_api.shortest_transit_duration(origin, dest, city=city)
                else:
                    raise ValueError(f"未实现的 mode: {mode}")
            except AmapAPIError as e:
                raise AmapAPIError(f"{addr_from}->{addr_to} 路径规划失败: {e}") from e

            segments.append({
                "from": addr_from,
                "to": addr_to,
                "mode": mode_cn,
                "duration": duration
            })
            total += duration

        return {"segments": segments, "total_duration": total}

    # ---------- 可选持久化 ----------
    def save_to_db(self, result: Dict[str, object]):
        """留待业务层实现，例如写入 PostgreSQL / MySQL / MongoDB"""
        pass 