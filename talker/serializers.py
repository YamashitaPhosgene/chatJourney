from rest_framework import serializers
from .models import TalkSession

class TalkSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TalkSession
        fields = [
            'id', 'user', 'history', 'budget', 'locations', 'start_date', 'end_date', 'state', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'state'] 