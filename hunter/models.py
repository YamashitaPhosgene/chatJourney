from django.db import models

# Create your models here.

class POICategory(models.Model):
    """
    高德官方 POI 分类码表
    code = 6 位数字，主键
    中文、英文三级分类均保留，方便中英查询
    """
    code = models.CharField("typecode", max_length=6, primary_key=True)

    big_cn  = models.CharField("大类(中文)", max_length=32, blank=True)
    mid_cn  = models.CharField("中类(中文)", max_length=32, blank=True)
    sub_cn  = models.CharField("小类(中文)", max_length=32, blank=True)

    big_en  = models.CharField("Big Category", max_length=64, blank=True)
    mid_en  = models.CharField("Mid  Category", max_length=64, blank=True)
    sub_en  = models.CharField("Sub Category", max_length=64, blank=True)

    class Meta:
        verbose_name = "POI分类"
        verbose_name_plural = "POI分类"
        indexes = [
            models.Index(fields=["big_cn", "mid_cn", "sub_cn"]),
            models.Index(fields=["big_en", "mid_en", "sub_en"]),
        ]

    def __str__(self):
        return f"{self.code} · {self.sub_cn or self.mid_cn or self.big_cn}"


class POIKeywordAlias(models.Model):
    """
    自定义同义词 → 官方 code
    如 'Citywalk' -> 110000
    """
    alias = models.CharField(max_length=64, unique=True)
    code  = models.CharField(max_length=6)

    class Meta:
        verbose_name = "POI关键词别名"
        verbose_name_plural = "POI关键词别名"
        indexes = [models.Index(fields=["alias"])]

    def __str__(self):
        return f"{self.alias} → {self.code}"
