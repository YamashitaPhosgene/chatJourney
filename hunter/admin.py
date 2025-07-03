from django.contrib import admin
from hunter.models import POICategory, POIKeywordAlias

# Register your models here.

@admin.register(POICategory)
class POICategoryAdmin(admin.ModelAdmin):
    """POI分类管理"""
    list_display = ['code', 'big_cn', 'mid_cn', 'sub_cn', 'big_en', 'mid_en', 'sub_en']
    list_filter = ['big_cn', 'mid_cn']
    search_fields = ['code', 'big_cn', 'mid_cn', 'sub_cn', 'big_en', 'mid_en', 'sub_en']
    ordering = ['code']
    readonly_fields = ['code']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('code',)
        }),
        ('中文分类', {
            'fields': ('big_cn', 'mid_cn', 'sub_cn')
        }),
        ('英文分类', {
            'fields': ('big_en', 'mid_en', 'sub_en')
        }),
    )


@admin.register(POIKeywordAlias)
class POIKeywordAliasAdmin(admin.ModelAdmin):
    """POI关键词别名管理"""
    list_display = ['alias', 'code', 'get_category_info']
    list_filter = ['code']
    search_fields = ['alias', 'code']
    ordering = ['alias']
    
    def get_category_info(self, obj):
        """获取分类信息"""
        try:
            category = POICategory.objects.get(code=obj.code)
            return f"{category.sub_cn or category.mid_cn or category.big_cn}"
        except POICategory.DoesNotExist:
            return "未知分类"
    get_category_info.short_description = "分类名称"
