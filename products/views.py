from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.core.cache import cache
from .models import Product
from .forms import ProductForm


def manager_or_admin_required(view_func):
    """Декоратор: доступ только менеджеру или админу."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not (request.user.is_manager or request.user.is_admin_user):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper


def invalidate_products_cache():
    """Очистка кэша товаров."""
    cache.delete('available_products')


def get_available_products():
    """Получить товары с остатком > 0 (с кэшированием)."""
    products = cache.get('available_products')
    if products is None:
        products = list(Product.objects.filter(quantity__gt=0).order_by('name'))
        cache.set('available_products', products, 300)
    return products


@manager_or_admin_required
def product_list(request):
    """Список всех товаров на складе (для менеджера)."""
    products = Product.objects.all().order_by('name')
    return render(request, 'products/product_list.html', {'products': products})


@manager_or_admin_required
def product_create(request):
    """Добавление нового товара."""
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            invalidate_products_cache()
            messages.success(request, 'Товар добавлен на склад.')
            return redirect('products:product_list')
    else:
        form = ProductForm()
    return render(request, 'products/product_create.html', {'form': form})


@manager_or_admin_required
def product_edit(request, pk):
    """Редактирование товара (количество и цена)."""
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            invalidate_products_cache()
            messages.success(request, f'Товар «{product.name}» обновлён.')
            return redirect('products:product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'products/product_edit.html', {'form': form, 'product': product})


@manager_or_admin_required
def product_delete(request, pk):
    """Удаление товара со склада."""
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        name = product.name
        product.delete()
        invalidate_products_cache()
        messages.success(request, f'Товар «{name}» удалён.')
        return redirect('products:product_list')
    return render(request, 'products/product_confirm_delete.html', {'product': product})