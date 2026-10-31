from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import Sum
from django.utils import timezone
from catalog.models import Customer, Product
from subscriptions.models import Subscription


class Invoice(models.Model):
    STATUS_CHOICES = [('draft', 'Draft'), ('confirmed', 'Confirmed'),
                      ('paid', 'Paid'), ('cancelled', 'Cancelled')]
    number = models.CharField(max_length=20, unique=True, null=True, blank=True, editable=False)
    subscription = models.ForeignKey(Subscription, on_delete=models.PROTECT, related_name='invoices')
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='invoices')
    period_start = models.DateField()
    period_end = models.DateField()
    issue_date = models.DateField(default=timezone.localdate)
    due_date = models.DateField(db_index=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft', db_index=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['subscription', 'period_start'],
                                               name='one_invoice_per_period')]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.number:
            self.number = f'INV-{self.pk:06d}'
            super().save(update_fields=['number'])

    @property
    def amount_paid(self):
        return self.payments.aggregate(s=Sum('amount'))['s'] or 0

    @property
    def balance(self):
        return self.total - self.amount_paid

    @property
    def is_overdue(self):
        return self.status == 'confirmed' and self.due_date < timezone.localdate()

    def confirm(self):
        if self.status != 'draft':
            raise ValidationError('Only draft invoices can be confirmed.')
        self.status = 'confirmed'
        self.save()

    def cancel(self):
        if self.status not in ('draft', 'confirmed') or self.payments.exists():
            raise ValidationError('This invoice cannot be cancelled.')
        self.status = 'cancelled'
        self.save()

    def __str__(self):
        return self.number or f'Invoice #{self.pk}'


class InvoiceLine(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    description = models.CharField(max_length=200, blank=True)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount = models.DecimalField(max_digits=12, decimal_places=2)   # before tax


class Payment(models.Model):
    METHOD_CHOICES = [('cash', 'Cash'), ('card', 'Card'), ('upi', 'UPI'),
                      ('bank', 'Bank transfer'), ('cheque', 'Cheque')]
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name='payments')
    method = models.CharField(max_length=10, choices=METHOD_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    payment_date = models.DateField(default=timezone.localdate, db_index=True)
    note = models.CharField(max_length=200, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                   on_delete=models.SET_NULL)

    def clean(self):
        if self.invoice_id and self._state.adding:
            if self.invoice.status != 'confirmed':
                raise ValidationError('Payments can only be recorded on confirmed invoices.')
            if self.amount and self.amount > self.invoice.balance:
                raise ValidationError(f'Amount exceeds the balance ({self.invoice.balance}).')

    def save(self, *args, **kwargs):
        with transaction.atomic():
            super().save(*args, **kwargs)
            inv = self.invoice
            if inv.status == 'confirmed' and inv.amount_paid >= inv.total:
                inv.status = 'paid'
                inv.save()