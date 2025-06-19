from datetime import timedelta, datetime, time
from rest_framework.exceptions import ValidationError
from .models import Trip, Event, Activity, Transport, Accommodation

def get_trip_timeline(trip, day_index=None):
    events = Event.objects.filter(trip=trip)
    target_date = None
    if day_index is not None:
        day_index = int(day_index)
        if day_index < 1:
            raise ValidationError({'detail': '天数必须大于0'})
        target_date = trip.start_date + timedelta(days=day_index - 1)
        if target_date > trip.end_date:
            raise ValidationError({'detail': f'指定的天数超出行程范围（共{(trip.end_date - trip.start_date).days + 1}天）'})
        events = events.filter(date=target_date)
    events = events.order_by('date', 'start_time')
    timeline = []
    for event in events:
        start_datetime = datetime.combine(event.date, event.start_time)
        end_datetime = start_datetime + event.duration
        if isinstance(event, Activity):
            serializer = ActivitySerializer
        elif isinstance(event, Transport):
            serializer = TransportSerializer
        elif isinstance(event, Accommodation):
            serializer = AccommodationSerializer
        else:
            serializer = EventSerializer
        event_data = serializer(event).data
        event_data.update({
            'start_datetime': start_datetime.isoformat(),
            'end_datetime': end_datetime.isoformat(),
            'day_index': (event.date - trip.start_date).days + 1
        })
        timeline.append(event_data)
    response_data = {
        'trip': {
            'id': trip.id,
            'title': trip.title,
            'start_date': trip.start_date.isoformat(),
            'end_date': trip.end_date.isoformat(),
            'total_days': (trip.end_date - trip.start_date).days + 1
        },
        'timeline': timeline
    }
    if day_index is not None:
        response_data['current_day'] = {
            'index': day_index,
            'date': target_date.isoformat()
        }
    return response_data

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