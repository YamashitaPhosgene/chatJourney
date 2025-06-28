from datetime import timedelta, datetime
from planner.models import Event, Activity, Transport, Accommodation
from planner.serializers import EventSerializer, ActivitySerializer, TransportSerializer, AccommodationSerializer

class TripService:
    @staticmethod
    def generate_timeline(trip, day_index=None):
        events = Event.objects.filter(trip=trip)
        target_date = None
        if day_index is not None:
            day_index = int(day_index)
            target_date = trip.start_date + timedelta(days=day_index - 1)
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
        if day_index is not None and target_date is not None:
            response_data['current_day'] = {
                'index': day_index,
                'date': target_date.isoformat()
            }
        return response_data 