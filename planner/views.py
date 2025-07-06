# views.py

from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Prefetch
from datetime import timedelta, datetime, time
from rest_framework.permissions import IsAuthenticated, AllowAny
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
from planner.services.trip_service import TripService
from planner.services.event_service import EventService


class TripViewSet(viewsets.ModelViewSet):
    queryset = Trip.objects.all().order_by('-created_at')
    serializer_class = TripSerializer
    permission_classes = [IsAuthenticated]

    # 默认需要登录，但允许任何人 GET（retrieve/list）以便前端无需鉴权即可读取示例行程
    def get_permissions(self):
        if self.action in ["retrieve", "list"]:
            return [AllowAny()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TripDetailSerializer
        return TripSerializer

    def get_queryset(self):
        # 未登录时允许访问全部公开 Trip（示例数据）
        if self.request.user and self.request.user.is_authenticated:
            return self.queryset.filter(user=self.request.user)
        return self.queryset.filter(is_public=True)

    @action(detail=True, methods=['get'], url_path='timeline(?:/(?P<day_index>[0-9]+))?')
    def timeline(self, request, pk=None, day_index=None):
        trip = self.get_object()
        response_data = TripService.generate_timeline(trip, day_index)
        return Response(response_data)


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
        if self.action in ['retrieve', 'update', 'partial_update'] and hasattr(self, 'get_object'):
            instance = self.get_object()
            return EventService.get_serializer_for_type(instance.type)
        if self.action == 'create':
            event_type = self.request.data.get('type', '')
            return EventService.get_serializer_for_type(event_type)
        return EventSerializer

    def perform_create(self, serializer):
        trip = get_object_or_404(Trip, pk=serializer.validated_data['trip'].id)
        event_date = serializer.validated_data['date']
        event_start_time = serializer.validated_data['start_time']
        event_duration = serializer.validated_data.get('duration', timedelta(hours=1))
        EventService.validate_event_time(trip, event_date, event_start_time, event_duration)
        serializer.save()

    def perform_update(self, serializer):
        trip = serializer.instance.trip
        event_date = serializer.validated_data.get('date', serializer.instance.date)
        event_start_time = serializer.validated_data.get('start_time', serializer.instance.start_time)
        event_duration = serializer.validated_data.get('duration', serializer.instance.duration)
        EventService.validate_event_time(trip, event_date, event_start_time, event_duration)
        serializer.save()


class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all().order_by('name')
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated]
