import os
from django.conf import settings
 
# 获取配置文件路径
PROMPTS_CONFIG_PATH = os.path.join(settings.BASE_DIR, 'talker', 'config', 'prompts.json') 