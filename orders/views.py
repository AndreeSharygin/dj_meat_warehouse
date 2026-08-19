from decimal import Decimal
from datetime import datetime, date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.core.cache import cache
from django.utils import timezone

from .models import Order, OrderItem
from .forms import OrderForm, ManagerDeleteForm
from .services import (
    send_order_created_email,
    send_order_completed_email,
    send_order_deleted_email,
    send_issue_email,
    return_stock,
    invalidate_all_cache,
)
from products.models import Product
from products.views import invalidate_products_cache


# ═══════════════════════════════════════════
#              ОБЩИЕ VIEWS
# ═══════════════════════════════════════════

@login_required
def home_view(request):
    """Главная — редирект по роли."""
    if request.user.is_manager or request.user.is_admin_user:
        return redirect('orders:manager_orders')
    return redirect('orders:order_list')


# ═══════════════════════════════════════════
#              КЛИЕНТСКИЕ VIEWS
# ═══════════════════════════════════════════

@login_required
def order_list(request):
    """Список активных заявок клиента (без выданных)."""
    if not request.user.is_client:
        return redirect('orders:manager_orders')

    request.user.try_restore_rating()

    orders = Order.objects.filter(
        client=request.user
    ).exclude(status='issued').prefetch_related('items').order_by('-created_at')

    status_filter = request.GET.get('status', '')
    search = request.GET.get('search', '')

    if status_filter:
        orders = orders.filter(status=status_filter)
    if search:
        orders = orders.filter(items__product_name__icontains=search).distinct()

    return render(request, 'orders/order_list.html', {
        'orders': orders,
        'status_filter': status_filter,
        'search': search,
    })


@login_required
def order_create(request):
    products = Product.objects.filter(quantity__gt=0).order_by('name')

    if request.method == 'POST':
        shipment_date = request.POST.get('shipment_date')
        comment = request.POST.get('comment', '')
        product_ids = request.POST.getlist('product_id')
        quantities = request.POST.getlist('quantity')

        if not shipment_date:
            messages.error(request, 'Укажите дату отгрузки.')
            return render(request, 'orders/order_create.html', {
                'products': products,
                'has_discount': request.user.has_discount,
            })

        try:
            ship_date = datetime.strptime(shipment_date, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, 'Неверный формат даты.')
            return render(request, 'orders/order_create.html', {
                'products': products,
                'has_discount': request.user.has_discount,
            })

        if ship_date < timezone.now().date():
            messages.error(request, 'Дата не может быть прошедшей.')
            return render(request, 'orders/order_create.html', {
                'products': products,
                'has_discount': request.user.has_discount,
            })

        items_data = []
        over_stock_products = []

        for pid, qty_str in zip(product_ids, quantities):
            qty_str = qty_str.strip()
            if not qty_str or float(qty_str) <= 0:
                continue
            try:
                product = Product.objects.get(pk=pid)
                qty = Decimal(qty_str)
            except (Product.DoesNotExist, Exception):
                continue

            if qty > product.quantity:
                over_stock_products.append(
                    f'{product.name} (запрошено: {qty} кг, на складе: {product.quantity} кг)'
                )

            items_data.append({
                'product': product,
                'quantity': qty,
            })

        if not items_data:
            messages.error(request, 'Добавьте хотя бы один товар.')
            return render(request, 'orders/order_create.html', {
                'products': products,
                'has_discount': request.user.has_discount,
            })

        if over_stock_products:
            error_list = '\n'.join(over_stock_products)
            messages.error(request, f'Недостаточно товара на складе:\n{error_list}')
            return render(request, 'orders/order_create.html', {
                'products': products,
                'has_discount': request.user.has_discount,
            })

        order = Order.objects.create(
            client=request.user,
            shipment_date=ship_date,
            comment=comment,
        )

        for item_data in items_data:
            product = item_data['product']
            qty = item_data['quantity']

            OrderItem.objects.create(
                order=order,
                product=product,
                product_name=product.name,
                quantity=qty,
                original_quantity=qty,
                price=product.price,
            )

            product.quantity -= qty
            product.save(update_fields=['quantity'])

        send_order_created_email(order)
        invalidate_all_cache()

        messages.success(request, f'Заявка #{order.order_number} создана!')
        return redirect('orders:order_list')

    return render(request, 'orders/order_create.html', {
        'products': products,
        'has_discount': request.user.has_discount,
    })


