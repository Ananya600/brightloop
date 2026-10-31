"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from accounts.views import signup    
from django.urls import include
from accounts.views import signup, home, staff_create
from accounts.forms import StrongSetPasswordForm

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', signup, name='signup'),
    path('', home, name='dashboard'),
    path('staff/new/', staff_create, name='staff_create'),
    path('portal/', include('portal.urls')),
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='accounts/auth_form.html',
        email_template_name='accounts/password_reset_email.txt',
        subject_template_name='accounts/password_reset_subject.txt',
        extra_context={'title': 'Reset password'}), name='password_reset'),
    path('password-reset/sent/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/auth_message.html',
        extra_context={'title': 'Check your email',
                   'message': 'If that email is registered, a reset link has been sent.'}),
        name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/auth_form.html', form_class=StrongSetPasswordForm,
        extra_context={'title': 'Set a new password'}), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/auth_message.html',
        extra_context={'title': 'Password changed',
                   'message': 'You can now log in with your new password.'}),
        name='password_reset_complete'),
]
