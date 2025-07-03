from rest_framework import serializers
from .models import TalkSession, POIItem, POISession

class TalkSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TalkSession
        fields = [
            'id', 'user', 'history', 'budget', 'locations',
            'start_date', 'end_date', 'state', 'user_profile',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class POIItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = POIItem
        fields = '__all__'

class POISessionSerializer(serializers.ModelSerializer):
    poi = POIItemSerializer(read_only=True)
    
    class Meta:
        model = POISession
        fields = '__all__' 