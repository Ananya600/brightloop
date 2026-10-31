from django.urls import path
from . import views

urlpatterns = [
    path('subscriptions/', views.my_subscriptions, name='my_subscriptions'),
    path('subscriptions/<int:pk>/', views.my_subscription, name='my_subscription'),
    path('invoices/', views.my_invoices, name='my_invoices'),
    path('invoices/<int:pk>/', views.my_invoice, name='my_invoice'),
    path('payments/', views.my_payments, name='my_payments'),
]