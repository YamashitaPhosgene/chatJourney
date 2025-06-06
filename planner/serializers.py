# serializers.py

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Trip,
    Day,
    Location,
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


class ActivitySerializer(serializers.ModelSerializer):
    day = serializers.PrimaryKeyRelatedField(read_only=True)
    trip_id = serializers.PrimaryKeyRelatedField(
        queryset=Trip.objects.all(),
        write_only=True
    )
    date = serializers.DateField(write_only=True)

    location = LocationSerializer(read_only=True)
    location_id = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(),
        source='location',
        write_only=True,
        required=False,
        allow_null=True
    )

    class Meta:
        model = Activity
        fields = [
            'id',
            'day',
            'trip_id',
            'date',
            'title',
            'description',
            'start_time',
            'end_time',
            'location',
            'location_id',
            'sequence',
            'cost',
            'category',
            'notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['day', 'created_at', 'updated_at']

    def create(self, validated_data):
        trip = validated_data.pop('trip_id')
        date = validated_data.pop('date')
        day = Day.objects.get(trip=trip, date=date)
        validated_data['day'] = day
        return super().create(validated_data)


class TransportSerializer(serializers.ModelSerializer):
    day = serializers.PrimaryKeyRelatedField(read_only=True)
    trip_id = serializers.PrimaryKeyRelatedField(
        queryset=Trip.objects.all(),
        write_only=True
    )

    from_location = LocationSerializer(read_only=True)
    to_location = LocationSerializer(read_only=True)
    from_location_id = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(),
        source='from_location',
        write_only=True,
        required=False,
        allow_null=True
    )
    to_location_id = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(),
        source='to_location',
        write_only=True,
        required=False,
        allow_null=True
    )

    class Meta:
        model = Transport
        fields = [
            'id',
            'day',
            'trip_id',
            'mode',
            'from_location',
            'from_location_id',
            'to_location',
            'to_location_id',
            'departure_datetime',
            'arrival_datetime',
            'cost',
            'notes',
        ]
        read_only_fields = ['day']

    def create(self, validated_data):
        trip = validated_data.pop('trip_id')
        dep = validated_data.get('departure_datetime')
        day = Day.objects.get(trip=trip, date=dep.date())
        validated_data['day'] = day
        return super().create(validated_data)


class AccommodationSerializer(serializers.ModelSerializer):
    day = serializers.PrimaryKeyRelatedField(read_only=True)

    trip_id = serializers.PrimaryKeyRelatedField(
        queryset=Trip.objects.all(),
        write_only=True
    )
    location = LocationSerializer(read_only=True)
    location_id = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(),
        source='location',
        write_only=True
    )

    check_in_datetime = serializers.DateTimeField(write_only=True)
    check_out_datetime = serializers.DateTimeField(write_only=True, required=False, allow_null=True)

    cost = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    notes = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Accommodation
        fields = [
            'id',
            'day',
            'trip_id',
            'location',
            'location_id',
            'check_in_datetime',
            'check_out_datetime',
            'cost',
            'notes',
        ]
        read_only_fields = ['day']


class DaySerializer(serializers.ModelSerializer):
    activities = ActivitySerializer(many=True, read_only=True)
    transports = TransportSerializer(many=True, read_only=True)
    accommodations = AccommodationSerializer(many=True, read_only=True)

    class Meta:
        model = Day
        fields = [
            'id',
            'trip',
            'date',
            'day_index',
            'notes',
            'activities',
            'transports',
            'accommodations',
        ]


class DayNestedCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Day
        fields = ['date', 'day_index', 'notes']


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
    days = DaySerializer(many=True, read_only=True)

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
            'days',
        ]
