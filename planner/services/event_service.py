from datetime import datetime, timedelta, time
from django.core.exceptions import ValidationError
from planner.models import Trip
from planner.serializers import EventSerializer, ActivitySerializer, TransportSerializer, AccommodationSerializer

class EventService:
    @staticmethod
    def validate_event_time(trip, event_date, event_start_time, event_duration):
        event_start_datetime = datetime.combine(event_date, event_start_time)
        event_end_datetime = event_start_datetime + event_duration
        trip_start_datetime = datetime.combine(trip.start_date, time.min)
        trip_end_datetime = datetime.combine(trip.end_date, time.max)
        if event_start_datetime < trip_start_datetime or event_end_datetime > trip_end_datetime:
            raise ValidationError({
                'detail': '事件时间必须在行程范围内。',
                'event_time': f'从 {event_start_datetime} 到 {event_end_datetime}',
                'trip_time': f'从 {trip_start_datetime} 到 {trip_end_datetime}'
            })

    @staticmethod
    def get_serializer_for_type(event_type):
        if event_type == 'activity':
            return ActivitySerializer
        elif event_type in ['departure', 'arrival']:
            return TransportSerializer
        elif event_type in ['checkin', 'checkout', 'stay']:
            return AccommodationSerializer
        return EventSerializer 