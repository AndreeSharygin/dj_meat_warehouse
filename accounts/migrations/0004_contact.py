from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_customuser_last_overdue_date'),
    ]

    operations = [
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('admin', 'Администратор'), ('manager', 'Менеджер')], max_length=10, verbose_name='Должность')),
                ('name', models.CharField(max_length=150, verbose_name='Имя')),
                ('phone', models.CharField(max_length=30, verbose_name='Телефон')),
                ('email', models.EmailField(max_length=254, verbose_name='Email')),
                ('is_active', models.BooleanField(default=True, verbose_name='Отображать')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Порядок')),
            ],
            options={
                'verbose_name': 'Контакт',
                'verbose_name_plural': 'Контакты',
                'ordering': ['order', 'role'],
            },
        ),
    ]