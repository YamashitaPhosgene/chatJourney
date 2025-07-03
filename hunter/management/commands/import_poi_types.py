import pandas as pd
from django.core.management.base import BaseCommand
from django.conf import settings
from hunter.models import POICategory

class Command(BaseCommand):
    """
    导入高德官方 POI 分类码表
    用法:
        python manage.py import_poi_types --file=/绝对路径/xxx.xlsx --truncate
    """
    help = "Import AMap POI typecodes from Excel"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file", required=True,
            help="Excel 文件路径"
        )
        parser.add_argument(
            "--truncate", action="store_true",
            help="先清空 hunter_poiCategory 表"
        )

    def handle(self, *args, **options):
        path = options["file"]
        df = pd.read_excel(path, sheet_name=0)

        colmap = {
            "NEW_TYPE": "code",
            "大类": "big_cn",
            "中类": "mid_cn",
            "小类": "sub_cn",
            "Big Category": "big_en",
            "Mid  Category": "mid_en",
            "Sub Category": "sub_en",
        }
        df = df.rename(columns=colmap)[colmap.values()]
        df["code"] = df["code"].astype(str).str.zfill(6)

        if options["truncate"]:
            POICategory.objects.all().delete()

        objs = [
            POICategory(**row._asdict())
            for row in df.itertuples(index=False)
        ]
        POICategory.objects.bulk_create(objs, batch_size=1000)

        self.stdout.write(
            self.style.SUCCESS(f"导入完成，共 {len(objs)} 条")
        ) 