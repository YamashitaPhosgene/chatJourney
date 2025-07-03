import json, pickle, os
from pathlib import Path
import numpy as np
import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from hunter.models import POICategory
from django.db import models
from chatJourney.utils.auth import AuthUtils

MODEL_NAME = "m3e-base"
OUT_FILE = Path("vector_cache/poi_vec.pkl")   # 自定目录
EMB_DIM_EXPECT = 768                     # m3e-base 输出 768 维

class Command(BaseCommand):
    help = "预编码高德官方小类名称向量（使用vivo Embedding API）"

    def handle(self, *args, **kwargs):
        self.stdout.write("读取数据库…")
        rows = POICategory.objects.filter(~models.Q(sub_cn="")).values_list(
            "sub_cn", "code"
        )  # 只用小类名

        self.stdout.write(f"编码 {len(rows)} 条…")
        vec_map = {}
        
        # 批量处理，每次最多50个
        batch_size = 50
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            names = [name for name, code in batch]
            
            try:
                # 调用vivo Embedding API
                payload = {"model_name": MODEL_NAME, "sentences": names}
                
                # 使用项目现有的AuthUtils进行鉴权
                uri = "/embedding-model-api/predict/batch"
                query = {}
                headers = AuthUtils.gen_sign_headers(settings.VIVO_APP_ID, settings.VIVO_APP_KEY, "POST", uri, query)
                headers["Content-Type"] = "application/json"
                
                url = f"https://api-ai.vivo.com.cn{uri}"
                url_with_params = f"{url}?{AuthUtils.gen_canonical_query_string(query)}"
                
                resp = requests.post(url_with_params, json=payload, headers=headers, timeout=30)
                resp.raise_for_status()
                vec_list: list[list[float]] = resp.json()["data"]
                
                # 保存向量
                for j, (name, code) in enumerate(batch):
                    vec = np.array(vec_list[j], dtype=np.float32)
                    if vec.shape[0] != EMB_DIM_EXPECT:
                        self.stdout.write(self.style.WARNING(f"向量维度异常：{vec.shape}"))
                        continue
                    vec_map[code] = vec
                
                self.stdout.write(f"已处理 {min(i + batch_size, len(rows))}/{len(rows)} 条")
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"批量处理失败: {e}"))
                continue

        OUT_FILE.parent.mkdir(exist_ok=True, parents=True)
        with open(OUT_FILE, "wb") as f:
            pickle.dump(vec_map, f)

        self.stdout.write(self.style.SUCCESS(
            f"完成！向量文件已保存 {OUT_FILE}，共 {len(vec_map)} 条")) 