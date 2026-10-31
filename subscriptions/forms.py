from django import forms
from catalog.models import Customer, QuotationTemplate
from .models import Subscription, SubscriptionLine


class BootstrapMixin:
    def style(self):
        for f in self.fields.values():
            cls = 'form-select' if isinstance(f.widget, forms.Select) else 'form-control'
            f.widget.attrs['class'] = cls


class SubscriptionForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Subscription
        fields = ['customer', 'plan', 'start_date', 'expiry_date', 'payment_terms']
        widgets = {'start_date': forms.DateInput(attrs={'type': 'date'}),
                   'expiry_date': forms.DateInput(attrs={'type': 'date'})}

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.style()

    def clean(self):
        d = super().clean()
        plan, start = d.get('plan'), d.get('start_date')
        if plan and start:
            if start < plan.start_date or (plan.end_date and start > plan.end_date):
                self.add_error('start_date', 'This plan is not available on that date.')
            if not plan.is_active:
                self.add_error('plan', 'This plan is not active.')
        return d


class TemplateForm(BootstrapMixin, forms.Form):
    template = forms.ModelChoiceField(QuotationTemplate.objects.all())
    customer = forms.ModelChoiceField(Customer.objects.all())
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    payment_terms = forms.ChoiceField(choices=Subscription.TERMS_CHOICES)

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.style()


class LineForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = SubscriptionLine
        fields = ['product', 'variant', 'quantity', 'tax']

    def __init__(self, *a, subscription=None, **kw):
        super().__init__(*a, **kw)
        self.subscription = subscription
        self.style()

    def clean(self):
        d = super().clean()
        p, v, q = d.get('product'), d.get('variant'), d.get('quantity')
        if p and v and v.product_id != p.id:
            self.add_error('variant', 'This variant does not belong to the selected product.')
        if q and self.subscription and q < self.subscription.plan.min_quantity:
            self.add_error('quantity', f'Minimum quantity for this plan is {self.subscription.plan.min_quantity}.')
        return d

    def save(self, commit=True):
        line = super().save(commit=False)
        line.subscription = self.subscription
        extra = line.variant.extra_price if line.variant else 0
        line.unit_price = line.product.sales_price + extra
        if commit:
            line.save()
        return line