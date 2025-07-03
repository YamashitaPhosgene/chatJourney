from django.core.management.base import BaseCommand
from talker.models import TalkSession
from planner.services.timeline_service import TimelineService
from hunter.api.amap_api import AmapPlaceAPI, AmapDirectionAPI
import os

class Command(BaseCommand):
    help = '测试 TimelineService 市内交通slot自动插入功能'

    def add_arguments(self, parser):
        parser.add_argument('--session', type=int, help='TalkSession的ID')

    def handle(self, *args, **options):
        AMAP_KEY = os.environ.get('AMAP_KEY', 'your_amap_key_here')
        session_id = options.get('session')
        if session_id:
            try:
                session = TalkSession.objects.get(id=session_id)
            except TalkSession.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'未找到ID为{session_id}的TalkSession'))
                return
        else:
            self.stdout.write(self.style.ERROR('请通过 --session 指定要测试的 TalkSession ID'))
            return

        place_api = AmapPlaceAPI(AMAP_KEY)
        dir_api = AmapDirectionAPI(AMAP_KEY)
        service = TimelineService(place_api, dir_api)
        slots = service.build_timeline(session)
        for slot in slots:
            self.stdout.write(f"{slot.start.strftime('%Y-%m-%d %H:%M')} - {slot.end.strftime('%H:%M')} | {slot.type} | {slot.title}")
            if slot.type == 'transfer':
                self.stdout.write(self.style.WARNING('  (交通slot已自动插入)')) 