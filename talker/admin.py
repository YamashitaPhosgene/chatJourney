from django.contrib import admin
from .models import TalkSession, POIItem, POISession

@admin.register(TalkSession)
class TalkSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'budget', 'start_date', 'end_date', 'created_at']
    list_filter = ['created_at', 'start_date', 'end_date']
    search_fields = ['user__username', 'budget', 'locations']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('user', 'budget', 'start_date', 'end_date')
        }),
        ('地点信息', {
            'fields': ('locations',)
        }),
        ('状态信息', {
            'fields': ('state', 'user_profile')
        }),
        ('对话历史', {
            'fields': ('history',),
            'classes': ('collapse',)
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(POIItem)
class POIItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'poi_id', 'type', 'address', 'created_at']
    list_filter = ['type', 'created_at']
    search_fields = ['name', 'address', 'poi_id']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'poi_id', 'type')
        }),
        ('位置信息', {
            'fields': ('address', 'location', 'distance')
        }),
        ('详细信息', {
            'fields': ('tel',)
        }),
        ('原始数据', {
            'fields': ('raw_data',),
            'classes': ('collapse',)
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(POISession)
class POISessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'session', 'poi', 'source', 'created_at']
    list_filter = ['source', 'created_at']
    search_fields = ['session__id', 'poi__name', 'poi__poi_id']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('关联信息', {
            'fields': ('session', 'poi', 'source')
        }),
        ('时间信息', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