@login_required
def order_detail(request, pk):
    """Детали заявки."""
    order = get_object_or_404(Order.objects.prefetch_related('items'), pk=pk)
    if not (request.user.is_manager or request.user.is_admin_user) and order.client != request.user:
        raise PermissionDenied
    return render(request, 'orders/order_detail.html', {'order': order})


@login_required
def order_delete(request, pk):
    """Удаление заявки клиентом."""
    order = get_object_or_404(Order.objects.prefetch_related('items'), pk=pk)
    if order.client != request.user:
        raise PermissionDenied
    if order.status == 'processing':
        messages.error(request, 'Нельзя удалить заявку — она на сборке.')
        return redirect('orders:order_list')

    if request.method == 'POST':
        order_pk = order.order_number
        return_stock(order)
        order.delete()
        invalidate_all_cache()
        messages.success(request, f'Заявка #{order_pk} удалена. Остатки возвращены на склад.')
        return redirect('orders:order_list')
    return render(request, 'orders/order_confirm_delete.html', {'order': order})


@login_required
def order_result(request, pk):
    """Результат собранной заявки."""
    order = get_object_or_404(
        Order.objects.prefetch_related('items'),
        pk=pk, client=request.user, status='completed',
    )
    return render(request, 'orders/order_result.html', {'order': order})


@login_required
def order_history(request):
    """Последние 10 выданных заявок клиента."""
    if request.user.is_client:
        orders = Order.objects.filter(
            client=request.user, status='issued'
        ).prefetch_related('items').order_by('-issued_at')[:10]
    else:
        # Менеджер/админ — все выданные, сгруппированные по клиентам
        from accounts.models import CustomUser
        clients = CustomUser.objects.filter(role='client', orders__status='issued').distinct()
        clients_data = []
        for client in clients:
            client_orders = Order.objects.filter(
                client=client, status='issued'
            ).prefetch_related('items').order_by('-issued_at')[:10]
            if client_orders.exists():
                clients_data.append({
                    'client': client,
                    'orders': client_orders,
                })
        return render(request, 'orders/order_history_manager.html', {
            'clients_data': clients_data,
        })

    return render(request, 'orders/order_history.html', {
        'orders': orders,
    })


@login_required
def order_repeat(request, pk):
    """Повторить заявку — создать копию с теми же товарами."""
    if not request.user.is_client:
        raise PermissionDenied

    original = get_object_or_404(
        Order.objects.prefetch_related('items__product'),
        pk=pk, client=request.user
    )

    if request.method == 'POST':
        # Получаем дату из формы
        shipment_date_str = request.POST.get('shipment_date', '')
        if not shipment_date_str:
            messages.error(request, 'Укажите дату отгрузки.')
            return render(request, 'orders/order_repeat_confirm.html', {'order': original})

        try:
            ship_date = datetime.strptime(shipment_date_str, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, 'Неверный формат даты.')
            return render(request, 'orders/order_repeat_confirm.html', {'order': original})

        if ship_date <= timezone.now().date():
            messages.error(request, 'Дата отгрузки должна быть в будущем.')
            return render(request, 'orders/order_repeat_confirm.html', {'order': original})

        # Проверяем доступность товаров
        items_to_create = []
        errors = []

        for item in original.items.all():
            product = item.product
            if not product:
                errors.append(f'Товар «{item.product_name}» больше не существует.')
                continue
            if product.quantity <= 0:
                errors.append(f'Товар «{product.name}» отсутствует на складе.')
                continue

            qty = min(item.quantity, product.quantity)
            items_to_create.append({
                'product': product,
                'quantity': qty,
                'original_quantity': qty,
                'price': product.price,
            })

        if errors and not items_to_create:
            for err in errors:
                messages.error(request, err)
            return redirect('orders:order_history')

        if not items_to_create:
            messages.error(request, 'Нет доступных товаров для повтора.')
            return redirect('orders:order_history')

        # Создаём новую заявку
        new_order = Order.objects.create(
            client=request.user,
            shipment_date=ship_date,
            comment=f'Повтор заявки #{original.pk}',
        )

        for data in items_to_create:
            OrderItem.objects.create(
                order=new_order,
                product=data['product'],
                product_name=data['product'].name,
                quantity=data['quantity'],
                original_quantity=data['original_quantity'],
                price=data['price'],
            )
            data['product'].quantity -= data['quantity']
            data['product'].save(update_fields=['quantity'])

        invalidate_all_cache()

        if errors:
            for err in errors:
                messages.warning(request, err)

        messages.success(
            request,
            f'Заявка #{new_order.order_number} создана (повтор #{original.pk}). '
            f'Дата отгрузки: {ship_date.strftime("%d.%m.%Y")}.'
        )
        return redirect('orders:order_list')

    return render(request, 'orders/order_repeat_confirm.html', {'order': original})


