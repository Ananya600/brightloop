from django.shortcuts import get_object_or_404, render
from accounts.decorators import role_required
from billing.models import Invoice, Payment
from subscriptions.models import Subscription

HIDDEN = ('draft', 'cancelled')   # customers never see these invoices


def _customer(request):
    return getattr(request.user, 'customer', None)


@role_required('customer')
def my_subscriptions(request):
    subs = Subscription.objects.filter(customer=_customer(request)).select_related('plan').order_by('-id')
    return render(request, 'portal/subscriptions.html', {'subs': subs})


@role_required('customer')
def my_subscription(request, pk):
    sub = get_object_or_404(Subscription, pk=pk, customer=_customer(request))
    return render(request, 'portal/subscription_detail.html', {
        'sub': sub, 'lines': sub.lines.select_related('product', 'variant', 'tax'),
        'invoices': sub.invoices.exclude(status__in=HIDDEN)})


@role_required('customer')
def my_invoices(request):
    invs = Invoice.objects.filter(customer=customer(request)).exclude(status_in=HIDDEN).order_by('-id')
    return render(request, 'portal/invoices.html', {'invoices': invs})


@role_required('customer')
def my_invoice(request, pk):
    inv = get_object_or_404(Invoice.objects.exclude(status__in=HIDDEN), pk=pk, customer=_customer(request))
    return render(request, 'portal/invoice_detail.html', {
        'inv': inv, 'lines': inv.lines.select_related('product'), 'payments': inv.payments.all()})


@role_required('customer')
def my_payments(request):
    pays = Payment.objects.filter(invoice__customer=_customer(request)).select_related('invoice').order_by('-payment_date')
    return render(request, 'portal/payments.html', {'payments': pays})
