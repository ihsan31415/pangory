from django.contrib import admin
from .models import Certificate

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'course', 'issue_date', 'expiration_date', 'is_valid')
    list_filter = ('issue_date', 'course')
    search_fields = ('user__email', 'course__title')
    readonly_fields = ('id', 'issue_date')
