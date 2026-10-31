from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone


class Customer(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='customer')
    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    company = models.CharField(max_length=150, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    TYPE_CHOICES = [('service', 'Service'), ('software', 'Software'), ('goods', 'Goods')]
    name = models.CharField(max_length=150)
    product_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='software')
    sales_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    attribute = models.CharField(max_length=50)            # e.g. Brand
    value = models.CharField(max_length=50)                # e.g. Odoo
    extra_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # e.g. 560

    class Meta:
        unique_together = ('product', 'attribute', 'value')

    def __str__(self):
        return f'{self.product.name} - {self.attribute}: {self.value} (+{self.extra_price})'


class Tax(models.Model):
    name = models.CharField(max_length=50)
    rate = models.DecimalField(max_digits=5, decimal_places=2,
                               validators=[MinValueValidator(0), MaxValueValidator(100)])  # percent
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'taxes'

    def __str__(self):
        return f'{self.name} ({self.rate}%)'


class Plan(models.Model):
    PERIOD_CHOICES = [('daily', 'Daily'), ('weekly', 'Weekly'),
                      ('monthly', 'Monthly'), ('yearly', 'Yearly')]
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    billing_period = models.CharField(max_length=10, choices=PERIOD_CHOICES, default='monthly')
    min_quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    auto_close = models.BooleanField(default=False)   # closes itself when it ends
    closable = models.BooleanField(default=True)      # can be closed early
    pausable = models.BooleanField(default=False)
    renewable = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    def clean(self):
        if self.end_date and self.end_date <= self.start_date:
            raise ValidationError('End date must be after start date.')

    def __str__(self):
        return f'{self.name} ({self.billing_period})'

class Discount(models.Model):
    TYPE_CHOICES = [('fixed', 'Fixed amount'), ('percentage', 'Percentage')]
    SCOPE_CHOICES = [('product', 'Specific products'), ('subscription', 'Whole subscription')]
    name = models.CharField(max_length=100)
    discount_type = models.CharField(max_length=12, choices=TYPE_CHOICES)
    value = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    scope = models.CharField(max_length=12, choices=SCOPE_CHOICES, default='subscription')
    products = models.ManyToManyField(Product, blank=True)   # used when scope = product
    min_purchase = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    min_quantity = models.PositiveIntegerField(default=0)
    start_date = models.DateField()
    end_date = models.DateField()
    usage_limit = models.PositiveIntegerField(null=True, blank=True)  # blank = unlimited
    times_used = models.PositiveIntegerField(default=0, editable=False)
    is_active = models.BooleanField(default=True)

    def clean(self):
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError('End date cannot be before start date.')
        if self.discount_type == 'percentage' and self.value is not None and self.value > 100:
            raise ValidationError('Percentage cannot exceed 100.')

    def is_available(self, on=None):
        on = on or timezone.localdate()
        if not self.is_active or not (self.start_date <= on <= self.end_date):
            return False
        return self.usage_limit is None or self.times_used < self.usage_limit

    def _str_(self):
        return self.name


class QuotationTemplate(models.Model):
    name = models.CharField(max_length=100)
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    validity_days = models.PositiveIntegerField(default=30, validators=[MinValueValidator(1)])
    notes = models.TextField(blank=True)

    def _str_(self):
        return self.name


class QuotationTemplateLine(models.Model):
    template = models.ForeignKey(QuotationTemplate, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    variant = models.ForeignKey(ProductVariant, null=True, blank=True, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    tax = models.ForeignKey(Tax, null=True, blank=True, on_delete=models.SET_NULL)