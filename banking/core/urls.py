from django.urls import path
from .views import AccountAPI, AuditLogAPI, TransferAPI, BalanceAPI

urlpatterns = [
    path('v1/transfer/', TransferAPI.as_view(), name='transfer'),
    path('v1/balance/', BalanceAPI.as_view(), name='balance'),
    path('v1/accounts/', AccountAPI.as_view(), name='account_api'),
    path('v1/audit-logs/', AuditLogAPI.as_view(), name='audit_log_api'),

]
