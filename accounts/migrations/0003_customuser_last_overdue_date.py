from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_alter_customuser_date_joined_alter_customuser_role'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='last_overdue_date',
            field=models.DateField(verbose_name='Дата последней просрочки', null=True, blank=True),
        ),
    ]