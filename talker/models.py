from django.db import models
from django.contrib.auth.models import User

class TalkSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='talk_sessions')
    history = models.JSONField(default=list, help_text="对话历史记录")
    budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="预算")
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


