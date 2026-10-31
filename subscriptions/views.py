from datetime import timedelta
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import LineForm, SubscriptionForm, TemplateForm
from .models import Subscription, SubscriptionLine


def staff_only(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        u = request.user
        if not (u.is_superuser or u.role in ('admin', 'staff')):
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return login_required(wrapper)


@staff_only
def subscription_list(request):
    qs = Subscription.objects.select_related('customer', 'plan').order_by('-id')
    status, q = request.GET.get('status', ''), request.GET.get('q', '')
    if status:
        qs = qs.filter(status=status)
    if q:
        qs = qs.filter(Q(number__icontains=q) | Q(customer__name__icontains=q))
    page = Paginator(qs, 20).get_page(request.GET.get('page'))
    return render(request, 'subscriptions/list.html', {
        'page': page, 'status': status, 'q': q, 'statuses': Subscription.STATUS_CHOICES})


@staff_only
def subscription_create(request):
    form = SubscriptionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        sub = form.save(commit=False)
        sub.created_by = request.user
        sub.save()
        messages.success(request, f'{sub.number} created.')
        return redirect('subscription_detail', pk=sub.pk)
    return render(request, 'subscriptions/form.html', {'form': form, 'title': 'New subscription'})


@staff_only
def subscription_from_template(request):
    form = TemplateForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        t, cd = form.cleaned_data['template'], form.cleaned_data
        with transaction.atomic():
            sub = Subscription.objects.create(
                customer=cd['customer'], plan=t.plan, start_date=cd['start_date'],
                expiry_date=cd['start_date'] + timedelta(days=t.validity_days),
                payment_terms=cd['payment_terms'], created_by=request.user)
            for l in t.lines.select_related('product', 'variant'):
                extra = l.variant.extra_price if l.variant else 0
                SubscriptionLine.objects.create(
                    subscription=sub, product=l.product, variant=l.variant, quantity=l.quantity,
                    tax=l.tax, unit_price=l.product.sales_price + extra)
        messages.success(request, f'{sub.number} created from template.')
        return redirect('subscription_detail', pk=sub.pk)
    return render(request, 'subscriptions/form.html', {'form': form, 'title': 'New from template'})


@staff_only
def subscription_detail(request, pk):
    sub = get_object_or_404(Subscription.objects.select_related('customer', 'plan'), pk=pk)
    can_edit = sub.status in ('draft', 'quotation')
    form = LineForm(request.POST or None, subscription=sub)
    if request.method == 'POST':
        if not can_edit:
            messages.error(request, 'Lines can only be changed in Draft or Quotation.')
        elif form.is_valid():
            form.save()
            messages.success(request, 'Line added.')
        else:
            messages.error(request, 'Please fix the errors in the line form.')
        if can_edit and not form.errors:
            return redirect('subscription_detail', pk=pk)
    labels = dict(Subscription.STATUS_CHOICES)
    next_statuses = [(s, labels[s]) for s in Subscription.TRANSITIONS[sub.status]]
    return render(request, 'subscriptions/detail.html', {
        'sub': sub, 'lines': sub.lines.select_related('product', 'variant', 'tax'),
        'history': sub.history.select_related('changed_by'), 'form': form,
        'can_edit': can_edit, 'next_statuses': next_statuses})


@staff_only
@require_POST
def subscription_status(request, pk):
    sub = get_object_or_404(Subscription, pk=pk)
    new = request.POST.get('status', '')
    if new in ('quotation', 'confirmed', 'active') and not sub.lines.exists():
        messages.error(request, 'Add at least one line first.')
    else:
        try:
            sub.change_status(new, request.user)
            messages.success(request, f'Status changed to {sub.get_status_display()}.')
        except ValidationError as e:
            messages.error(request, ' '.join(e.messages))
    return redirect('subscription_detail', pk=pk)


@staff_only
@require_POST
def line_delete(request, pk):
    line = get_object_or_404(SubscriptionLine, pk=pk)
    sub_pk = line.subscription_id
    if line.subscription.status in ('draft', 'quotation'):
        line.delete()
        messages.success(request, 'Line removed.')
    else:
        messages.error(request, 'Lines can only be changed in Draft or Quotation.')
    return redirect('subscription_detail', pk=sub_pk)