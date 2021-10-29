from django.contrib import admin

from yubival.models import Device, APIKey


class APIKeyAdmin(admin.ModelAdmin):
    pass


class DeviceAdmin(admin.ModelAdmin):
    pass


admin.site.register(APIKey, APIKeyAdmin)
admin.site.register(Device, DeviceAdmin)
