# views.py

from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Prefetch
from datetime import timedelta, datetime, time
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import (
    Trip,
    Location,
    Event,
    Activity,
    Transport,
    Accommodation,
)
from .serializers import (
    TripSerializer,
    TripDetailSerializer,
    EventSerializer,
    ActivitySerializer,
    TransportSerializer,
    AccommodationSerializer,
    LocationSerializer
)
from .services import get_trip_timeline, validate_event_time


class TripViewSet(viewsets.ModelViewSet):
    queryset = Trip.objects.all().order_by('-created_at')
    serializer_class = TripSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TripDetailSerializer
        return TripSerializer

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    @action(detail=True, methods=['get'], url_path='timeline(?:/(?P<day_index>[0-9]+))?')
    def timeline(self, request, pk=None, day_index=None):
        trip = self.get_object()
        try:
            response_data = get_trip_timeline(trip, day_index)
            return Response(response_data)
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)


class EventViewSet(viewsets.ModelViewSet):
    """
    统一处理所有类型的事件（活动、交通、住宿）的API端点。
    根据事件类型自动选择对应的序列化器。
    """
    queryset = Event.objects.all().order_by('date', 'start_time')
    permission_classes = [IsAuthenticated]
    serializer_class = EventSerializer

    def get_queryset(self):
        return self.queryset.filter(trip__user=self.request.user)

    def get_serializer_class(self):
        # 如果是检索单个实例，根据实例类型选择序列化器
        if self.action in ['retrieve', 'update', 'partial_update'] and hasattr(self, 'get_object'):
            instance = self.get_object()
            return self._get_serializer_for_type(instance.type)
        
        # 如果是创建新实例，根据请求数据中的类型选择序列化器
        if self.action == 'create':
            event_type = self.request.data.get('type', '')
            return self._get_serializer_for_type(event_type)
            
        # 如果是列表视图，使用基础序列化器
        return EventSerializer

    def _get_serializer_for_type(self, event_type):
        """
        根据事件类型返回对应的序列化器
        """
        if event_type == 'activity':
            return ActivitySerializer
        elif event_type in ['departure', 'arrival']:
            return TransportSerializer
        elif event_type in ['checkin', 'checkout', 'stay']:
            return AccommodationSerializer
        return EventSerializer

    def perform_create(self, serializer):
        trip = get_object_or_404(Trip, pk=serializer.validated_data['trip'].id)
        event_date = serializer.validated_data['date']
        event_start_time = serializer.validated_data['start_time']
        event_duration = serializer.validated_data.get('duration', timedelta(hours=1))
        validate_event_time(trip, event_date, event_start_time, event_duration)
        serializer.save()

    def perform_update(self, serializer):
        trip = serializer.instance.trip
        event_date = serializer.validated_data.get('date', serializer.instance.date)
        event_start_time = serializer.validated_data.get('start_time', serializer.instance.start_time)
        event_duration = serializer.validated_data.get('duration', serializer.instance.duration)
        validate_event_time(trip, event_date, event_start_time, event_duration)
        serializer.save()


class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all().order_by('name')
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated]
