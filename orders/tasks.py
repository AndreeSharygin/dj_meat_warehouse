from django.utils import timezone
from celery import shared_task
from orders.services import send_rating_restored_email


@shared_task
def check_shipment_dates():
    """Ежедневная проверка заявок (Celery Beat, 6:00)."""
    from django.core.management import call_command
    call_command('check_orders')
    return 'check_orders выполнено'

@shared_task
def check_shipment_dates():
    """
    Запускается каждый день:
    1. Отправляет напоминание в день отгрузки
    2. Удаляет просроченные заявки (дата < сегодня)
    3. Восстанавливает рейтинг клиентов (5 дней без просрочек)
    """
    from orders.models import Order
    from orders.services import (
        send_shipment_day_email,
        send_overdue_email,
        return_stock,
        invalidate_all_cache,
    )
    from accounts.models import CustomUser

    today = timezone.now().date()

    # 1. Напоминание в день отгрузки
    today_orders = Order.objects.filter(
        shipment_date=today,
        status='completed',
    ).select_related('client')

    for order in today_orders:
        send_shipment_day_email(order)

    # 2. Просроченные заявки (дата отгрузки прошла)
    overdue_orders = Order.objects.filter(
        shipment_date__lt=today,
        status='completed',
    ).select_related('client').prefetch_related('items')

    for order in overdue_orders:
        client = order.client
        # Возврат остатков на склад
        return_stock(order)
        # Снижение рейтинга
        client.decrease_rating()
        # Отправка email
        send_overdue_email(order, client.rating)
        # Удаление заявки
        order.delete()

    # 3. Восстановление рейтинга (5 дней без просрочек)
    clients = CustomUser.objects.filter(
        role='client',
        rating__lt=5,
        last_overdue_date__isnull=False,
    )
    for client in clients:
        if client.try_restore_rating():
            send_rating_restored_email(client)

    invalidate_all_cache()

    return f'Проверено: {today_orders.count()} сегодня, {overdue_orders.count()} просрочено'