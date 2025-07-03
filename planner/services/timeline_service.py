from __future__ import annotations

import collections
import datetime as dt
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from django.db.models import Q
from talker.models import TalkSession, POIItem, POISession
from hunter.api.amap_api import AmapPlaceAPI, AmapDirectionAPI

# == 每日时间块模板 ===============================
BLOCKS: list[tuple[str, str]] = [
    ("08:00", "09:00"),  # 早餐
    ("09:00", "11:30"),  # 上午景点
    ("11:30", "13:00"),  # 午餐
    ("13:00", "16:30"),  # 下午景点
    ("16:30", "18:00"),  # 交通/休息
    ("18:00", "20:00"),  # 晚餐
    ("20:00", "22:00"),  # 夜间活动
]

@dataclass
class TimelineSlot:
    title: str
    start: dt.datetime
    end: dt.datetime
    type: str                       # poi / food / transfer / hotel / inter_city / other
    poi: Optional[dict] = None      # 仅 type == "poi" 时填充

class POITimelineHelper:
    """负责：把 POIItem 补全为高德完整数据、城市聚类、中心坐标估计"""
    def __init__(self, place_api: AmapPlaceAPI):
        self.place_api = place_api

    def fetch_detail(self, item: POIItem) -> dict:
        """
        确保 POIItem.raw_data 至少包含 citycode + location。
        不全则调用高德 text_search / detail 并写回数据库缓存。
        """
        if item.raw_data and item.raw_data.get("citycode") and item.location:
            return item.raw_data
        if item.poi_id:
            detail = self.place_api.get_poi_detail(item.poi_id)
        else:
            search = self.place_api.text_search(keywords=item.name, page_size=1, city_limit=False)
            if not search["pois"]:
                raise ValueError(f"高德无结果：{item.name}")
            detail = self.place_api.get_poi_detail(search["pois"][0]["id"])
        item.raw_data = detail
        item.location = detail["location"]
        item.address = item.address or detail.get("address")
        item.type = item.type or detail.get("type")
        item.poi_id = item.poi_id or detail["id"]
        item.save(update_fields=["raw_data", "location", "address", "type", "poi_id"])
        return detail

    def cluster_by_city(self, items: list[POIItem]) -> dict[str, list[POIItem]]:
        clusters: dict[str, list[POIItem]] = collections.defaultdict(list)
        for it in items:
            try:
                detail = self.fetch_detail(it)
            except Exception:
                continue
            clusters[detail["citycode"]].append(it)
        return clusters

    def city_center(self, citycode: str) -> str:
        try:
            res = self.place_api.text_search(types="110000", region=citycode, city_limit=True, page_size=1)
            return res["pois"][0]["location"]
        except Exception:
            return "0,0"

