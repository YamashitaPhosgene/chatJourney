# models.py

from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta
from model_utils.managers import InheritanceManager

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


class Event(models.Model):
    EVENT_TYPES = [
        ('activity', '活动'),
        ('departure', '出发'),
        ('arrival', '到达'),
        ('checkin', '入住'),
        ('checkout', '退房'),
        ('stay', '住宿'),
    ]

    objects = InheritanceManager()

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='events')
    type = models.CharField(max_length=20, choices=EVENT_TYPES)
    date = models.DateField()
    start_time = models.TimeField()
    duration = models.DurationField(default=timedelta(hours=1))
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    location = models.ForeignKey('Location', on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"{self.date} {self.start_time} - {self.title}"


class Activity(Event):
    CATEGORY_CHOICES = [
        ('sightseeing', '游览'),
        ('dining', '餐饮'),
        ('transport', '交通'),
        ('rest', '休息'),
        ('free', '自由活动'),
        ('custom', '自定义'),
    ]
    
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='custom')

    def save(self, *args, **kwargs):
        self.type = 'activity'
        super().save(*args, **kwargs)


class Transport(Event):
    MODE_CHOICES = [
        ('fly', '飞机'),
        ('train', '火车'),
        ('bus', '大巴'),
        ('metro', '地铁'),
        ('taxi', '出租'),
        ('car', '自驾'),
        ('other', '其他'),
    ]
    
    mode = models.CharField(max_length=20, choices=MODE_CHOICES)
    destination = models.ForeignKey(
        'Location', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='transport_destinations'
    )

    def save(self, *args, **kwargs):
        if not hasattr(self, 'type') or not self.type:
            self.type = 'departure'  # 默认为departure，可以在创建时指定为arrival
        super().save(*args, **kwargs)


class Accommodation(Event):
    linked_accommodation = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='related_accommodations'
    )

    def save(self, *args, **kwargs):
        if not hasattr(self, 'type') or not self.type:
            self.type = 'stay'  # 默认为stay，可以在创建时指定为checkin或checkout
        super().save(*args, **kwargs)


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
