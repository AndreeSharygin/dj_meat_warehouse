#!/bin/bash
set -e

echo "⏳ Ожидание PostgreSQL..."
while ! nc -z db 5432; do sleep 1; done
echo "✅ PostgreSQL доступен."

echo "⏳ Ожидание Redis..."
while ! nc -z redis 6379; do sleep 1; done
echo "✅ Redis доступен."

echo "📦 Применение миграций..."
python manage.py migrate --noinput || python manage.py migrate --fake orders 0003_order_issued_status && python manage.py migrate --noinput

echo "📁 Сборка статики..."
python manage.py collectstatic --noinput

echo "👤 Создание пользователей..."
python manage.py shell -c "
from accounts.models import CustomUser

if not CustomUser.objects.filter(email='admin@warehouse.ru').exists():
    CustomUser.objects.create_superuser(email='admin@warehouse.ru', name='Администратор', password='admin123')
    print('  ✅ Админ: admin@warehouse.ru / admin123')
else:
    print('  ℹ️ Админ уже существует.')

if not CustomUser.objects.filter(email='manager@warehouse.ru').exists():
    CustomUser.objects.create_user(email='manager@warehouse.ru', name='Менеджер склада', password='manager123', role='manager', is_staff=True)
    print('  ✅ Менеджер: manager@warehouse.ru / manager123')
else:
    print('  ℹ️ Менеджер уже существует.')
"

echo "🔍 Проверка просроченных заявок..."
python manage.py check_orders

echo "════════════════════════════════════════"
echo "🚀 Сервер: http://localhost:8000/"
echo "👑 Админ: admin@warehouse.ru / admin123"
echo "👔 Менеджер: manager@warehouse.ru / manager123"
exec python manage.py runserver 0.0.0.0:8000