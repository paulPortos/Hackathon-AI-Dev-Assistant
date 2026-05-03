from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from users.models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = (
        (None, {'fields': ('github_id', 'username', 'password')}),
        ('GitHub profile', {'fields': ('name', 'email', 'avatar_url', 'access_token')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': ('github_id', 'username', 'email', 'password1', 'password2'),
            },
        ),
    )
    list_display = ('username', 'github_id', 'email', 'name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'is_superuser')
    readonly_fields = ('created_at', 'updated_at')
    search_fields = ('username', 'github_id', 'email', 'name')
    ordering = ('username',)
