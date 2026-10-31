from django.contrib import messages
from django.shortcuts import render, redirect
from .forms import SignupForm

def signup(request):
    form = SignupForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Account created. Please log in.')
        return redirect('login')
    return render(request, 'accounts/signup.html', {'form': form})