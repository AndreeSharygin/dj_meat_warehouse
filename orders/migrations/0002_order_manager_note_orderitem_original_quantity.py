from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='manager_note',
            field=models.TextField(blank=True, default='', verbose_name='Примечание менеджера'),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='original_quantity',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Исходное количество (кг)'),
        ),
    ]
