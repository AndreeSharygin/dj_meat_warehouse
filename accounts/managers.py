from django.contrib.auth.base_user import BaseUserManager


class CustomUserManager(BaseUserManager):
    """Менеджер пользователей с авторизацией по email."""

    def create_user(self, email, name, password=None, **extra_fields):
        if not email:
            raise ValueError('Email обязателен')
        if not name:
            raise ValueError('Имя обязательно')
        email = self.normalize_email(email)
        extra_fields.setdefault('role', 'client')
        user = self.model(email=email, name=name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password=None, **extra_fields):
        """Суперпользователь = Администратор с полным доступом."""
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, name, password, **extra_fields)