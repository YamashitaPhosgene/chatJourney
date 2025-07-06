# -*- coding: utf-8 -*-
"""Management command: create_sample_trips

生成符合 planner/models.py 结构的演示数据，方便前端联调：

>>> python manage.py create_sample_trips --user demo
"""

from datetime import date, time, timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from planner.models import (
    Trip,
    Day,
    Location,
    Activity,
    Transport,
    Accommodation,
)


class Command(BaseCommand):
    help = "Create sample Trip / Day / Event data strictly following planner models."

    def add_arguments(self, parser):
        parser.add_argument("--user", default="demo", help="用户名；不存在则创建")

    def handle(self, *args, **options):
        username = options["user"]
        user, _ = User.objects.get_or_create(username=username, defaults={"password": "demo"})

        self.stdout.write(self.style.WARNING(f"Using user {user.username} (id={user.id})"))

        # 删除旧示例
        Trip.objects.filter(user=user, title__startswith="示例Trip").delete()

        # -------- 样例 1：成都 3 日游 --------
        self._create_chengdu_trip(user)
        # -------- 样例 2：北京 2 日游 --------
        self._create_beijing_trip(user)

        self.stdout.write(self.style.SUCCESS("示例 Trip 已创建完毕！"))

    # ---------------------------------------------------------------------
    # 内部辅助
    # ---------------------------------------------------------------------

    @transaction.atomic
    def _create_chengdu_trip(self, user):
        start = date.today()
        trip = Trip.objects.create(
            user=user,
            title="示例Trip · 成都 3 日游",
            description="自动生成的示例行程：春熙路 / 太古里 / 宽窄巷子",
            start_date=start,
            end_date=start + timedelta(days=2),
        )

        # 统一地点
        locations = {
            "hotel": self._get_location("锦江宾馆", "hotel", 30.6537, 104.0758),
            "春熙路": self._get_location("春熙路", "sight", 30.657378, 104.082321),
            "太古里IFS": self._get_location("太古里IFS", "sight", 30.657689, 104.080989),
            "宽窄巷子": self._get_location("宽窄巷子", "sight", 30.671009, 104.060321),
            "海底捞春熙店": self._get_location("海底捞春熙店", "restaurant", 30.6571, 104.0829),
            "成都双流机场": self._get_location("成都双流国际机场", "transport", 30.5785, 103.9471),
        }

        for i in range(3):
            day_date = start + timedelta(days=i)
            day = Day.objects.create(trip=trip, date=day_date, day_index=i + 1)

            # --- 交通出发（第 1 天早上 & 第 3 天返回机场）---
            if i == 0:
                Transport.objects.create(
                    trip=trip,
                    date=day_date,
                    start_time=time(8, 0),
                    duration=timedelta(minutes=30),
                    title="前往春熙路",
                    location=locations["hotel"],
                    destination=locations["春熙路"],
                    mode="car",
                    type="departure",
                )
            elif i == 2:
                # 退房后去机场
                Transport.objects.create(
                    trip=trip,
                    date=day_date,
                    start_time=time(9, 0),
                    duration=timedelta(hours=1),
                    title="前往成都双流机场",
                    location=locations["hotel"],
                    destination=locations["成都双流机场"],
                    mode="car",
                    type="departure",
                )

            # --- 活动 & 餐饮 ---
            sight = ["春熙路", "太古里IFS", "宽窄巷子"][i % 3]
            Activity.objects.create(
                trip=trip,
                date=day_date,
                start_time=time(10, 0),
                duration=timedelta(hours=2),
                title=f"游览 {sight}",
                location=locations[sight],
                category="sightseeing",
            )

            Activity.objects.create(
                trip=trip,
                date=day_date,
                start_time=time(13, 0),
                duration=timedelta(hours=1, minutes=30),
                title="海底捞午餐",
                location=locations["海底捞春熙店"],
                category="dining",
            )

            # --- 住宿 ---
            if i == 0:
                acc = Accommodation.objects.create(
                    trip=trip,
                    date=day_date,
                    start_time=time(18, 0),
                    duration=timedelta(hours=12),
                    title="入住锦江宾馆",
                    location=locations["hotel"],
                    type="checkin",
                )
            elif i == 1:
                acc = Accommodation.objects.create(
                    trip=trip,
                    date=day_date,
                    start_time=time(18, 0),
                    duration=timedelta(hours=12),
                    title="酒店休息",
                    location=locations["hotel"],
                    type="stay",
                )
            else:
                acc = Accommodation.objects.create(
                    trip=trip,
                    date=day_date,
                    start_time=time(7, 0),
                    duration=timedelta(hours=1),
                    title="退房",
                    location=locations["hotel"],
                    type="checkout",
                )

        self.stdout.write(self.style.SUCCESS(f"✓ 成都示例 Trip(id={trip.id}) 完成"))

    @transaction.atomic
    def _create_beijing_trip(self, user):
        start = date.today() + timedelta(days=10)
        trip = Trip.objects.create(
            user=user,
            title="示例Trip · 北京 2 日游",
            description="自动生成的示例行程：故宫 / 天安门 / 王府井",
            start_date=start,
            end_date=start + timedelta(days=1),
        )

        locations = {
            "hotel": self._get_location("王府井大饭店", "hotel", 39.9086, 116.4123),
            "天安门广场": self._get_location("天安门广场", "sight", 39.9042, 116.4074),
            "故宫博物院": self._get_location("故宫博物院", "sight", 39.9163, 116.3972),
            "东来顺王府井": self._get_location("东来顺王府井店", "restaurant", 39.9087, 116.4109),
            "首都机场": self._get_location("北京首都国际机场", "transport", 40.0801, 116.5846),
        }

        for i in range(2):
            day_date = start + timedelta(days=i)
            Day.objects.create(trip=trip, date=day_date, day_index=i + 1)

            Activity.objects.create(
                trip=trip,
                date=day_date,
                start_time=time(9, 0),
                duration=timedelta(hours=2),
                title="天安门参观" if i == 0 else "故宫游览",
                location=locations["天安门广场" if i == 0 else "故宫博物院"],
                category="sightseeing",
            )

            Activity.objects.create(
                trip=trip,
                date=day_date,
                start_time=time(12, 0),
                duration=timedelta(hours=1, minutes=30),
                title="东来顺午餐",
                location=locations["东来顺王府井"],
                category="dining",
            )

            if i == 0:
                Accommodation.objects.create(
                    trip=trip,
                    date=day_date,
                    start_time=time(18, 0),
                    duration=timedelta(hours=12),
                    title="入住王府井大饭店",
                    location=locations["hotel"],
                    type="checkin",
                )
            else:
                Accommodation.objects.create(
                    trip=trip,
                    date=day_date,
                    start_time=time(6, 0),
                    duration=timedelta(hours=2),
                    title="退房并前往机场",
                    location=locations["hotel"],
                    type="checkout",
                )
                Transport.objects.create(
                    trip=trip,
                    date=day_date,
                    start_time=time(8, 30),
                    duration=timedelta(hours=1),
                    title="前往首都机场",
                    location=locations["hotel"],
                    destination=locations["首都机场"],
                    mode="car",
                    type="departure",
                )

        self.stdout.write(self.style.SUCCESS(f"✓ 北京示例 Trip(id={trip.id}) 完成"))

    # ------------------------------------------------------------------
    @staticmethod
    def _get_location(name: str, category: str, lat: float, lng: float):
        loc, _ = Location.objects.get_or_create(
            name=name,
            defaults={"category": category, "latitude": lat, "longitude": lng},
        )
        return loc 