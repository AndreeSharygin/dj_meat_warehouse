from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from datetime import timedelta


class CustomUserManager(BaseUserManager):
    def create_user(self, email, name, password=None, **extra_fields):
        if not email:
            raise ValueError('Email обязателен')
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        return self.create_user(email, name, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('client', 'Клиент'),
        ('manager', 'Менеджер'),
        ('admin', 'Администратор'),
    ]

    email = models.EmailField('Email', unique=True)
    name = models.CharField('Имя', max_length=150)
    role = models.CharField('Роль', max_length=10, choices=ROLE_CHOICES, default='client')
    rating = models.IntegerField('Рейтинг', default=5)
    last_overdue_date = models.DateField('Дата последней просрочки', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField('Дата регистрации', default=timezone.now)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f'{self.name} ({self.email})'

    @property
    def is_client(self):
        return self.role == 'client'

    @property
    def is_manager(self):
        return self.role == 'manager'

    @property
    def is_admin_user(self):
        return self.role == 'admin'

    @property
    def has_discount(self):
        return self.rating >= 5

    @property
    def days_until_rating_restore(self):
        """Дней до восстановления рейтинга (считаем от даты последней просроченной заявки)"""
        if self.rating >= 5 or not self.last_overdue_date:
            return 0
        from django.utils import timezone
        days_passed = (timezone.now().date() - self.last_overdue_date).days
        remaining = 5 - days_passed
        return max(0, remaining)

    def decrease_rating(self):
        """Понижение рейтинга на 1. СОХРАНЯЕТ В БД."""
        if self.rating > 0:
            self.rating -= 1
        self.last_overdue_date = timezone.now().date()
        self.save(update_fields=['rating', 'last_overdue_date'])
        return self.rating

    def try_restore_rating(self):
        """Восстановление рейтинга: отсчёт от даты последней просроченной заявки"""
        if self.rating >= 5:
            return False
        if not self.last_overdue_date:
            return False
        from django.utils import timezone
        from datetime import timedelta
        days_passed = (timezone.now().date() - self.last_overdue_date).days
        if days_passed >= 5:
            self.rating = min(5, self.rating + 1)
            if self.rating < 5:
                # Сдвигаем дату на 5 дней вперёд для следующего цикла восстановления
                self.last_overdue_date = self.last_overdue_date + timedelta(days=5)
            else:
                self.last_overdue_date = None
            self.save(update_fields=['rating', 'last_overdue_date'])
            return True
        return False


class Contact(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Администратор'),
        ('manager', 'Менеджер'),
    ]

    role = models.CharField('Должность', max_length=10, choices=ROLE_CHOICES)
    name = models.CharField('Имя', max_length=150)
    phone = models.CharField('Телефон', max_length=30)
    email = models.EmailField('Email')
    is_active = models.BooleanField('Отображать', default=True)
    order = models.PositiveIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Контакт'
        verbose_name_plural = 'Контакты'
        ordering = ['order', 'role']

    def __str__(self):
        return f'{self.get_role_display()} — {self.name}'