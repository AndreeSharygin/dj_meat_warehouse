from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, unique=True, verbose_name='Наименование')),
                ('price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Цена за кг (₽)')),
                ('quantity', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Остаток на складе (кг)')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Добавлен')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Обновлён')),
            ],
            options={
                'verbose_name': 'Товар',
                'verbose_name_plural': 'Товары',
                'ordering': ['name'],
            },
        ),
    ]
