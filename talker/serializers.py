from rest_framework import serializers
from .models import TalkSession

class TalkSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TalkSession
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'state'] 