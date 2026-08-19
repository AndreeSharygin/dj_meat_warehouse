from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.core.cache import cache
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def _send_email(subject, recipient, html_content):
    """Отправка email с HTML-версией и текстовым fallback."""
    text_message = strip_tags(html_content)

    if settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
        sep = '=' * 60
        print(f'\n{sep}')
        print(f'  Кому: {recipient}')
        print(f'  Тема: {subject}')
        print(f'{sep}')
        print(text_message)
        print(f'{sep}\n')
    else:
        try:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient],
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send(fail_silently=True)
        except Exception as e:
            print(f'[EMAIL ERROR]: {e}')


def invalidate_orders_cache(user=None):
    cache.delete('all_active_orders')
    if user:
        cache.delete(f'user_orders_{user.pk}')


def invalidate_all_cache():
    cache.clear()


def send_order_created_email(order):
    items = list(order.items.all())
    html_content = render_to_string('emails/order_created.html', {
        'order': order,
        'items': items,
    })
    _send_email(
        subject=f'Заявка #{order.order_number} создана',
        recipient=order.client.email,
        html_content=html_content,
    )


def send_order_completed_email(order):
    items = list(order.items.all())
    html_content = render_to_string('emails/order_completed.html', {
        'order': order,
        'items': items,
    })
    _send_email(
        subject=f'Заявка #{order.order_number} собрана',
        recipient=order.client.email,
        html_content=html_content,
    )


def send_order_deleted_email(order, reason):
    html_content = render_to_string('emails/order_deleted.html', {
        'order': order,
        'reason': reason,
    })
    _send_email(
        subject=f'Заявка #{order.order_number} удалена',
        recipient=order.client.email,
        html_content=html_content,
    )


def send_shipment_day_email(order):
    items = list(order.items.all())
    html_content = render_to_string('emails/shipment_day.html', {
        'order': order,
        'items': items,
    })
    _send_email(
        subject=f'Напоминание: отгрузка заявки #{order.order_number} сегодня!',
        recipient=order.client.email,
        html_content=html_content,
    )


def send_overdue_email(order, new_rating):
    items = list(order.items.all())
    stars = '⭐' * new_rating + '☆' * (5 - new_rating)
    html_content = render_to_string('emails/order_overdue.html', {
        'order': order,
        'items': items,
        'new_rating': new_rating,
        'stars': stars,
    })
    _send_email(
        subject=f'Заявка #{order.order_number} просрочена — рейтинг понижен',
        recipient=order.client.email,
        html_content=html_content,
    )


def send_overdue_no_penalty_email(order):
    items = list(order.items.all())
    status_display = 'новая' if order.status == 'new' else 'на сборке'
    html_content = render_to_string('emails/order_overdue_no_penalty.html', {
        'order': order,
        'items': items,
        'status_display': status_display,
    })
    _send_email(
        subject=f'Заявка #{order.order_number} удалена (просрочена, без штрафа)',
        recipient=order.client.email,
        html_content=html_content,
    )


def send_order_status_email(order, old_status, new_status):
    status_names = dict(order.STATUS_CHOICES) if hasattr(order, 'STATUS_CHOICES') else {}
    old_name = status_names.get(old_status, old_status)
    new_name = status_names.get(new_status, new_status)
    html_content = render_to_string('emails/order_status_changed.html', {
        'order': order,
        'old_name': old_name,
        'new_name': new_name,
    })
    _send_email(
        subject=f'Статус заявки #{order.order_number} изменён',
        recipient=order.client.email,
        html_content=html_content,
    )


def send_rating_restored_email(client):
    stars = '⭐' * client.rating + '☆' * (5 - client.rating)
    html_content = render_to_string('emails/rating_restored.html', {
        'client': client,
        'stars': stars,
    })
    _send_email(
        subject='Ваш рейтинг восстановлен',
        recipient=client.email,
        html_content=html_content,
    )


def send_issue_email(order):
    items = list(order.items.all())
    html_content = render_to_string('emails/order_issued.html', {
        'order': order,
        'items': items,
    })
    _send_email(
        subject=f'Заявка #{order.order_number} выдана — спасибо за покупку!',
        recipient=order.client.email,
        html_content=html_content,
    )


def return_stock(order):
    """Возврат остатков на склад."""
    from products.models import Product

    try:
        for item in order.items.select_related('product').all():
            if item.product:
                item.product.quantity += item.quantity
                item.product.save(update_fields=['quantity'])
            else:
                product, created = Product.objects.get_or_create(
                    name=item.product_name,
                    defaults={
                        'price': item.price,
                        'quantity': item.quantity,
                    },
                )
                if not created:
                    product.quantity += item.quantity
                    product.save(update_fields=['quantity'])
    except Exception as e:
        print(f'[STOCK ERROR] return_stock: {e}')

    try:
        from products.views import invalidate_products_cache
        invalidate_products_cache()
    except Exception:
        pass