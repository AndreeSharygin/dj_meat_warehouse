from django.contrib import admin
from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'quantity', 'is_available', 'updated_at')
    list_filter = ('updated_at',)
    search_fields = ('name',)
    list_editable = ('price', 'quantity')
    list_per_page = 25
    date_hierarchy = 'updated_at'

# Скрыть django_celery_beat из админки
from django_celery_beat.models import (
    CrontabSchedule, IntervalSchedule,
    PeriodicTask, SolarSchedule,
)

for model in [CrontabSchedule, IntervalSchedule, PeriodicTask, SolarSchedule]:
    try:
        admin.site.unregister(model)
    except admin.sites.NotRegistered:
        pass