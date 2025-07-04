from django.urls import path
from .views import xiaohongshu_summary, StateMachineView, SessionView, ChatStreamView
 
urlpatterns = [
    path('xhs/summary/', xiaohongshu_summary, name='xhs_summary'),
    path('state-machine/', StateMachineView.as_view(), name='state_machine'),
    path('session/', SessionView.as_view(), name='session'),
    path('session/<str:session_id>/', SessionView.as_view(), name='session_detail'),
    path('chat/stream/', ChatStreamView.as_view(), name='chat_stream'),
] 