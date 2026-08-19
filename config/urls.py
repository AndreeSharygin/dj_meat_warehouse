from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from orders.views import home_view

admin.site.site_header = '🥩 Мясной склад'
admin.site.site_title = 'Мясной склад — Админ'
admin.site.index_title = 'Панель управления'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),
    path('accounts/', include('accounts.urls')),
    path('orders/', include('orders.urls')),
    path('products/', include('products.urls')),
]

# Для раздачи статики в любом режиме (dev)
if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()