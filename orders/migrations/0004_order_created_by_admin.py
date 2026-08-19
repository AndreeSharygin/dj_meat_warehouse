from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0003_order_issued_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='created_by_admin',
            field=models.BooleanField(default=False, verbose_name='Создана администратором'),
        ),
    ]