# ═══════════════════════════════════════════
#             МЕНЕДЖЕРСКИЕ VIEWS
# ═══════════════════════════════════════════

def manager_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not (request.user.is_manager or request.user.is_admin_user):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper


@manager_required
def manager_orders(request):
    """Все активные заявки для менеджера (без выданных)."""
    orders = Order.objects.select_related('client').prefetch_related(
        'items'
    ).exclude(status='issued').order_by('-created_at')

    client_search = request.GET.get('client', '')
    status_filter = request.GET.get('status', '')

    if client_search:
        orders = orders.filter(client__name__icontains=client_search)
    if status_filter:
        orders = orders.filter(status=status_filter)

    return render(request, 'orders/manager_orders.html', {
        'orders': orders,
        'client_search': client_search,
        'status_filter': status_filter,
    })


@manager_required
def manager_process(request, pk):
    order = get_object_or_404(
        Order.objects.select_related('client').prefetch_related('items__product'),
        pk=pk
    )

    # Защита от повторной обработки
    if order.status not in ('new',):
        messages.info(request, f'Заявка #{order.order_number} уже обрабатывается.')
        return redirect('orders:manager_orders')

    if request.method == 'POST':
        item_ids = request.POST.getlist('item_id')
        new_quantities = request.POST.getlist('new_quantity')
        manager_note = request.POST.get('manager_note', '').strip()

        errors = []
        adjustments = []

        for item_id_str, new_qty_str in zip(item_ids, new_quantities):
            try:
                item = OrderItem.objects.select_related('product').get(
                    pk=int(item_id_str), order=order
                )
            except OrderItem.DoesNotExist:
                errors.append(f'Позиция #{item_id_str} не найдена.')
                continue

            try:
                new_qty = Decimal(new_qty_str)
            except Exception:
                errors.append(f'Некорректное количество для «{item.product_name}».')
                continue

            if new_qty < 0:
                errors.append(f'Количество «{item.product_name}» не может быть отрицательным.')
                continue

            max_available = item.quantity
            if item.product:
                max_available = item.quantity + item.product.quantity

            if new_qty > max_available:
                errors.append(
                    f'«{item.product_name}»: максимально доступно {max_available} кг.'
                )
                continue

            adjustments.append((item, new_qty))

        if errors:
            for err in errors:
                messages.error(request, err)
        else:
            for item, new_qty in adjustments:
                old_qty = item.quantity
                difference = old_qty - new_qty

                if difference != 0 and item.product:
                    item.product.quantity += difference
                    if item.product.quantity < 0:
                        item.product.quantity = 0
                    item.product.save()

                item.quantity = new_qty
                item.save()

            order.items.filter(quantity=0).delete()

            if order.items.count() == 0:
                return_stock(order)
                order.delete()
                invalidate_all_cache()
                messages.warning(request, f'Заявка #{pk} удалена — все товары обнулены.')
                return redirect('orders:manager_orders')

            order.status = 'processing'
            order.manager_note = manager_note
            order.save(update_fields=['status', 'manager_note'])

            invalidate_all_cache()
            invalidate_products_cache()
            messages.success(request, f'Заявка #{order.order_number} взята в сборку.')
            return redirect('orders:manager_confirm', pk=order.pk)

    items_data = []
    for item in order.items.select_related('product').all():
        stock = float(item.product.quantity) if item.product else 0
        current = float(item.quantity)
        items_data.append({
            'item': item,
            'stock': stock,
            'max_available': round(current + stock, 2),
        })

    return render(request, 'orders/manager_process.html', {
        'order': order,
        'items_data': items_data,
    })


