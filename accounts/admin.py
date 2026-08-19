from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser, Contact


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    list_display = ('email', 'name', 'role', 'rating', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'rating')
    search_fields = ('email', 'name')
    ordering = ('-date_joined',)
    list_editable = ('role', 'rating')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Личные данные', {'fields': ('name', 'role', 'rating', 'last_overdue_date')}),
        ('Права', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Даты', {'fields': ('date_joined', 'last_login')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'role', 'password1', 'password2'),
        }),
    )


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('role', 'name', 'phone', 'email', 'is_active', 'order')
    list_filter = ('role', 'is_active')
    list_editable = ('phone', 'email', 'is_active', 'order')
    search_fields = ('name', 'email', 'phone')
