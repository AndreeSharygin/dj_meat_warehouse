from .models import Contact


def contacts(request):
    return {
        'site_contacts': Contact.objects.filter(is_active=True),
    }