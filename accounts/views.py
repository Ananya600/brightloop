from django.contrib import messages
from django.shortcuts import render, redirect
from .forms import SignupForm
from django.contrib.auth.decorators import login_required
from .decorators import role_required
from .forms import StaffForm   # keep your existing SignupForm import too

def signup(request):
    form = SignupForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Account created. Please log in.')
        return redirect('login')
    return render(request, 'accounts/signup.html', {'form': form})

@login_required
def home(request):
    if request.user.role == 'customer' and not request.user.is_superuser:
        return redirect('my_subscriptions')
    return redirect('subscription_list')


@role_required('admin')
def staff_create(request):
    form = StaffForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        u = form.save()
        messages.success(request, f'Staff account created for {u.email}.')
        return redirect('staff_create')
    return render(request, 'accounts/auth_form.html', {'form': form, 'title': 'Add staff member'})