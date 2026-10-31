from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from accounts.views import signup          # <- this line was missing

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', signup, name='signup'),
    path('', TemplateView.as_view(template_name='base.html'), name='dashboard'),
    path('subscriptions/', include('subscriptions.urls')),
    path('invoices/', include('billing.urls')),
]
