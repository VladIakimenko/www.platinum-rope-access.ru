from django.contrib import admin
from reports.models import Settings, Worker


class SettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False if self.model.objects.count() > 0 else super().has_add_permission(request)


admin.site.register(Settings, SettingsAdmin)
admin.site.register(Worker)
