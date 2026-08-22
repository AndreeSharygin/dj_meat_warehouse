from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import CustomUser
from orders.models import Order
from orders.services import (
    send_shipment_day_email,
    send_overdue_email,
    send_overdue_no_penalty_email,
    send_rating_restored_email,
    return_stock,
    invalidate_all_cache,
)


class Command(BaseCommand):
    help = 'Проверка просроченных заявок и восстановление рейтинга'

    def handle(self, *args, **options):
        today = timezone.now().date()

        # 1. Напоминание в день отгрузки (собранные)
        today_orders = Order.objects.filter(
            shipment_date=today, status='completed'
        ).select_related('client')

        for order in today_orders:
            send_shipment_day_email(order)
            self.stdout.write(f'  Напоминание: заявка #{order.order_number} → {order.client.email}')

        # 2. Просроченные собранные заявки → возврат + штраф + удаление
        overdue_completed = Order.objects.filter(
            shipment_date__lt=today, status='completed'
        ).select_related('client').prefetch_related('items__product')

        for order in overdue_completed:
            client = order.client
            order_pk = order.order_number

            return_stock(order)

            if client.rating > 0:
                client.rating = max(0, client.rating - 1)
            client.last_overdue_date = order.shipment_date
            client.save(update_fields=['rating', 'last_overdue_date'])

            send_overdue_email(order, client.rating)
            order.delete()

            self.stdout.write(self.style.WARNING(
                f'  Просрочена #{order_pk}: {client.name}, рейтинг {client.rating}/5'
            ))

        # 3. Просроченные новые/на сборке → возврат + удаление (без штрафа)
        overdue_pending = Order.objects.filter(
            shipment_date__lt=today, status__in=['new', 'processing']
        ).select_related('client').prefetch_related('items__product')

        for order in overdue_pending:
            client = order.client
            order_pk = order.order_number

            return_stock(order)
            send_overdue_no_penalty_email(order)
            order.delete()

            self.stdout.write(self.style.WARNING(
                f'  Просрочена (без штрафа) #{order_pk}: {client.name}'
            ))
        # 4. Восстановление рейтинга (каждые 5 дней +1)
        clients_to_restore = CustomUser.objects.filter(
            role='client', rating__lt=5, last_overdue_date__isnull=False
        )

        restored_count = 0
        for client in clients_to_restore:
            days_since = (today - client.last_overdue_date).days
            if days_since >= 5:
                client.rating = min(5, client.rating + 1)
                if client.rating < 5:
                    client.last_overdue_date = client.last_overdue_date + timedelta(days=5)
                else:
                    client.last_overdue_date = None
                client.save(update_fields=['rating', 'last_overdue_date'])
                send_rating_restored_email(client)
                restored_count += 1


        invalidate_all_cache()

        self.stdout.write(self.style.SUCCESS(
            f'Готово. Напоминаний: {today_orders.count()}, '
            f'просрочено: {overdue_completed.count() + overdue_pending.count()}, '
            f'восстановлено рейтингов: {restored_count}'
        ))