from django.contrib import admin
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
from django.contrib.auth.admin import UserAdmin


class MyUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('email',)


admin.site.register(CustomUser, UserAdmin)