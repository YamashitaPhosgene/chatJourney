"""
URL configuration for chatJourney project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from planner import views as planner_views

router = DefaultRouter()
router.register(r'trips', planner_views.TripViewSet, basename='trip')
router.register(r'days', planner_views.DayViewSet, basename='day')
router.register(r'activities', planner_views.ActivityViewSet, basename='activity')
router.register(r'transports', planner_views.TransportViewSet, basename='transport')
router.register(r'accommodations', planner_views.AccommodationViewSet, basename='accommodation')
router.register(r'locations', planner_views.LocationViewSet, basename='location')

urlpatterns = [
    path("admin/", admin.site.urls),
    path('api/', include(router.urls)),
]
