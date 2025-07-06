from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# 创建路由器
router = DefaultRouter()
router.register(r'trips', views.TripViewSet)
router.register(r'events', views.EventViewSet)
router.register(r'activities', views.ActivityViewSet)
router.register(r'transports', views.TransportViewSet)
router.register(r'accommodations', views.AccommodationViewSet)
router.register(r'locations', views.LocationViewSet)
router.register(r'days', views.DayViewSet)

# URL模式
urlpatterns = [
    # REST API路由
    path('api/', include(router.urls)),

    # 自定义API端点
    path('api/convert-chain/', views.convert_chain_to_planner,
         name='convert_chain_to_planner'),
    path('api/trips/<int:trip_id>/markdown/',
         views.get_trip_markdown, name='get_trip_markdown'),
    path('api/trips/<int:trip_id>/json/',
         views.get_trip_json, name='get_trip_json'),
    path('api/trips/', views.list_user_trips, name='list_user_trips'),
]
