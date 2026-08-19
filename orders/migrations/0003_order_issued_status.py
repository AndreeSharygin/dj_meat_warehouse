from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0002_order_manager_note_orderitem_original_quantity'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(
                choices=[
                    ('new', 'Новая'),
                    ('processing', 'На сборке'),
                    ('completed', 'Собрана'),
                    ('issued', 'Выдана'),
                ],
                default='new', max_length=12, verbose_name='Статус'
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='issued_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Дата выдачи'),
        ),
    ]