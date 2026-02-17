from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import Business, User, Product, ActivityLog


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "location", "date_created")
    search_fields = ("name", "email")
    list_filter = ("date_created",)

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "role", "business", "is_staff", "is_superuser")
    list_filter = ("role", "is_staff", "is_superuser")
    search_fields = ("username", "email")
    ordering = ("username",)
    
  
    readonly_fields = ("date_created", "last_seen", "last_login", "date_joined")
    
    fieldsets = (
        (None, {"fields": ("username", "email", "password")}),
        ("Personal info", {"fields": ("role", "phone_number", "business")}),
        ("Permissions", {"fields": ("is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined", "date_created", "last_seen")}),
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "business", "created_by", "price", "status", "created_at")
    list_filter = ("status", "business")
    search_fields = ("name", "description")
    readonly_fields = ("created_at",)

 


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("user", "action", "timestamp")
    search_fields = ("user__username", "action")
    list_filter = ("timestamp",)
    readonly_fields = ("user", "action", "timestamp")

