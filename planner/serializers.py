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
        validated_data['type'] = 'activity'
        return super().create(validated_data)

    def to_representation(self, instance):
        # 确保instance是Activity类型
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

    def create(self, validated_data):
        event_type = self.context.get('event_type', 'departure')
        validated_data['type'] = event_type
        return super().create(validated_data)

    def to_representation(self, instance):
        # 确保instance是Transport类型
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

    def create(self, validated_data):
        event_type = self.context.get('event_type', 'stay')
        validated_data['type'] = event_type
        return super().create(validated_data)

    def to_representation(self, instance):
        # 确保instance是Accommodation类型
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
        ]

    def get_events(self, obj):
        """
        返回按日期和时间排序的所有事件
        使用select_subclasses()确保获取到正确的子类实例
        """
        events = Event.objects.filter(trip=obj).select_subclasses().order_by('date', 'start_time')
        serialized_events = []
        
        for event in events:
            if isinstance(event, Activity):
                serializer = ActivitySerializer(event)
            elif isinstance(event, Transport):
                serializer = TransportSerializer(event)
            elif isinstance(event, Accommodation):
                serializer = AccommodationSerializer(event)
            else:
                serializer = EventSerializer(event)
            
            serialized_events.append(serializer.data)
        
        return serialized_events
