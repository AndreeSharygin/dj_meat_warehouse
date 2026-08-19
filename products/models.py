from django.db import models


class Product(models.Model):
    """Товар на складе. Создаётся и редактируется менеджером."""

    name = models.CharField('Наименование', max_length=200, unique=True)
    price = models.DecimalField('Цена за кг (₽)', max_digits=10, decimal_places=2)
    quantity = models.DecimalField(
        'Остаток на складе (кг)', max_digits=10, decimal_places=2
    )
    created_at = models.DateTimeField('Добавлен', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлён', auto_now=True)

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} — {self.quantity} кг по {self.price} ₽/кг'

    @property
    def is_available(self):
        """Доступен ли товар для заказа."""
        return self.quantity > 0