class TimelineService:
    def __init__(self, place_api: AmapPlaceAPI, dir_api: AmapDirectionAPI):
        self.place_api = place_api
        self.dir_api = dir_api
        self.helper = POITimelineHelper(place_api)

    def build_timeline(self, session: TalkSession) -> list[TimelineSlot]:
        """
        主入口：传入 TalkSession → 返回按时间排序的 TimelineSlot 列表
        """
        # 通过POISession获取会话的所有POIItem
        poi_relations = POISession.objects.filter(session=session).select_related('poi')
        all_items = [rel.poi for rel in poi_relations]
        
        if not all_items:
            return []
        
        # 按来源分类
        must_items = [rel.poi for rel in poi_relations if rel.source in ("manual", "reverse_search")]
        opt_items = [rel.poi for rel in poi_relations if rel.source == "keyword_search"]
        
        city_map = self.helper.cluster_by_city(all_items)
        start_d, end_d = session.start_date, session.end_date
        total_days = (end_d - start_d).days + 1
        days_each = self._allocate_days_by_poi(city_map, total_days)
        ordered_citycodes: list[str] = []
        for name in session.locations:
            try:
                detail = self.place_api.text_search(keywords=name, page_size=1)["pois"][0]
                cc = detail["citycode"]
                if cc not in ordered_citycodes:
                    ordered_citycodes.append(cc)
            except Exception:
                continue
        for cc in city_map:
            if cc not in ordered_citycodes:
                ordered_citycodes.append(cc)
        slots: list[TimelineSlot] = []
        cur_date = start_d
        prev_center = None
        for cc in ordered_citycodes:
            city_name = (city_map[cc][0].raw_data or {}).get("cityname", "未知城市")
            if prev_center:
                cur_center = self.helper.city_center(cc)
                mins = self._drive_minutes(prev_center, cur_center)
                dep_ts = dt.datetime.combine(cur_date, dt.time(8, 30))
                slots.append(TimelineSlot(f"前往 {city_name}", dep_ts, dep_ts + dt.timedelta(minutes=mins), type="inter_city"))
            prev_center = self.helper.city_center(cc)
            for _ in range(days_each[cc]):
                day_slots = self._plan_one_day(
                    date=cur_date,
                    must_pois=[i for i in must_items if self.helper.fetch_detail(i)["citycode"] == cc],
                    opt_pois=[i for i in opt_items  if self.helper.fetch_detail(i)["citycode"] == cc],
                    user_profile=session.user_profile
                )
                slots.extend(day_slots)
                cur_date += dt.timedelta(days=1)
        return sorted(slots, key=lambda s: s.start)

    def _plan_one_day(self, date: dt.date, must_pois: list[POIItem], opt_pois: list[POIItem], user_profile: dict[str, Any]) -> list[TimelineSlot]:
        blk_times: list[tuple[dt.datetime, dt.datetime]] = [
            (self._to_dt(date, s), self._to_dt(date, e)) for s, e in BLOCKS
        ]
        plan: list[TimelineSlot] = []
        prev_loc: Optional[str] = None
        prev_end: Optional[dt.datetime] = None
        prev_city: Optional[str] = None
        def choose_transport_mode(user_profile, walk_min, bike_min, car_min, taxi_min, public_min):
            # 1. 用户自驾游优先
            if any(k in str(user_profile) for k in ["自驾", "自驾游", "自驾车", "自驾旅行"]):
                if walk_min is not None and walk_min <= 10:
                    return "walk"
                return "car"
            # 2. 步行优先
            if walk_min is not None and walk_min <= 15:
                return "walk"
            # 3. 骑行
            if bike_min is not None and bike_min <= 15:
                return "bike"
            # 4. 公共交通和打车时间相近
            if public_min and taxi_min and abs(public_min - taxi_min) / taxi_min < 0.1:
                return "metro"
            # 5. 公共交通优先
            if public_min and (not taxi_min or public_min < taxi_min):
                return "metro"
            # 6. 打车
            if taxi_min:
                return "taxi"
            # 7. 兜底
            return "walk"
        def get_transfer_slot(prev_loc, curr_loc, prev_end_time, user_profile, city=None):
            try:
                walk_min = self.dir_api.shortest_walking_duration(prev_loc, curr_loc) // 60
            except Exception:
                walk_min = None
            try:
                bike_min = self.dir_api.shortest_bicycling_duration(prev_loc, curr_loc) // 60
            except Exception:
                bike_min = None
            try:
                car_min = self.dir_api.shortest_driving_duration(prev_loc, curr_loc) // 60
            except Exception:
                car_min = None
            # taxi_min 直接用驾车时间
            taxi_min = car_min
            public_min = None
            if city:
                try:
                    public_min = self.dir_api.shortest_transit_duration(prev_loc, curr_loc, city=city) // 60
                except Exception:
                    public_min = None
            mode = choose_transport_mode(user_profile, walk_min, bike_min, car_min, taxi_min, public_min)
            # 选定的交通方式所需分钟数
            mode_min = {
                "walk": walk_min,
                "bike": bike_min,
                "car": car_min,
                "taxi": taxi_min,
                "metro": public_min
            }.get(mode, walk_min)
            if mode_min is None or mode_min == 0:
                return None
            transfer_start = prev_end_time
            transfer_end = prev_end_time + dt.timedelta(minutes=mode_min)
            return TimelineSlot(
                title=f"市内交通（{mode}）",
                start=transfer_start,
                end=transfer_end,
                type="transfer",
                poi=None
            )
        def place_poi(item: POIItem) -> None:
            nonlocal prev_loc, prev_end, prev_city
            detail = self.helper.fetch_detail(item)
            idx = self._first_fittable_block(detail, prev_loc, blk_times)
            if idx is None:
                return
            st, ed = blk_times[idx]
            # 插入市内交通slot
            if prev_loc and prev_end:
                citycode = detail.get("citycode")
                transfer_slot = get_transfer_slot(prev_loc, detail["location"], prev_end, user_profile, city=citycode)
                if transfer_slot:
                    plan.append(transfer_slot)
                    # 交通slot结束时间就是当前POI的开始时间
                    st = transfer_slot.end
            plan.append(TimelineSlot(detail["name"], st, ed, "poi", poi=detail))
            blk_times[idx] = (st, st)
            prev_loc = detail["location"]
            prev_end = ed
            prev_city = detail.get("citycode")
        for poi in must_pois:
            place_poi(poi)
        opt_sorted = sorted(opt_pois, key=lambda i: -self._poi_score(i, user_profile))
        for poi in opt_sorted:
            place_poi(poi)
        self._fill_meals_and_hotels(date, blk_times, plan)
        return sorted(plan, key=lambda s: s.start)

    @staticmethod
    def _allocate_days_by_poi(city_map: dict[str, list[POIItem]], total_days: int) -> dict[str, int]:
        poi_cnt = {c: max(1, len(lst)) for c, lst in city_map.items()}
        total_poi = sum(poi_cnt.values())
        days = {c: round(total_days * cnt / total_poi) for c, cnt in poi_cnt.items()}
        for c in days:
            days[c] = max(days[c], 1)
        diff = total_days - sum(days.values())
        order = sorted(poi_cnt, key=poi_cnt.get, reverse=(diff > 0))
        i = 0
        while diff != 0:
            c = order[i % len(order)]
            if diff > 0:
                days[c] += 1
                diff -= 1
            else:
                if days[c] > 1:
                    days[c] -= 1
                    diff += 1
            i += 1
        return days

    def _first_fittable_block(self, detail: dict, prev_loc: Optional[str], blocks: list[tuple[dt.datetime, dt.datetime]]) -> Optional[int]:
        NEED_MIN = 90
        for idx, (st, ed) in enumerate(blocks):
            if (ed - st).seconds < NEED_MIN * 60:
                continue
            if not self._is_open(detail, st.time()):
                continue
            if prev_loc:
                walk_min = self._walk_minutes(prev_loc, detail["location"])
                if walk_min + NEED_MIN > (ed - st).seconds / 60:
                    continue
            return idx
        return None

    def _poi_score(self, item: POIItem, profile: dict[str, Any]) -> float:
        detail = self.helper.fetch_detail(item)
        rating = float(detail.get("business", {}).get("rating") or 4)
        interests = profile.get("兴趣爱好", [])
        hit = 1 if any(k in (detail.get("type") or "") for k in interests) else 0
        return rating + 0.5 * hit

    @staticmethod
    def _fill_meals_and_hotels(date: dt.date, blocks: list[tuple[dt.datetime, dt.datetime]], plan: list[TimelineSlot]) -> None:
        for st, ed in blocks:
            if st == ed:
                continue
            if st.hour in (8, 11, 18):
                plan.append(TimelineSlot("用餐", st, ed, "food"))
            elif st.hour == 20:
                plan.append(TimelineSlot("夜间自由活动", st, ed, "other"))
            elif st.hour == 22:
                plan.append(TimelineSlot("入住酒店", st, ed, "hotel"))

    @staticmethod
    def _to_dt(base: dt.date, hhmm: str) -> dt.datetime:
        h, m = map(int, hhmm.split(":"))
        return dt.datetime.combine(base, dt.time(h, m))

    def _walk_minutes(self, loc1: str, loc2: str) -> int:
        try:
            return int(self.dir_api.shortest_walking_duration(loc1, loc2) / 60)
        except Exception:
            return 0

    def _drive_minutes(self, loc1: str, loc2: str) -> int:
        try:
            return int(self.dir_api.shortest_driving_duration(loc1, loc2) / 60)
        except Exception:
            return 120

    @staticmethod
    def _is_open(detail: dict, when: dt.time) -> bool:
        ot = detail.get("business", {}).get("opentime_today") or ""
        try:
            st_s, ed_s = ot.split("-")
            st = dt.datetime.strptime(st_s.strip(), "%H:%M").time()
            ed = dt.datetime.strptime(ed_s.strip(), "%H:%M").time()
            return st <= when <= ed
        except Exception:
            return True 