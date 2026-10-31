from django.contrib import admin
from .models import (Customer, Product, ProductVariant, Tax, Plan,
                     Discount, QuotationTemplate, QuotationTemplateLine)

class VariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'product_type', 'sales_price', 'cost_price', 'is_active')
    list_filter = ('product_type', 'is_active')
    search_fields = ('name',)
    inlines = [VariantInline]

class TemplateLineInline(admin.TabularInline):
    model = QuotationTemplateLine
    extra = 1

@admin.register(QuotationTemplate)
class TemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'plan', 'validity_days')
    inlines = [TemplateLineInline]

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'billing_period', 'start_date', 'end_date', 'is_active')
    list_filter = ('billing_period', 'is_active')

@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ('name', 'discount_type', 'value', 'scope', 'start_date', 'end_date', 'times_used', 'usage_limit')
    list_filter = ('discount_type', 'scope', 'is_active')
    filter_horizontal = ('products',)

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'company')
    search_fields = ('name', 'email')

admin.site.register(Tax)