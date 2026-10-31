from django.contrib import admin
from .models import Subscription, SubscriptionLine, SubscriptionStatusHistory

class LineInline(admin.TabularInline):
    model = SubscriptionLine
    extra = 1

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('number', 'customer', 'plan', 'status', 'next_billing_date')
    list_filter = ('status', 'plan')
    search_fields = ('number', 'customer__name')
    inlines = [LineInline]

admin.site.register(SubscriptionStatusHistory)