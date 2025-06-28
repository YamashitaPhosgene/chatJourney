from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json
import asyncio
from .services.xiaohongshu_service import XiaohongshuService

# Create your views here.

@method_decorator(csrf_exempt, name='dispatch')
class XiaohongshuLoginView(View):
    def post(self, request):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        service = XiaohongshuService()
        result = loop.run_until_complete(service.login())
        return JsonResponse({'result': result})

@method_decorator(csrf_exempt, name='dispatch')
class XiaohongshuSearchView(View):
    def post(self, request):
        data = json.loads(request.body.decode('utf-8'))
        keywords = data.get('keywords', '')
        limit = int(data.get('limit', 5))
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        service = XiaohongshuService()
        result = loop.run_until_complete(service.search_notes(keywords, limit))
        return JsonResponse({'result': result})

@method_decorator(csrf_exempt, name='dispatch')
class XiaohongshuNoteContentView(View):
    def post(self, request):
        data = json.loads(request.body.decode('utf-8'))
        url = data.get('url', '')
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        service = XiaohongshuService()
        result = loop.run_until_complete(service.get_note_content(url))
        return JsonResponse({'result': result})

@method_decorator(csrf_exempt, name='dispatch')
class XiaohongshuNoteCommentsView(View):
    def post(self, request):
        data = json.loads(request.body.decode('utf-8'))
        url = data.get('url', '')
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        service = XiaohongshuService()
        result = loop.run_until_complete(service.get_note_comments(url))
        return JsonResponse({'result': result})
