from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from catalog.models import Customer, Plan, Product, ProductVariant, Tax


class Subscription(models.Model):
    STATUS_CHOICES = [('draft', 'Draft'), ('quotation', 'Quotation'),
                      ('confirmed', 'Confirmed'), ('active', 'Active'), ('closed', 'Closed')]
    TRANSITIONS = {
        'draft': ['quotation'],
        'quotation': ['confirmed', 'draft'],
        'confirmed': ['active'],
        'active': ['closed'],
        'closed': [],
    }
    TERMS_CHOICES = [('immediate', 'Immediate'), ('net15', 'Net 15 days'), ('net30', 'Net 30 days')]

    number = models.CharField(max_length=20, unique=True, null=True, blank=True, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='subscriptions')
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name='subscriptions')
    start_date = models.DateField()
    expiry_date = models.DateField()
    payment_terms = models.CharField(max_length=10, choices=TERMS_CHOICES, default='immediate')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft', db_index=True)
    next_billing_date = models.DateField(null=True, blank=True, db_index=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                   on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.start_date and self.expiry_date and self.expiry_date <= self.start_date:
            raise ValidationError('Expiry date must be after start date.')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.number:
            self.number = f'SUB-{self.pk:05d}'
            super().save(update_fields=['number'])

    @property
    def total(self):
        return sum(line.amount for line in self.lines.all())

    def change_status(self, new_status, user=None):
        if new_status not in self.TRANSITIONS[self.status]:
            raise ValidationError(f'Cannot move from {self.status} to {new_status}.')
        with transaction.atomic():
            SubscriptionStatusHistory.objects.create(
                subscription=self, old_status=self.status,
                new_status=new_status, changed_by=user)
            self.status = new_status
            if new_status == 'active' and not self.next_billing_date:
                self.next_billing_date = self.start_date
            self.save()

    def __str__(self):
        return self.number or f'Subscription #{self.pk}'


class SubscriptionLine(models.Model):
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    variant = models.ForeignKey(ProductVariant, null=True, blank=True, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    tax = models.ForeignKey(Tax, null=True, blank=True, on_delete=models.SET_NULL)
    amount = models.DecimalField(max_digits=12, decimal_places=2, editable=False, default=0)

    def clean(self):
        if self.subscription_id and self.quantity < self.subscription.plan.min_quantity:
            raise ValidationError(
                f'Minimum quantity for this plan is {self.subscription.plan.min_quantity}.')

    def save(self, *args, **kwargs):
        self.amount = self.quantity * self.unit_price   # before tax
        super().save(*args, **kwargs)


class SubscriptionStatusHistory(models.Model):
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='history')
    old_status = models.CharField(max_length=10)
    new_status = models.CharField(max_length=10)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                   on_delete=models.SET_NULL)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-changed_at']