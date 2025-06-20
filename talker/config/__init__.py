import os
from django.conf import settings
import yaml
import json

# 获取配置文件路径
PROMPTS_YAML_PATH = os.path.join(settings.BASE_DIR, 'talker', 'config', 'prompts.yaml')
PROMPTS_JSON_PATH = os.path.join(settings.BASE_DIR, 'talker', 'config', 'prompts.json')

def load_prompts():
    if os.path.exists(PROMPTS_YAML_PATH):
        with open(PROMPTS_YAML_PATH, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    elif os.path.exists(PROMPTS_JSON_PATH):
        with open(PROMPTS_JSON_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        return {} 