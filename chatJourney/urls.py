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
from talker.views import (
    ChatView,
    ChatHistoryView,
    TalkSessionViewSet,
    SessionView,
    StateMachineView,
    ChatStreamView,
)
from hunter.views import XiaohongshuLoginView, XiaohongshuSearchView, XiaohongshuNoteContentView, XiaohongshuNoteCommentsView

router = DefaultRouter()
router.register(r'trips', planner_views.TripViewSet, basename='trip')
router.register(r'events', planner_views.EventViewSet, basename='event')
router.register(r'locations', planner_views.LocationViewSet, basename='location')
router.register(r'talk_sessions', TalkSessionViewSet, basename='talksession')

urlpatterns = [
    path("admin/", admin.site.urls),
    path('api/', include(router.urls)),
    path('api/chat/', ChatView.as_view(), name='chat'),
    path('api/chat/history/', ChatHistoryView.as_view(), name='chat_history'),
    path('api/message/', StateMachineView.as_view(), name='message'),
    path('api/message/stream/', ChatStreamView.as_view(), name='message_stream'),
    path('api/session/', SessionView.as_view(), name='session'),
    path('api/session/<str:session_id>/', SessionView.as_view(), name='session_detail'),
    path('api/hunter/', include('hunter.urls')),
    path('api/talker/', include('talker.urls')),
]