@manager_required
def manager_confirm(request, pk):
    order = get_object_or_404(
        Order.objects.select_related('client').prefetch_related('items'),
        pk=pk
    )

    if request.method == 'POST':
        order.status = 'completed'
        order.save()
        invalidate_all_cache()
        send_order_completed_email(order)
        messages.success(request, f'Заявка #{order.order_number} подтверждена.')
        return redirect('orders:manager_orders')

    return render(request, 'orders/manager_confirm.html', {'order': order})


@manager_required
def manager_delete_order(request, pk):
    order = get_object_or_404(Order.objects.prefetch_related('items'), pk=pk)

    if request.method == 'POST':
        form = ManagerDeleteForm(request.POST)
        if form.is_valid():
            reason = form.cleaned_data['reason']
            order_pk = order.order_number
            client_email = order.client.email

            return_stock(order)
            send_order_deleted_email(order, reason)
            order.delete()
            invalidate_all_cache()

            messages.success(request, f'Заявка #{order_pk} удалена. Уведомление отправлено на {client_email}.')
            return redirect('orders:manager_orders')
    else:
        form = ManagerDeleteForm()

    return render(request, 'orders/manager_confirm_delete.html', {
        'order': order,
        'form': form,
    })


@manager_required
def manager_issue_order(request, pk):
    """Менеджер выдаёт заявку → статус 'issued', НЕ удаляем."""
    order = get_object_or_404(
        Order.objects.select_related('client').prefetch_related('items'),
        pk=pk
    )

    if order.status != 'completed':
        messages.error(request, f'Заявка #{order.order_number} ещё не собрана.')
        return redirect('orders:manager_orders')

    if request.method == 'POST':
        order.status = 'issued'
        order.issued_at = timezone.now()
        order.save()

        send_issue_email(order)
        invalidate_all_cache()

        messages.success(
            request,
            f'Заявка #{order.order_number} выдана клиенту {order.client.name}. '
            f'Уведомление отправлено на {order.client.email}.'
        )
        return redirect('orders:manager_orders')

    return render(request, 'orders/manager_confirm_issue.html', {'order': order})


@manager_required
def manager_products(request):
    products = Product.objects.all().order_by('name')

    search = request.GET.get('search', '')
    availability = request.GET.get('availability', '')

    if search:
        products = products.filter(name__icontains=search)
    if availability == 'available':
        products = products.filter(quantity__gt=10)
    elif availability == 'low':
        products = products.filter(quantity__gt=0, quantity__lt=10)
    elif availability == 'empty':
        products = products.filter(quantity__lte=0)

    all_products = Product.objects.all()
    total_products = all_products.count()
    available_count = all_products.filter(quantity__gt=10).count()
    low_count = all_products.filter(quantity__gt=0, quantity__lt=10).count()
    empty_count = all_products.filter(quantity__lte=0).count()

    return render(request, 'orders/manager_products.html', {
        'products': products,
        'search': search,
        'availability': availability,
        'total_products': total_products,
        'available_count': available_count,
        'low_count': low_count,
        'empty_count': empty_count,
    })