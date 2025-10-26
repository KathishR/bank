from rest_framework import serializers
from .models import Account, Transaction, ScheduledTransfer
from .models import AuditLog


class TransferSerializer(serializers.Serializer):
    from_account = serializers.CharField()
    to_account = serializers.CharField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    schedule_at = serializers.DateTimeField(required=False, allow_null=True)


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'account_number', 'balance', 'daily_limit']


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = ['id', 'txn', 'user', 'action', 'outcome']
