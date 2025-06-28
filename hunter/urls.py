from django.urls import path
from .views import XiaohongshuLoginView, XiaohongshuSearchView, XiaohongshuNoteContentView, XiaohongshuNoteCommentsView

urlpatterns = [
    path('xhs/login/', XiaohongshuLoginView.as_view(), name='xhs_login'),
    path('xhs/search/', XiaohongshuSearchView.as_view(), name='xhs_search'),
    path('xhs/note_content/', XiaohongshuNoteContentView.as_view(), name='xhs_note_content'),
    path('xhs/note_comments/', XiaohongshuNoteCommentsView.as_view(), name='xhs_note_comments'),
] 