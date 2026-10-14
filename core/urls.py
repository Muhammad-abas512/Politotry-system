from django.urls import path
from . import views
from . import new_accounts, market_rate, inventory_managment, reports, opening, accounts_views

urlpatterns = [
    path('', views.login_view, name='login'),


    path('parties/', new_accounts.parties, name='parties'),
    path('expense-head/', new_accounts.expense_head, name='expense_head'),

    # Chart of Accounts & Vouchers Module
    path('chart-of-accounts/', accounts_views.chart_of_accounts, name='chart_of_accounts'),
    path('voucher-entry/', accounts_views.voucher_entry, name='voucher_entry'),
    path('account-ledger/', accounts_views.account_ledger, name='account_ledger'),

    path('waste-rate/', market_rate.waste_rate, name='waste_rate'),
    path('fat-rate/', market_rate.fat_rate, name='fat_rate'),
    path('broiler-rate/', market_rate.broiler_rate, name='broiler_rate'),

    path('sells/', inventory_managment.sells, name='sells'),
    path('purchase_receiving/', inventory_managment.purchase_receiving, name='purchase_receiving'),

    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('user-management/', views.user_management, name='user_management'),
    path('hierarchy/', views.hierarchy_management, name='hierarchy'),
    path('today-rate/', views.today_rate, name='today_rate'),
    path('waste_entry/', views.waste_entry, name='waste_entry'),



 
    path('receipt/', views.receipt, name='receipt'),
    path('payment/', views.payment, name='payment'),
    path('waste-payment/', views.waste_payment, name='waste_payment'),
    path('expenses/', views.expenses, name='expenses'),



    path('party_ledger/', reports.party_ledger, name='party_ledger'),
    path('get_party_ledger/', reports.get_party_ledger, name='get_party_ledger'),
    path('export-ledger-pdf/', reports.export_ledger_pdf, name='export_ledger_pdf'),

    path('purchase_report/', reports.purchase_report, name='purchase_report'),
    path('purchase-report/print/', reports.purchase_report_print, name='purchase_report_print'),
    path('sells_report/', reports.sells_report, name='sells_report'),
    path('sells-report/print/', reports.sells_report_print, name='sells_report_print'),
    path('profit_loss_report/', reports.profit_loss_report, name='profit_loss_report'),
    path('profit-loss-report/print/', reports.profit_loss_report_print, name='profit_loss_report_print'),
    path('cash_ledger/', reports.cash_ledger, name='cash_ledger'),
    path('cash-ledger/print/', reports.cash_ledger_print, name='cash_ledger_print'),
    path('broiler_report/', reports.broiler_report, name='broiler_report'),
    path('broiler-report/print/', reports.broiler_report, name='broiler_report_print'),
    path('cashreport/', reports.cash_report, name='cash_report'),
    path('cashreport/print/', reports.cash_report_print, name='cash_report_print'),
    path('net_position/', reports.net_position_report, name='net_position'),
    path('net-position/', reports.net_position_report, name='net_position_hyphen'),
    path('net_position/print/', reports.net_position_print, name='net_position_print'),
    path('net-position/print/', reports.net_position_print, name='net_position_print_hyphen'),



    path('opening/', opening.opening, name='opening'),
    path('cash/', opening.cash, name='cash'),



]