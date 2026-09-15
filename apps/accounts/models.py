from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Customer account. Accounts are optional — guest checkout works too."""

    first_name = models.CharField("Prénom", max_length=150, blank=True)
    last_name = models.CharField("Nom", max_length=150, blank=True)
    phone = models.CharField("Téléphone", max_length=20, blank=True)

    def __str__(self):
        return self.get_full_name() or self.email or self.username