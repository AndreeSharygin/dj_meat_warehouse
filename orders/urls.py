from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Клиент
    path('', views.order_list, name='order_list'),
    path('create/', views.order_create, name='order_create'),
    path('history/', views.order_history, name='order_history'),
    path('<int:pk>/', views.order_detail, name='order_detail'),
    path('<int:pk>/delete/', views.order_delete, name='order_delete'),
    path('<int:pk>/result/', views.order_result, name='order_result'),
    path('<int:pk>/repeat/', views.order_repeat, name='order_repeat'),

    # Менеджер
    path('manager/', views.manager_orders, name='manager_orders'),
    path('manager/<int:pk>/process/', views.manager_process, name='manager_process'),
    path('manager/<int:pk>/confirm/', views.manager_confirm, name='manager_confirm'),
    path('manager/<int:pk>/delete/', views.manager_delete_order, name='manager_delete_order'),
    path('manager/<int:pk>/issue/', views.manager_issue_order, name='manager_issue_order'),
    path('manager/products/', views.manager_products, name='manager_products'),
]