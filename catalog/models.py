from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


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