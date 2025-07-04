import re
import datetime as dt
from typing import List, Tuple, Dict, Optional, Any
from dataclasses import dataclass
from decimal import Decimal
import logging
import time

from django.conf import settings
from django.contrib.auth.models import User
from hunter.api.amap_api import (
    AmapAPIError,
    AmapGeocodeAPI,
    AmapDirectionAPI,
    AmapPlaceAPI,
    AmapDistrictAPI,
)
from planner.models import Trip, Location, Activity, Transport, Day
from talker.models import POIItem

@dataclass
class ActivityInfo:
    """活动信息"""
    name: str
    duration_minutes: int
    location: str

@dataclass
class DayPlan:
    """单日行程计划"""
    day_number: int
    activities: List[ActivityInfo]
    transport_segments: List[Dict[str, Any]]

@dataclass
class RouteSegment:
    """路线段信息"""
    from_location: str
    to_location: str
    transport_mode: str
    duration_seconds: int
    activity_before: Optional[ActivityInfo] = None
    activity_after: Optional[ActivityInfo] = None

class RouteTimeService:
    """
    业务流程：
    1. 解析多天行程字符串 → [DayPlan1, DayPlan2, ...]
       支持格式：DayX: 地点A(活动, 时长90分钟) --交通方式-- 地点B(活动, 时长60分钟)
    2. 每个地址用地理编码获取经纬度。
    3. 调用路径规划，按指定 mode 计算耗时（秒）。
    4. 返回整条线路的分段明细和总耗时；可选持久化到数据库。
    """

    # 支持的交通方式关键字映射到 AmapDirectionAPI 方法名
    MODE_MAP = {
        "步行":    "walking",
        "walking": "walking",
        "驾车":    "driving",
        "driving": "driving",
        "公交":    "transit",
        "transit": "transit",
        "地铁":    "transit",
        "打车":    "driving",
        "自驾":    "driving",
        "骑行":    "bicycling",
        "bicycling":"bicycling",
        "高铁":    "driving",  # 高铁站间交通
        "飞机":    "driving",  # 机场间交通
        "火车":    "driving",  # 火车站间交通
    }

    # 交通方式映射到数据库模式
    TRANSPORT_MODE_MAP = {
        "步行": "other",
        "地铁": "metro",
        "公交": "bus",
        "打车": "taxi",
        "自驾": "car",
        "骑行": "other",
        "高铁": "train",
        "飞机": "fly",
        "火车": "train",
    }

    _last_amap_call = 0  # 全局静态变量，记录上次高德API调用时间

    def _amap_rate_limit(self, min_interval=0.6):
        now = time.time()
        wait = self._last_amap_call + min_interval - now
        if wait > 0:
            time.sleep(wait)
        RouteTimeService._last_amap_call = time.time()

    def __init__(self, amap_key: str | None = None):
        self.key = amap_key or getattr(settings, "AMAP_KEY")
        if not self.key:
            raise ValueError("AMAP_KEY 未配置")
        self.geo_api = AmapGeocodeAPI(self.key)
        self.dir_api = AmapDirectionAPI(self.key)

    # ---------- 解析多天行程 ----------
    def parse_multi_day_plan(self, plan_text: str) -> List[DayPlan]:
        """
        解析多天行程文本，支持新格式：
        Day1: 地点A(活动, 时长90分钟) --交通方式-- 地点B(活动, 时长60分钟)
        Day2: 地点C(活动, 时长120分钟)
        """
        day_plans = []
        plan_text = plan_text.strip()
        logging.info(f"[RouteTimeService] 原始行程文本: {repr(plan_text)}")
        if '\n' not in plan_text:
            import re
            day_lines = re.split(r'(Day\d+:)', plan_text)
            processed_lines = []
            for i in range(1, len(day_lines), 2):
                if i + 1 < len(day_lines):
                    day_line = day_lines[i] + day_lines[i + 1]
                    processed_lines.append(day_line)
            logging.info(f"[RouteTimeService] Day分割结果: {processed_lines}")
        else:
            processed_lines = plan_text.split('\n')
            logging.info(f"[RouteTimeService] 换行分割结果: {processed_lines}")
        for line in processed_lines:
            line = line.strip()
            if not line or not line.startswith('Day'):
                continue
            day_plan = self._parse_single_day(line)
            if day_plan:
                day_plans.append(day_plan)
            else:
                logging.error(f"[RouteTimeService] 单日行程解析失败: {repr(line)}")
        logging.info(f"[RouteTimeService] 解析得到 {len(day_plans)} 天行程")
        return day_plans

    def _parse_single_day(self, day_line: str) -> Optional[DayPlan]:
        """解析单日行程"""
        import logging
        logging.info(f"[RouteTimeService] 解析单日行程: {repr(day_line)}")
        import re
        day_match = re.match(r'Day(\d+):\s*(.+)', day_line)
        if not day_match:
            logging.error(f"[RouteTimeService] Day行正则不匹配: {repr(day_line)}")
            return None
        day_number = int(day_match.group(1))
        content = day_match.group(2).strip()
        activities = []
        transport_segments = []
        segments = re.split(r'\s*--([^--]+)--\s*', content)
        logging.info(f"[RouteTimeService] 活动/交通分割: {segments}")
        for i, segment in enumerate(segments):
            if i % 2 == 0:
                activity = self._parse_activity(segment.strip())
                if activity:
                    activities.append(activity)
                else:
                    logging.error(f"[RouteTimeService] 活动解析失败: {repr(segment)}")
            else:
                transport_mode = segment.strip()
                transport_segments.append({"mode": transport_mode})
        return DayPlan(
            day_number=day_number,
            activities=activities,
            transport_segments=transport_segments
        )

    def _parse_activity(self, activity_text: str) -> Optional[ActivityInfo]:
        """解析单个活动信息，增强容错能力"""
        # 1. 标准化括号和逗号
        text = activity_text.replace('（', '(').replace('）', ')').replace('，', ',')
        # 2. 匹配格式：地点A(活动, 时长90分钟)
        pattern = r'(.+?)\(\s*(.+?)\s*,\s*时长\s*(\d+)\s*分钟\s*\)'
        match = re.match(pattern, text)
        if match:
            location = match.group(1).strip()
            # 去除地点内部所有空白，避免"宽窄巷 子"等解析异常
            location = re.sub(r"\s+", "", location)
            activity_name = match.group(2).strip()
            duration = int(match.group(3))
            return ActivityInfo(
                name=activity_name,
                duration_minutes=duration,
                location=location
            )
        # 3. 匹配简单格式：地点A(活动)
        simple_pattern = r'(.+?)\(\s*(.+?)\s*\)'
        match = re.match(simple_pattern, text)
        if match:
            location = match.group(1).strip()
            # 去除地点内部所有空白，避免"宽窄巷 子"等解析异常
            location = re.sub(r"\s+", "", location)
            activity_name = match.group(2).strip()
            return ActivityInfo(
                name=activity_name,
                duration_minutes=60,  # 默认60分钟
                location=location
            )
        # 4. 解析失败时输出详细日志
        logging.error(f"[RouteTimeService] 活动解析失败: '{activity_text}' (标准化后: '{text}')")
        return None

    # ---------- 数据库保存功能 ----------
    def save_plan_to_db(self, plan_text: str, user: User, trip_title: str, 
                       trip_description: str = "", city_hint: str | None = None,
                       start_date: dt.date | None = None) -> Trip:
        """
        将解析的行程计划保存到数据库
        
        :param plan_text: 多天行程文本
        :param user: 用户对象
        :param trip_title: 行程标题
        :param trip_description: 行程描述
        :param city_hint: 城市提示
        :param start_date: 开始日期
        :return: 创建的 Trip 对象
        """
        day_plans = self.parse_multi_day_plan(plan_text)
        if not day_plans:
            raise ValueError("无法解析行程计划")
        
        # 设置默认开始日期
        if not start_date:
            start_date = dt.date.today()
        
        # 计算结束日期
        end_date = start_date + dt.timedelta(days=len(day_plans) - 1)
        
        # 创建 Trip
        trip = Trip.objects.create(
            user=user,
            title=trip_title,
            description=trip_description,
            start_date=start_date,
            end_date=end_date
        )
        
        # 创建 Day 记录
        days = {}
        current_date = start_date
        for day_plan in day_plans:
            day = Day.objects.create(
                trip=trip,
                date=current_date,
                day_index=day_plan.day_number
            )
            days[day_plan.day_number] = day
            current_date += dt.timedelta(days=1)
        
        # 处理每天的活动和交通
        current_date = start_date
        for day_plan in day_plans:
            self._save_day_to_db(day_plan, trip, days[day_plan.day_number], 
                               current_date, city_hint)
            current_date += dt.timedelta(days=1)
        
        return trip

    def _get_or_create_location_by_poiitem(self, name, city_hint=None):
        from talker.models import POIItem
        from planner.models import Location
        from hunter.api.amap_api import AmapPlaceAPI
        lng, lat = None, None
        official_name = name
        poi = POIItem.objects.filter(name=name).first()
        need_amap = True
        if poi and poi.location:
            try:
                lng, lat = map(float, poi.location.split(','))
                official_name = poi.name
                need_amap = False
            except Exception:
                lng, lat = None, None
                need_amap = True
        if need_amap:
            for attempt in range(2):
                try:
                    self._amap_rate_limit()
                    logging.debug(f"[DEBUG] Amap search keywords={name} (attempt {attempt+1})")
                    amap_client = AmapPlaceAPI(key=self.key)
                    # 如果提供了城市提示，则先解析为adcode（6位行政区划代码）后再限定搜索范围
                    region_param = None
                    if city_hint:
                        if re.match(r"^\d{6}$", str(city_hint)):
                            region_param = str(city_hint)
                        else:
                            try:
                                district_api = AmapDistrictAPI(key=self.key)
                                district_data = district_api.query(keywords=city_hint, subdistrict=0)
                                districts = district_data.get("districts", [])
                                if districts:
                                    region_param = districts[0].get("adcode")
                                    logging.debug(f"[DEBUG] city_hint '{city_hint}' 解析为adcode {region_param}")
                            except Exception as ge:
                                logging.debug(f"[DEBUG] city_hint解析adcode失败: {ge}")
                    # 调用 Amap 搜索（始终 city_limit=True，若 region_param 为None 则全国范围）
                    data = amap_client.text_search(
                        keywords=name,
                        region=region_param,
                        city_limit=True,
                        page_size=1
                    )
                    pois = data.get('pois', []) if data else []
                    if pois:
                        poi_data = pois[0]
                        loc_str = poi_data.get('location')
                        official_name = poi_data.get('name', name)
                        if loc_str:
                            try:
                                lng, lat = map(float, loc_str.split(','))
                                # 同步写入 POIItem（用官方名称）
                                poi, _ = POIItem.objects.get_or_create(
                                    poi_id=poi_data.get('id', ''),
                                    defaults={
                                        'name': official_name,
                                        'address': poi_data.get('address', ''),
                                        'location': loc_str,
                                        'type': poi_data.get('type', ''),
                                        'tel': poi_data.get('tel', ''),
                                        'distance': poi_data.get('distance', ''),
                                        'raw_data': poi_data
                                    }
                                )
                                poi.location = loc_str
                                poi.address = poi_data.get('address', poi.address)
                                poi.name = official_name
                                poi.save()
                            except Exception:
                                pass
                        break  # 成功后跳出重试
                    logging.info(f"[INFO] Amap search result for '{name}': status={data.get('status')} count={data.get('count')} first={{'id': pois[0].get('id') if pois else None, 'name': pois[0].get('name') if pois else None, 'location': pois[0].get('location') if pois else None}}")
                except Exception as e:
                    if "QPS" in str(e) or "10021" in str(e):
                        time.sleep(2.0)  # QPS超限，额外等待
                    else:
                        break
        location, created = Location.objects.get_or_create(
            name=official_name,
            defaults={
                'longitude': lng,
                'latitude': lat,
                'category': 'sight'
            }
        )
        logging.info(f"[INFO] POI resolve: input='{name}' -> official='{official_name}', lng={lng}, lat={lat}, poi_exists={bool(poi)}, loc_created={created}")
        if (not location.longitude or not location.latitude) and lng and lat:
            location.longitude = lng
            location.latitude = lat
            location.save()
        return location, official_name

    def _save_day_to_db(self, day_plan: DayPlan, trip: Trip, day: Day, 
                       date: dt.date, city_hint: str | None = None):
        """保存单日行程到数据库，地点经纬度优先用POIItem"""
        activities = day_plan.activities
        transport_segments = day_plan.transport_segments
        if not activities:
            return
        # 获取所有地点的 Location（优先用POIItem经纬度），key为官方名
        locations = {}
        name_map = {}
        for activity in activities:
            loc, official_name = self._get_or_create_location_by_poiitem(activity.location, city_hint)
            locations[official_name] = loc
            name_map[activity.location] = official_name
        logging.info("[INFO] Day locations map: " + ", ".join([f"{k}({v.longitude},{v.latitude})" for k,v in locations.items()]))
        # 计算交通时间
        transport_details = []
        total_transport_time = 0
        for i in range(len(activities) - 1):
            if i < len(transport_segments):
                transport_mode = transport_segments[i]["mode"]
                mode = self.MODE_MAP.get(transport_mode)
                from_official = name_map[activities[i].location]
                to_official = name_map[activities[i + 1].location]
                origin = f"{locations[from_official].longitude},{locations[from_official].latitude}"
                dest = f"{locations[to_official].longitude},{locations[to_official].latitude}"
                real_mode = transport_mode
                duration = None
                # 智能选择
                if mode == "walking":
                    try:
                        walk_sec = self.dir_api.shortest_walking_duration(origin, dest)
                        if walk_sec <= 25*60:
                            real_mode = "步行"
                            duration = walk_sec
                        else:
                            real_mode, duration = self._smart_select_transport_mode(origin, dest, city_hint)
                            print(f"[RouteTimeService] 步行超时，切换为{real_mode}，耗时{duration//60}分钟")
                    except Exception as e:
                        real_mode, duration = self._smart_select_transport_mode(origin, dest, city_hint)
                        print(f"[RouteTimeService] 步行失败({e})，切换为{real_mode}，耗时{duration//60}分钟")
                else:
                    try:
                        if mode == "walking":
                            duration = self.dir_api.shortest_walking_duration(origin, dest)
                        elif mode == "driving":
                            duration = self.dir_api.shortest_driving_duration(origin, dest)
                        elif mode == "bicycling":
                            duration = self.dir_api.shortest_bicycling_duration(origin, dest)
                        elif mode == "transit":
                            city = city_hint or self.geo_api.geocode(activities[i].location)["geocodes"][0]["citycode"]
                            duration = self.dir_api.shortest_transit_duration(origin, dest, city=city)
                        else:
                            raise ValueError(f"未实现的 mode: {mode}")
                        real_mode = transport_mode
                    except Exception as e:
                        real_mode, duration = self._smart_select_transport_mode(origin, dest, city_hint)
                        print(f"[RouteTimeService] {transport_mode}失败({e})，切换为{real_mode}，耗时{duration//60}分钟")
                if duration is None:
                    real_mode, duration = self._smart_select_transport_mode(origin, dest, city_hint)
                    print(f"[RouteTimeService] 交通方式未知，兜底为{real_mode}，耗时{duration//60}分钟")
                transport_details.append({
                    "from": from_official,
                    "to": to_official,
                    "mode": real_mode,
                    "duration": duration
                })
                total_transport_time += duration
                if duration > 6*3600:
                    logging.warning(f"[WARN] 超长交通: {from_official}->{to_official} {real_mode} {duration//60}min")
                logging.info(f"[INFO] transport segment: {from_official}->{to_official} mode={real_mode} duration={duration//60}min origin={origin} dest={dest}")
        # 生成时间安排并保存到数据库
        current_time = dt.time(9, 0)  # 从9点开始
        for i, activity in enumerate(activities):
            # 保存活动
            activity_start = current_time
            activity_end = self._add_minutes_to_time(current_time, activity.duration_minutes)
            official_name = name_map[activity.location]
            Activity.objects.create(
                trip=trip,
                type='activity',
                date=date,
                start_time=activity_start,
                duration=dt.timedelta(minutes=activity.duration_minutes),
                location=locations[official_name],
                title=activity.name,
                description=f"第{day_plan.day_number}天活动"
            )
            current_time = activity_end
            # 保存交通（除了最后一个活动）
            if i < len(transport_details):
                transport = transport_details[i]
                transport_start = current_time
                transport_end = self._add_seconds_to_time(current_time, transport["duration"])
                dest_location = locations[transport["to"]]
                Transport.objects.create(
                    trip=trip,
                    type='departure',
                    date=date,
                    start_time=transport_start,
                    duration=dt.timedelta(seconds=transport["duration"]),
                    location=locations[transport["from"]],
                    destination=dest_location,
                    mode=self.TRANSPORT_MODE_MAP.get(transport["mode"], "other"),
                    title=f"{transport['from']} → {transport['to']}",
                    description=f"交通方式: {transport['mode']}"
                )
                current_time = transport_end

    def _calculate_transport_duration(self, from_location: str, to_location: str, 
                                    transport_mode: str, city_hint: str | None = None) -> int:
        """计算交通时间（秒）"""
        try:
            # 获取坐标
            from_coord = self.geo_api.geocode_location(from_location, city=city_hint)
            to_coord = self.geo_api.geocode_location(to_location, city=city_hint)
            
            # 根据交通方式计算时间
            mode = self.MODE_MAP.get(transport_mode)
            if not mode:
                return 900  # 默认15分钟
            
            if mode == "walking":
                return self.dir_api.shortest_walking_duration(from_coord, to_coord)
            elif mode == "driving":
                return self.dir_api.shortest_driving_duration(from_coord, to_coord)
            elif mode == "bicycling":
                return self.dir_api.shortest_bicycling_duration(from_coord, to_coord)
            elif mode == "transit":
                city = city_hint or self.geo_api.geocode(from_location)["geocodes"][0]["citycode"]
                return self.dir_api.shortest_transit_duration(from_coord, to_coord, city=city)
            else:
                return 900  # 默认15分钟
                
        except Exception as e:
            print(f"计算交通时间失败: {e}")
            return 900  # 默认15分钟

    def _add_minutes_to_time(self, time_obj: dt.time, minutes: int) -> dt.time:
        """给时间对象添加分钟数"""
        total_minutes = time_obj.hour * 60 + time_obj.minute + minutes
        hours = total_minutes // 60
        mins = total_minutes % 60
        return dt.time(hours, mins)

    def _add_seconds_to_time(self, time_obj: dt.time, seconds: int) -> dt.time:
        """给时间对象添加秒数"""
        total_seconds = time_obj.hour * 3600 + time_obj.minute * 60 + seconds
        hours = total_seconds // 3600
        mins = (total_seconds % 3600) // 60
        return dt.time(hours, mins)

    # ---------- 核心入口 ----------
    def compute_multi_day_plan(self, plan_text: str, city_hint: str | None = None,
                              start_date: dt.date | None = None) -> Dict[str, Any]:
        """
        计算多天行程的详细时间和安排
        
        :param plan_text: 多天行程文本
        :param city_hint: 城市提示
        :param start_date: 开始日期，用于生成具体时间安排
        :return: 包含每天详细安排的字典
        """
        day_plans = self.parse_multi_day_plan(plan_text)
        if not day_plans:
            raise ValueError("无法解析行程计划")
        
        # 设置默认开始日期
        if not start_date:
            start_date = dt.date.today()
        
        result = {
            "total_days": len(day_plans),
            "start_date": start_date.isoformat(),
            "days": []
        }
        
        current_date = start_date
        
        for day_plan in day_plans:
            day_result = self._compute_single_day(
                day_plan, current_date, city_hint
            )
            result["days"].append(day_result)
            current_date += dt.timedelta(days=1)
        
        # 计算总统计信息
        total_activities = sum(len(day["activities"]) for day in result["days"])
        total_transport_time = sum(day["total_transport_time"] for day in result["days"])
        total_activity_time = sum(day["total_activity_time"] for day in result["days"])
        
        result.update({
            "total_activities": total_activities,
            "total_transport_time": total_transport_time,
            "total_activity_time": total_activity_time,
            "total_time": total_transport_time + total_activity_time
        })
        
        return result

    def _smart_select_transport_mode(self, origin, dest, city_hint=None):
        """智能选择交通方式，返回(mode, duration)"""
        logging.debug(f"[DEBUG] smart_select start origin={origin} dest={dest}")
        try:
            walk_sec = self.dir_api.shortest_walking_duration(origin, dest)
        except Exception as e:
            logging.debug(f"[DEBUG] walking error: {e}")
            walk_sec = None
        if walk_sec:
            logging.debug(f"[DEBUG] walking duration={walk_sec}")
        # 其他方式
        def safe_call(label, func):
            try:
                val = func()
                logging.debug(f"[DEBUG] {label} duration={val}")
                return val
            except Exception as err:
                logging.debug(f"[DEBUG] {label} error: {err}")
                return None
        bike_sec   = safe_call("bicycle", lambda: self.dir_api.shortest_bicycling_duration(origin, dest))
        drive_sec  = safe_call("drive",   lambda: self.dir_api.shortest_driving_duration(origin, dest))
        transit_sec= safe_call("transit", lambda: self.dir_api.shortest_transit_duration(origin, dest, city=city_hint) if city_hint else None)
        # 骑行优先
        if bike_sec is not None and bike_sec <= 20*60:
            return ("骑行", bike_sec)
        # 打车/公交更快者
        candidates = []
        if drive_sec is not None:
            candidates.append(("打车", drive_sec))
        if transit_sec is not None:
            candidates.append(("公交", transit_sec))
        if candidates:
            return min(candidates, key=lambda x: x[1])
        # 都失败，兜底
        if walk_sec is not None:
            return ("步行", walk_sec)
        if bike_sec is not None:
            return ("骑行", bike_sec)
        if drive_sec is not None:
            return ("打车", drive_sec)
        if transit_sec is not None:
            return ("公交", transit_sec)
        # 兜底30分钟（秒）
        return ("步行", 1800)

    def _compute_single_day(self, day_plan: DayPlan, date: dt.date, 
                           city_hint: str | None) -> Dict[str, Any]:
        """计算单日行程的详细时间安排"""
        activities = day_plan.activities
        transport_segments = day_plan.transport_segments
        
        if not activities:
            return {
                "day_number": day_plan.day_number,
                "date": date.isoformat(),
                "activities": [],
                "transport_segments": [],
                "total_transport_time": 0,
                "total_activity_time": 0,
                "schedule": []
            }
        
        # 获取所有地点的坐标（只查数据库，不再用高德API）
        coords = {}
        for activity in activities:
            if activity.location not in coords:
                loc = Location.objects.filter(name=activity.location).first()
                if loc and loc.longitude and loc.latitude:
                    coords[activity.location] = f"{loc.longitude},{loc.latitude}"
                else:
                    raise ValueError(f"数据库未找到地点或缺少经纬度: {activity.location}")
        
        # 计算交通时间
        transport_details = []
        total_transport_time = 0
        
        for i in range(len(activities) - 1):
            if i < len(transport_segments):
                transport_mode = transport_segments[i]["mode"]
                mode = self.MODE_MAP.get(transport_mode)
                origin = coords[activities[i].location]
                dest = coords[activities[i + 1].location]
                real_mode = transport_mode
                duration = None
                # 智能选择
                if mode == "walking":
                    # 步行优先，超时或失败则智能选
                    try:
                        walk_sec = self.dir_api.shortest_walking_duration(origin, dest)
                        if walk_sec <= 25*60:
                            real_mode = "步行"
                            duration = walk_sec
                        else:
                            real_mode, duration = self._smart_select_transport_mode(origin, dest, city_hint)
                            print(f"[RouteTimeService] 步行超时，切换为{real_mode}，耗时{duration//60}分钟")
                    except Exception as e:
                        real_mode, duration = self._smart_select_transport_mode(origin, dest, city_hint)
                        print(f"[RouteTimeService] 步行失败({e})，切换为{real_mode}，耗时{duration//60}分钟")
                else:
                    # 其他方式按原有
                    try:
                        if mode == "walking":
                            duration = self.dir_api.shortest_walking_duration(origin, dest)
                        elif mode == "driving":
                            duration = self.dir_api.shortest_driving_duration(origin, dest)
                        elif mode == "bicycling":
                            duration = self.dir_api.shortest_bicycling_duration(origin, dest)
                        elif mode == "transit":
                            city = city_hint or self.geo_api.geocode(activities[i].location)["geocodes"][0]["citycode"]
                            duration = self.dir_api.shortest_transit_duration(origin, dest, city=city)
                        else:
                            raise ValueError(f"未实现的 mode: {mode}")
                        real_mode = transport_mode
                    except Exception as e:
                        real_mode, duration = self._smart_select_transport_mode(origin, dest, city_hint)
                        print(f"[RouteTimeService] {transport_mode}失败({e})，切换为{real_mode}，耗时{duration//60}分钟")
                # 兜底
                if duration is None:
                    real_mode, duration = self._smart_select_transport_mode(origin, dest, city_hint)
                    print(f"[RouteTimeService] 交通方式未知，兜底为{real_mode}，耗时{duration//60}分钟")
                transport_details.append({
                    "from": activities[i].location,
                    "to": activities[i + 1].location,
                    "mode": real_mode,
                    "duration": duration
                })
                total_transport_time += duration
        
        # 生成时间安排
        schedule = []
        current_time = dt.datetime.combine(date, dt.time(9, 0))  # 从9点开始
        
        for i, activity in enumerate(activities):
            # 添加活动
            activity_start = current_time
            activity_end = activity_start + dt.timedelta(minutes=activity.duration_minutes)
            
            schedule.append({
                "type": "activity",
                "start_time": activity_start.isoformat(),
                "end_time": activity_end.isoformat(),
                "location": activity.location,
                "name": activity.name,
                "duration_minutes": activity.duration_minutes
            })
            
            current_time = activity_end
            
            # 添加交通（除了最后一个活动）
            if i < len(transport_details):
                transport = transport_details[i]
                transport_start = current_time
                transport_end = transport_start + dt.timedelta(seconds=transport["duration"])
                
                schedule.append({
                    "type": "transport",
                    "start_time": transport_start.isoformat(),
                    "end_time": transport_end.isoformat(),
                    "from": transport["from"],
                    "to": transport["to"],
                    "mode": transport["mode"],
                    "duration": transport["duration"]
                })
                
                current_time = transport_end
        
        return {
            "day_number": day_plan.day_number,
            "date": date.isoformat(),
            "activities": [
                {
                    "location": a.location,
                    "name": a.name,
                    "duration_minutes": a.duration_minutes
                } for a in activities
            ],
            "transport_segments": transport_details,
            "total_transport_time": total_transport_time,
            "total_activity_time": sum(a.duration_minutes * 60 for a in activities),
            "schedule": schedule
        }

    # ---------- 兼容原有接口 ----------
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