from django.urls import path
from .views import (
    xiaohongshu_summary, StateMachineView, SessionView, ChatStreamView, 
    DestinationRecommendationView, AddPOIView, RemovePOIView, ListPOIView, 
    BudgetAnalysisView, state_machine_api, timeline_api, session_state_api
)
 
urlpatterns = [
    path('xhs/summary/', xiaohongshu_summary, name='xhs_summary'),
    path('state-machine/', StateMachineView.as_view(), name='state_machine'),
    path('state-machine/', state_machine_api, name='state_machine_api'),
    path('timeline/<str:session_id>/', timeline_api, name='timeline_api'),
    path('session/', SessionView.as_view(), name='session'),
    path('session/<str:session_id>/', SessionView.as_view(), name='session_detail'),
    path('session/<str:session_id>/', session_state_api, name='session_state_api'),
    path('chat/stream/', ChatStreamView.as_view(), name='chat_stream'),
    path('recommendations/destinations/', DestinationRecommendationView.as_view(), name='destination_recommendations'),
    path('recommendations/destinations/<str:session_id>/', DestinationRecommendationView.as_view(), name='destination_recommendations_with_session'),
    path('pois/add/', AddPOIView.as_view(), name='add_poi'),
    path('pois/remove/', RemovePOIView.as_view(), name='remove_poi'),
    path('pois/list/', ListPOIView.as_view(), name='list_pois'),
    path('budget/analysis/', BudgetAnalysisView.as_view(), name='budget_analysis'),
] 