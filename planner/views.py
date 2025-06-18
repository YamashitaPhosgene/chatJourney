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
        """
        获取行程的时间线。
        如果提供了day_index参数，则只返回指定天数的事件。
        day_index从1开始计数。
        """
        trip = self.get_object()
        events = Event.objects.filter(trip=trip)

        # 如果指定了天数，计算对应的日期
        if day_index is not None:
            try:
                day_index = int(day_index)
                if day_index < 1:
                    return Response(
                        {'detail': '天数必须大于0'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                target_date = trip.start_date + timedelta(days=day_index - 1)
                if target_date > trip.end_date:
                    return Response(
                        {'detail': f'指定的天数超出行程范围（共{(trip.end_date - trip.start_date).days + 1}天）'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                events = events.filter(date=target_date)
            except ValueError:
                return Response(
                    {'detail': '无效的天数参数'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # 按日期和时间排序
        events = events.order_by('date', 'start_time')

        # 准备时间线数据
        timeline = []
        for event in events:
            # 计算事件结束时间
            start_datetime = datetime.combine(event.date, event.start_time)
            end_datetime = start_datetime + event.duration

            # 根据事件类型选择合适的序列化器
            if isinstance(event, Activity):
                serializer = ActivitySerializer
            elif isinstance(event, Transport):
                serializer = TransportSerializer
            elif isinstance(event, Accommodation):
                serializer = AccommodationSerializer
            else:
                serializer = EventSerializer

            # 序列化事件数据
            event_data = serializer(event).data
            
            # 添加额外的时间信息
            event_data.update({
                'start_datetime': start_datetime.isoformat(),
                'end_datetime': end_datetime.isoformat(),
                'day_index': (event.date - trip.start_date).days + 1
            })
            
            timeline.append(event_data)

        # 准备响应数据
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
        """
        创建事件前验证时间范围是否在行程内
        """
        trip = get_object_or_404(Trip, pk=serializer.validated_data['trip'].id)
        event_date = serializer.validated_data['date']
        event_start_time = serializer.validated_data['start_time']
        event_duration = serializer.validated_data.get('duration', timedelta(hours=1))

        # 计算事件结束时间
        event_start_datetime = datetime.combine(event_date, event_start_time)
        event_end_datetime = event_start_datetime + event_duration

        # 计算行程的起止时间
        trip_start_datetime = datetime.combine(trip.start_date, time.min)  # 行程开始日期的0点
        trip_end_datetime = datetime.combine(trip.end_date, time.max)  # 行程结束日期的23:59:59

        # 验证事件时间是否在行程范围内
        if event_start_datetime < trip_start_datetime or event_end_datetime > trip_end_datetime:
            raise ValidationError({
                'detail': '事件时间必须在行程范围内。',
                'event_time': f'从 {event_start_datetime} 到 {event_end_datetime}',
                'trip_time': f'从 {trip_start_datetime} 到 {trip_end_datetime}'
            })

        serializer.save()

    def perform_update(self, serializer):
        """
        更新事件前验证时间范围是否在行程内
        """
        trip = serializer.instance.trip
        event_date = serializer.validated_data.get('date', serializer.instance.date)
        event_start_time = serializer.validated_data.get('start_time', serializer.instance.start_time)
        event_duration = serializer.validated_data.get('duration', serializer.instance.duration)

        # 计算事件结束时间
        event_start_datetime = datetime.combine(event_date, event_start_time)
        event_end_datetime = event_start_datetime + event_duration

        # 计算行程的起止时间
        trip_start_datetime = datetime.combine(trip.start_date, time.min)
        trip_end_datetime = datetime.combine(trip.end_date, time.max)

        # 验证事件时间是否在行程范围内
        if event_start_datetime < trip_start_datetime or event_end_datetime > trip_end_datetime:
            raise ValidationError({
                'detail': '事件时间必须在行程范围内。',
                'event_time': f'从 {event_start_datetime} 到 {event_end_datetime}',
                'trip_time': f'从 {trip_start_datetime} 到 {trip_end_datetime}'
            })

        serializer.save()


class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all().order_by('name')
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated]
