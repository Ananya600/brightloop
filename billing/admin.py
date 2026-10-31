from django.contrib import admin
from .models import Invoice, InvoiceLine, Payment

class InvoiceLineInline(admin.TabularInline):
    model = InvoiceLine
    extra = 0

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('number', 'customer', 'status', 'due_date', 'total')
    list_filter = ('status',)
    search_fields = ('number', 'customer__name')
    inlines = [InvoiceLineInline]

admin.site.register(Payment)