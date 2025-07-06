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
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
import json
from datetime import date
from .services.chain_to_planner_service import ChainToPlannerService

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

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TripDetailSerializer
        return TripSerializer

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

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
        event_duration = serializer.validated_data.get(
            'duration', timedelta(hours=1))
        EventService.validate_event_time(
            trip, event_date, event_start_time, event_duration)
        serializer.save()

    def perform_update(self, serializer):
        trip = serializer.instance.trip
        event_date = serializer.validated_data.get(
            'date', serializer.instance.date)
        event_start_time = serializer.validated_data.get(
            'start_time', serializer.instance.start_time)
        event_duration = serializer.validated_data.get(
            'duration', serializer.instance.duration)
        EventService.validate_event_time(
            trip, event_date, event_start_time, event_duration)
        serializer.save()


class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all().order_by('name')
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated]


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def convert_chain_to_planner(request):
    """
    将itinerary_chain转换为planner数据结构的API端点
    """
    try:
        # 解析请求数据
        data = json.loads(request.body)

        # 验证必需字段
        if 'itinerary_chain' not in data:
            return JsonResponse({
                'success': False,
                'error': '缺少必需字段: itinerary_chain'
            }, status=400)

        itinerary_chain = data['itinerary_chain']
        trip_title = data.get('trip_title', '旅行计划')
        trip_description = data.get('trip_description', '')
        start_date_str = data.get('start_date')

        # 解析开始日期
        start_date = None
        if start_date_str:
            try:
                start_date = date.fromisoformat(start_date_str)
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'error': '开始日期格式错误，请使用YYYY-MM-DD格式'
                }, status=400)

        # 创建服务实例并转换
        service = ChainToPlannerService()
        result = service.convert_chain_to_planner(
            itinerary_chain=itinerary_chain,
            user=request.user,
            trip_title=trip_title,
            trip_description=trip_description,
            start_date=start_date
        )

        if result['success']:
            # 返回成功结果
            return JsonResponse({
                'success': True,
                'trip_id': result['trip'].id,
                'summary': result['summary'],
                'message': '行程转换成功'
            })
        else:
            # 返回错误结果
            return JsonResponse({
                'success': False,
                'error': result['error'],
                'error_type': result.get('error_type', 'Unknown')
            }, status=500)

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': '请求数据格式错误，请提供有效的JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'服务器内部错误: {str(e)}'
        }, status=500)


@require_http_methods(["GET"])
@login_required
def get_trip_markdown(request, trip_id):
    """
    获取Trip的markdown格式数据
    """
    try:
        from .models import Trip

        # 获取Trip对象
        trip = Trip.objects.get(id=trip_id, user=request.user)

        # 生成markdown
        service = ChainToPlannerService()
        markdown_content = service.get_planner_data_as_markdown(trip)

        return JsonResponse({
            'success': True,
            'trip_id': trip_id,
            'markdown': markdown_content
        })

    except Trip.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Trip不存在或无权限访问'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'服务器内部错误: {str(e)}'
        }, status=500)


@require_http_methods(["GET"])
@login_required
def get_trip_json(request, trip_id):
    """
    获取Trip的JSON格式数据
    """
    try:
        from .models import Trip

        # 获取Trip对象
        trip = Trip.objects.get(id=trip_id, user=request.user)

        # 导出JSON
        service = ChainToPlannerService()
        json_data = service.export_trip_to_json(trip)

        return JsonResponse({
            'success': True,
            'trip_id': trip_id,
            'data': json_data
        })

    except Trip.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Trip不存在或无权限访问'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'服务器内部错误: {str(e)}'
        }, status=500)


@require_http_methods(["GET"])
@login_required
def list_user_trips(request):
    """
    获取用户的所有Trip列表
    """
    try:
        from .models import Trip

        trips = Trip.objects.filter(user=request.user).order_by('-created_at')

        trip_list = []
        for trip in trips:
            trip_list.append({
                'id': trip.id,
                'title': trip.title,
                'description': trip.description,
                'start_date': trip.start_date.isoformat(),
                'end_date': trip.end_date.isoformat(),
                'created_at': trip.created_at.isoformat(),
                'updated_at': trip.updated_at.isoformat()
            })

        return JsonResponse({
            'success': True,
            'trips': trip_list,
            'total': len(trip_list)
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'服务器内部错误: {str(e)}'
        }, status=500)
