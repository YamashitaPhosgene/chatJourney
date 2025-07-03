from django.urls import path
from .views import xiaohongshu_summary
 
urlpatterns = [
    path('xhs/summary/', xiaohongshu_summary, name='xhs_summary'),
] 