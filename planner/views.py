# views.py

from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Prefetch
from datetime import timedelta, datetime
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from .models import (
    Trip,
    Day,
    Location,
    Activity,
    Transport,
    Accommodation,
)
from .serializers import (
    TripSerializer, TripDetailSerializer,
    DaySerializer, DayNestedCreateSerializer,
    ActivitySerializer, TransportSerializer,
    AccommodationSerializer,
    LocationSerializer
)


class TripViewSet(viewsets.ModelViewSet):
    queryset = Trip.objects.all().order_by('-created_at')
    serializer_class = TripSerializer

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TripDetailSerializer
        return TripSerializer

    def perform_create(self, serializer):
        trip = serializer.save(user=self.request.user)
        start = trip.start_date
        end = trip.end_date
        curr = start
        idx = 1
        while curr <= end:
            Day.objects.create(trip=trip, date=curr, day_index=idx, notes="")
            curr += timedelta(days=1)
            idx += 1

    @action(detail=True, methods=['POST'])
    def bulk_create_days(self, request, pk=None):
        trip = get_object_or_404(Trip, pk=pk)
        serializer = DayNestedCreateSerializer(data=request.data.get('days', []), many=True)
        serializer.is_valid(raise_exception=True)
        for day_data in serializer.validated_data:
            Day.objects.create(trip=trip, **day_data)
        return Response({'status': 'days created'}, status=status.HTTP_201_CREATED)


class DayViewSet(viewsets.ModelViewSet):
    queryset = Day.objects.all().order_by('trip', 'day_index')
    serializer_class = DaySerializer


class ActivityViewSet(viewsets.ModelViewSet):
    queryset = Activity.objects.all().order_by('day', 'start_time', 'sequence')
    serializer_class = ActivitySerializer


class TransportViewSet(viewsets.ModelViewSet):
    queryset = Transport.objects.all().order_by('departure_datetime')
    serializer_class = TransportSerializer


class AccommodationViewSet(viewsets.ModelViewSet):
    """
    create(): 根据 check-in/check-out 时间范围创建多个 Accommodation 实例，并返回所有创建的记录。
    """
    queryset = Accommodation.objects.all().order_by('day')
    serializer_class = AccommodationSerializer

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        trip_id = data.get('trip_id')
        location_id = data.get('location_id')
        check_in_str = data.get('check_in_datetime')
        check_out_str = data.get('check_out_datetime', None)

        if not trip_id or not location_id or not check_in_str:
            return Response(
                {'detail': 'trip_id, location_id, check_in_datetime 为必填'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            check_in_dt = datetime.fromisoformat(check_in_str)
        except ValueError:
            return Response({'detail': 'check_in_datetime 格式非法'}, status=status.HTTP_400_BAD_REQUEST)

        trip = get_object_or_404(Trip, pk=trip_id)
        # 计算入住日期范围
        start_date = check_in_dt.date()
        if check_out_str:
            try:
                check_out_dt = datetime.fromisoformat(check_out_str)
            except ValueError:
                return Response({'detail': 'check_out_datetime 格式非法'}, status=status.HTTP_400_BAD_REQUEST)
            end_date = check_out_dt.date()
        else:
            end_date = start_date

        days = []
        curr = start_date
        while curr <= end_date:
            # 查找对应的 Day
            day = get_object_or_404(Day, trip=trip, date=curr)
            days.append(day)
            curr += timedelta(days=1)

        location = get_object_or_404(Location, pk=location_id)
        cost = data.get('cost', None)
        notes = data.get('notes', '')

        created = []
        prev_instance = None
        for day in days:
            acc = Accommodation.objects.create(
                day=day,
                location=location,
                cost=cost,
                notes=notes
            )
            if prev_instance:
                acc.predecessor = prev_instance
                acc.save(update_fields=['predecessor'])
                prev_instance.successor = acc
                prev_instance.save(update_fields=['successor'])
            prev_instance = acc
            created.append(acc)

        # 对所有 created 列表进行序列化并返回
        out_serializer = self.get_serializer(created, many=True)
        return Response(out_serializer.data, status=status.HTTP_201_CREATED)


class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all().order_by('name')
    serializer_class = LocationSerializer
