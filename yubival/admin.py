from django.contrib import admin

from yubival.models import Device, APIKey


class APIKeyAdmin(admin.ModelAdmin):
    readonly_fields = (
        'date_created',
    )


class DeviceAdmin(admin.ModelAdmin):
    readonly_fields = (
        'session_counter',
        'usage_counter',
        'date_created',
    )


admin.site.register(APIKey, APIKeyAdmin)
admin.site.register(Device, DeviceAdmin)
