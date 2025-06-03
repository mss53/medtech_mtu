"""
URL configuration for medtech_mtu project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib.auth import views as auth_views
from inventory.views import stock_list, upcoming_maintenance, home, MyLoginView, movements_list, movement_create, export_movements_excel, add_maintenance, send_maintenance_reminder, purchase_requests_list, purchase_request_create, purchase_request_edit, purchase_request_detail, create_purchase_order, purchase_order_detail, itemcard_detail

def my_logout(request):
    logout(request)
    return redirect('/login/')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('stocks/', stock_list, name='stock_list'),
    path('maintenance/upcoming/', upcoming_maintenance, name='upcoming_maintenance'),
    path('login/', MyLoginView.as_view(), name='login'),
    path('logout/', my_logout, name='logout'),
    path('', home, name='home'),
    path('movements/', movements_list, name='movements'),
    path('movements/create/', movement_create, name='movement_create'),
    path('movements/export_excel/', export_movements_excel, name='movements_export_excel'),
    path('maintenance/add/', add_maintenance, name='maintenance_add'),
    path('maintenance/remind/<int:schedule_id>/', send_maintenance_reminder, name='maintenance_remind'),
    path('purchase_requests/', purchase_requests_list, name='purchase_requests_list'),
    path('purchase_requests/create/', purchase_request_create, name='purchase_request_create'),
    path('purchase_requests/<int:pk>/edit/', purchase_request_edit, name='purchase_request_edit'),
    path('purchase_requests/<int:pk>/', purchase_request_detail, name='purchase_request_detail'),
    path('purchase_requests/<int:pk>/order/', create_purchase_order, name='create_purchase_order'),
    path('purchase_orders/<int:pk>/', purchase_order_detail, name='purchase_order_detail'),
    path('itemcards/<int:pk>/', itemcard_detail, name='itemcard_detail'),
]


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

