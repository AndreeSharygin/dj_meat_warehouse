import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('products', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('shipment_date', models.DateField(verbose_name='Дата отгрузки')),
                ('status', models.CharField(choices=[('new', 'Новая'), ('processing', 'На сборке'), ('completed', 'Собрана')], default='new', max_length=12, verbose_name='Статус')),
                ('comment', models.TextField(blank=True, default='', verbose_name='Комментарий клиента')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Создана')),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orders', to=settings.AUTH_USER_MODEL, verbose_name='Клиент')),
            ],
            options={
                'verbose_name': 'Заявка',
                'verbose_name_plural': 'Заявки',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_name', models.CharField(max_length=200, verbose_name='Наименование')),
                ('quantity', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Количество (кг)')),
                ('price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Цена за кг (₽)')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='orders.order')),
                ('product', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='products.product', verbose_name='Товар')),
            ],
            options={
                'verbose_name': 'Товар в заявке',
                'verbose_name_plural': 'Товары в заявке',
            },
        ),
    ]
