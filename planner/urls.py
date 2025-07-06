from rest_framework.routers import DefaultRouter
from django.urls import path, include

from .views import TripViewSet, EventViewSet, LocationViewSet

router = DefaultRouter()
router.register(r'trips', TripViewSet, basename='planner-trip')
router.register(r'events', EventViewSet, basename='planner-event')
router.register(r'locations', LocationViewSet, basename='planner-location')

urlpatterns = [
    # Expose router URLs
    *router.urls,
] 