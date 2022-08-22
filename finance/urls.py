"""finance URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
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

from . import views
from nab import views as nabViews

urlpatterns = [
    path('admin/', admin.site.urls),

    # Home Page.
    path('', views.Index, name='index'),
    path('dashboard/<int:year>/<int:month>/<int:day>/', views.Dashboard, name='dashboard'),
    path('summary/<int:year>/<int:month>/', views.Summary, name='summary'),

    path('update/', views.Update, name='update'),

    # Transactions
    path('transactions', views.Transactions, name='transactions'),

    # Budget
    path('budget', views.BudgetView, name='budget'),
    #path('budgetLock', views.LockBudget),

    # Unallocated
    path('unallocated', views.Unallocated, name='unallocated'),
    path('saveAllocations', views.SaveAllocations, name='saveAllocations'),

    path('unallocated_credits_all', views.UnallocatedCreditsAll, name='unallocated_credits_all'),
    path('unallocated_credits', views.UnallocatedCreditsToday, name='unallocated_credits'),
    path('unallocated_credits/<int:year>/<int:month>/<int:day>/', views.UnallocatedCredits, name='unallocated_credits_date'),
    path('save_transfers', views.SaveTransfers, name='save_transfers'),

    # CAPEX
    path('capex', views.CapexView, name='capex'),

    # Update NAB Transactions
    path('updateTransactions', nabViews.NABTransactions, name='updateTransactions')
]
