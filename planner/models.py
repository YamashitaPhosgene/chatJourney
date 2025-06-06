# models.py

from django.db import models
from django.contrib.auth.models import User

class Trip(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trips')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Day(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='days')
    date = models.DateField()
    day_index = models.PositiveIntegerField()
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = (('trip', 'day_index'), ('trip', 'date'))
        ordering = ['trip', 'day_index']

    def __str__(self):
        return f"{self.trip.title} - Day {self.day_index} ({self.date})"


class Location(models.Model):
    CATEGORY_CHOICES = [
        ('sight', '景点'),
        ('hotel', '酒店'),
        ('restaurant', '餐厅'),
        ('transport', '交通枢纽'),
        ('custom', '自定义'),
    ]
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=300, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='custom')
    phone = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Activity(models.Model):
    CATEGORY_CHOICES = [
        ('sightseeing', '游览'),
        ('dining', '餐饮'),
        ('transport', '交通'),
        ('rest', '休息'),
        ('free', '自由活动'),
        ('custom', '自定义'),
    ]
    day = models.ForeignKey(Day, on_delete=models.CASCADE, related_name='activities')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)
    sequence = models.PositiveIntegerField(default=0)
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='custom')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['day', 'start_time', 'sequence']

    def __str__(self):
        return f"{self.day} - {self.title}"


class Transport(models.Model):
    MODE_CHOICES = [
        ('fly', '飞机'),
        ('train', '火车'),
        ('bus', '大巴'),
        ('metro', '地铁'),
        ('taxi', '出租'),
        ('car', '自驾'),
        ('other', '其他'),
    ]
    day = models.ForeignKey(Day, on_delete=models.CASCADE, related_name='transports')
    mode = models.CharField(max_length=20, choices=MODE_CHOICES)
    from_location = models.ForeignKey(
        Location, on_delete=models.SET_NULL, null=True, blank=True, related_name='transport_starts'
    )
    to_location = models.ForeignKey(
        Location, on_delete=models.SET_NULL, null=True, blank=True, related_name='transport_ends'
    )
    departure_datetime = models.DateTimeField()
    arrival_datetime = models.DateTimeField()
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['departure_datetime']

    def __str__(self):
        return (f"{self.day} | {self.mode} "
                f"{self.from_location.name if self.from_location else '未知'} → "
                f"{self.to_location.name if self.to_location else '未知'}")


class Accommodation(models.Model):
    """
    已移除 check_in_datetime/check_out_datetime 存储字段。
    自链式：一条记录表示同日住宿；前端只传入一次完整的 checkin/checkout
    后端拆分成每天一条并串成链。
    """
    day = models.ForeignKey(Day, on_delete=models.CASCADE, related_name='accommodations')
    location = models.ForeignKey(
        Location, on_delete=models.SET_NULL, null=True, blank=True
    )
    cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)

    predecessor = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='successor_accommodations'
    )
    successor = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='predecessor_accommodations'
    )

    class Meta:
        ordering = ['day']

    def __str__(self):
        loc_name = self.location.name if self.location else '未知地点'
        return f"{self.day} | {loc_name}，费用¥{self.cost or '0.00'}"
