from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    fields = ('product', 'product_name', 'quantity', 'price', 'original_quantity', 'get_item_cost')
    readonly_fields = ('get_item_cost',)

    @admin.display(description='Стоимость (₽)')
    def get_item_cost(self, obj):
        if obj.pk:
            return f'{obj.item_cost} ₽'
        return '—'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('pk', 'client', 'shipment_date', 'status', 'get_adjusted', 'get_admin_created', 'get_total', 'created_at')
    list_filter = ('status', 'shipment_date', 'created_at', 'created_by_admin')
    search_fields = ('client__name', 'client__email', 'pk')
    list_display_links = ('pk', 'client')
    readonly_fields = ('created_at', 'get_total_detail', 'get_total_no_discount')
    inlines = [OrderItemInline]
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Основное', {'fields': ('client', 'shipment_date', 'status', 'created_by_admin')}),
        ('Комментарии', {'fields': ('comment', 'manager_note')}),
        ('Информация', {'fields': ('get_total_detail', 'get_total_no_discount', 'created_at')}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('client')

    @admin.display(description='Скорректирована', boolean=True)
    def get_adjusted(self, obj):
        return obj.was_adjusted

    @admin.display(description='От админа', boolean=True)
    def get_admin_created(self, obj):
        return obj.created_by_admin

    @admin.display(description='Сумма (₽)')
    def get_total(self, obj):
        return f'{obj.total_cost} ₽'

    @admin.display(description='Итого (со скидкой)')
    def get_total_detail(self, obj):
        return f'{obj.total_cost} ₽'

    @admin.display(description='Итого (без скидки)')
    def get_total_no_discount(self, obj):
        return f'{obj.total_cost_without_discount} ₽'

    def save_model(self, request, obj, form, change):
        """При создании заявки через админку — автоматически ставим пометку."""
        if not change:  # новая заявка
            obj.created_by_admin = True
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        """Сохраняем товары — при создании через админку заполняем product_name и price из product."""
        instances = formset.save(commit=False)
        for instance in instances:
            if instance.product and not instance.product_name:
                instance.product_name = instance.product.name
            if instance.product and not instance.price:
                instance.price = instance.product.price
            instance.save()
        formset.save_m2m()
        for obj in formset.deleted_objects:
            obj.delete()


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product_name', 'quantity', 'original_quantity', 'get_adjusted', 'price', 'get_cost')
    list_filter = ('order__status',)
    search_fields = ('product_name', 'order__pk')

    @admin.display(description='Изменено', boolean=True)
    def get_adjusted(self, obj):
        return obj.was_adjusted

    @admin.display(description='Стоимость (₽)')
    def get_cost(self, obj):
        return f'{obj.item_cost} ₽'


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
