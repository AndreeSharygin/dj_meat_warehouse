from django.db import models
from django.conf import settings
from products.models import Product


class Order(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новая'),
        ('processing', 'На сборке'),
        ('completed', 'Собрана'),
        ('issued', 'Выдана'),
    ]

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name='Клиент',
    )
    order_number = models.PositiveIntegerField('Номер заявки', unique=True, editable=False, null=True)
    shipment_date = models.DateField('Дата отгрузки')
    status = models.CharField('Статус', max_length=12, choices=STATUS_CHOICES, default='new')
    comment = models.TextField('Комментарий клиента', blank=True, default='')
    manager_note = models.TextField('Примечание менеджера', blank=True, default='')
    created_at = models.DateTimeField('Создана', auto_now_add=True)
    issued_at = models.DateTimeField('Дата выдачи', null=True, blank=True)
    created_by_admin = models.BooleanField('Создана администратором', default=False)


    class Meta:
        verbose_name = 'Заявка'
        verbose_name_plural = 'Заявки'
        ordering = ['-created_at']

    def __str__(self):
        num = self.order_number or self.pk
        label = f'Заявка #{num} — {self.client.name}'
        if self.created_by_admin:
            label += ' (создана админом)'
        return label


    def save(self, *args, **kwargs):
        if not self.order_number:
            last = Order.objects.order_by('-order_number').values_list('order_number', flat=True).first()
            self.order_number = (last or 0) + 1
        super().save(*args, **kwargs)


    @property
    def total_cost(self):
        total = sum(item.item_cost for item in self.items.all())
        if self.client.has_discount:
            total = total * 0.95
        return round(total, 2)

    @property
    def total_cost_without_discount(self):
        return round(sum(item.item_cost for item in self.items.all()), 2)

    @property
    def was_adjusted(self):
        return any(item.was_adjusted for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL, null=True, verbose_name='Товар'
    )
    product_name = models.CharField('Наименование', max_length=200)
    quantity = models.DecimalField('Количество (кг)', max_digits=10, decimal_places=2)
    original_quantity = models.DecimalField(
        'Исходное количество (кг)', max_digits=10, decimal_places=2, null=True, blank=True
    )
    price = models.DecimalField('Цена за кг (₽)', max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Товар в заявке'
        verbose_name_plural = 'Товары в заявке'

    def __str__(self):
        return f'{self.product_name} × {self.quantity} кг'

    @property
    def item_cost(self):
        return round(float(self.quantity) * float(self.price), 2)

    @property
    def was_adjusted(self):
        if self.original_quantity is None:
            return False
        return self.original_quantity != self.quantity

    @property
    def quantity_difference(self):
        if self.original_quantity is None:
            return 0
        return float(self.quantity) - float(self.original_quantity)

    @property
    def quantity_difference_abs(self):
        return abs(self.quantity_difference)

    @property
    def quantity_increased(self):
        return self.quantity_difference > 0

    @property
    def quantity_decreased(self):
        return self.quantity_difference < 0

