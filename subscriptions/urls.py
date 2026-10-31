from django.urls import path
from . import views

urlpatterns = [
    path('', views.subscription_list, name='subscription_list'),
    path('new/', views.subscription_create, name='subscription_create'),
    path('from-template/', views.subscription_from_template, name='subscription_from_template'),
    path('<int:pk>/', views.subscription_detail, name='subscription_detail'),
    path('<int:pk>/status/', views.subscription_status, name='subscription_status'),
    path('lines/<int:pk>/delete/', views.line_delete, name='subscription_line_delete'),
]