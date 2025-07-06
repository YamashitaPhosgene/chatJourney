# serializers.py

from rest_framework import serializers
from django.contrib.auth.models import User
from model_utils.managers import InheritanceManager
from .models import (
    Trip,
    Location,
    Event,
    Activity,
    Transport,
    Accommodation,
)


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = [
            'id',
            'name',
            'address',
            'latitude',
            'longitude',
            'category',
            'phone',
            'notes',
        ]


class EventSerializer(serializers.ModelSerializer):
    location = LocationSerializer(read_only=True)
    location_id = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(),
        source='location',
        write_only=True,
        required=False,
        allow_null=True
    )

    class Meta:
        model = Event
        fields = [
            'id',
            'trip',
            'type',
            'date',
            'start_time',
            'duration',
            'cost',
            'location',
            'location_id',
            'title',
            'description',
            'notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class ActivitySerializer(EventSerializer):
    class Meta(EventSerializer.Meta):
        model = Activity
        fields = EventSerializer.Meta.fields + ['category']

    def create(self, validated_data):
        if 'type' not in validated_data:
            validated_data['type'] = 'activity'
        return super().create(validated_data)

    def to_representation(self, instance):
        if isinstance(instance, Event) and not isinstance(instance, Activity):
            instance = Activity.objects.get(pk=instance.pk)
        return super().to_representation(instance)


class TransportSerializer(EventSerializer):
    destination = LocationSerializer(read_only=True)
    destination_id = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(),
        source='destination',
        write_only=True,
        required=False,
        allow_null=True
    )

    class Meta(EventSerializer.Meta):
        model = Transport
        fields = EventSerializer.Meta.fields + [
            'mode',
            'destination',
            'destination_id',
        ]

    def to_representation(self, instance):
        if isinstance(instance, Event) and not isinstance(instance, Transport):
            instance = Transport.objects.get(pk=instance.pk)
        return super().to_representation(instance)


class AccommodationSerializer(EventSerializer):
    linked_accommodation = serializers.PrimaryKeyRelatedField(
        queryset=Accommodation.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta(EventSerializer.Meta):
        model = Accommodation
        fields = EventSerializer.Meta.fields + ['linked_accommodation']

    def to_representation(self, instance):
        if isinstance(instance, Event) and not isinstance(instance, Accommodation):
            instance = Accommodation.objects.get(pk=instance.pk)
        return super().to_representation(instance)


class TripSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = Trip
        fields = [
            'id',
            'user',
            'title',
            'description',
            'start_date',
            'end_date',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class TripDetailSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    events = serializers.SerializerMethodField()
    days = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = [
            'id',
            'user',
            'title',
            'description',
            'start_date',
            'end_date',
            'created_at',
            'updated_at',
            'events',
            'days',
        ]

    def _serialize_event(self, event):
            if isinstance(event, Activity):
                serializer = ActivitySerializer(event)
            elif isinstance(event, Transport):
                serializer = TransportSerializer(event)
            elif isinstance(event, Accommodation):
                serializer = AccommodationSerializer(event)
            else:
                serializer = EventSerializer(event)
            return serializer.data

    def get_events(self, obj):
        """按时间排序的所有事件（平铺）"""
        events = Event.objects.filter(trip=obj).select_subclasses().order_by('date', 'start_time')
        return [self._serialize_event(ev) for ev in events]

    def get_days(self, obj):
        """返回 days 数组，每天包含 events"""
        # 优先使用 Day 模型，如不存在则按照日期分组
        days_qs = obj.days.all().order_by('day_index')
        if days_qs.exists():
            result = []
            for day in days_qs:
                day_events = Event.objects.filter(trip=obj, date=day.date).select_subclasses().order_by('start_time')
                result.append({
                    'day_index': day.day_index,
                    'date': day.date,
                    'events': [self._serialize_event(ev) for ev in day_events]
                })
            return result

        # fallback: group by date
        events = Event.objects.filter(trip=obj).select_subclasses().order_by('date', 'start_time')
        grouped = {}
        for ev in events:
            grouped.setdefault(str(ev.date), []).append(self._serialize_event(ev))
        result = []
        for idx, (date_str, ev_list) in enumerate(grouped.items(), start=1):
            result.append({
                'day_index': idx,
                'date': date_str,
                'events': ev_list
            })
        return result
