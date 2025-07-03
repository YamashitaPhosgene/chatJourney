from django.db import models
from django.contrib.auth.models import User

class TalkSession(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='talk_sessions')
    history = models.JSONField(default=list, help_text="对话历史记录")
    budget = models.CharField(max_length=50, null=True, blank=True, help_text="预算")
    locations = models.JSONField(default=list, help_text="地点列表")
    start_date = models.DateField(null=True, blank=True, help_text="第一天日期")
    end_date = models.DateField(null=True, blank=True, help_text="最后一天日期")
    state = models.JSONField(default=dict, blank=True, help_text="当前对话状态，包含阶段、意图等信息")
    user_profile = models.JSONField(default=dict, blank=True, help_text="用户画像，记录偏好、心情等信息")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"会话 {self.id} - 用户: {self.user.username}"


class POIItem(models.Model):
    """POI基础信息表（全局唯一）"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200, help_text="POI名称")
    poi_id = models.CharField(max_length=50, unique=True, help_text="高德POI ID")
    address = models.CharField(max_length=500, null=True, blank=True, help_text="地址")
    location = models.CharField(max_length=100, null=True, blank=True, help_text="经纬度坐标")
    type = models.CharField(max_length=100, null=True, blank=True, help_text="POI类型")
    tel = models.CharField(max_length=50, null=True, blank=True, help_text="电话")
    distance = models.CharField(max_length=50, null=True, blank=True, help_text="距离")
    raw_data = models.JSONField(default=dict, help_text="原始高德API数据")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.poi_id})"


class POISession(models.Model):
    """会话-POI关联表"""
    id = models.AutoField(primary_key=True)
    session = models.ForeignKey(TalkSession, on_delete=models.CASCADE, related_name='poi_sessions', help_text="关联的会话")
    poi = models.ForeignKey(POIItem, on_delete=models.CASCADE, related_name='session_relations', help_text="关联的POI")
    source = models.CharField(max_length=20, choices=[
        ('manual', '用户手动添加'),
        ('reverse_search', 'locations逆搜索'),
        ('keyword_search', '关键词搜索')
    ], help_text="POI来源")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['session', 'poi']  # 防止同一会话重复添加同一POI

    def __str__(self):
        return f"会话{self.session.id} - {self.poi.name} ({self.source})"


