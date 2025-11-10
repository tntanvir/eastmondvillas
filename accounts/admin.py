from django.contrib import admin
from django.contrib.auth import get_user_model

User = get_user_model()


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
	list_display = ("email", "name", "role", "permission", "is_staff", "is_active")
	search_fields = ("email", "name")
	list_filter = ("role", "permission", "is_staff", "is_active")
	readonly_fields = ("date_joined",)
	fieldsets = (
		(None, {"fields": ("email", "name", "phone")} ),
		("Permissions", {"fields": ("role", "permission", "is_staff", "is_active", "is_superuser")}),
		("Important dates", {"fields": ("date_joined",)}),
	)

