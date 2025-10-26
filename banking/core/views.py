from django.views.generic import TemplateView
from django.db import transaction as db_transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_redis import get_redis_connection
from .models import Account, Transaction, AuditLog
from .serializers import TransferSerializer, AccountSerializer
import uuid
from .serializers import AccountSerializer
from .models import AuditLog
from .serializers import AuditLogSerializer
from .models import ScheduledTransfer
from .tasks import execute_scheduled_transfer

redis_conn = get_redis_connection("default")

class HomeTemplate(TemplateView):
    template_name = "transfer.html"

class BalanceAPI(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        accounts = Account.objects.filter(user=request.user)
        data = [{"account_number": acc.account_number, "balance": float(acc.balance)} for acc in accounts]
        return Response(data)


redis_conn = get_redis_connection("default")

class TransferAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TransferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            txn = self.perform_transfer(
                request.user,
                data['from_account'],
                data['to_account'],
                data['amount'],
                data.get('schedule_at')
            )

            if isinstance(txn, ScheduledTransfer):
                return Response({
                    "scheduled_transfer_id": txn.id,
                    "status": txn.status,
                    "schedule_at": txn.schedule_at
                })
            else:
                return Response({
                    "transaction_id": txn.txn_id,
                    "status": txn.status
                })

        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        

    def perform_transfer(self, user, from_acc_no, to_acc_no, amount, schedule_at=None):
        try:
            from_acc = Account.objects.select_for_update().get(account_number=from_acc_no)
        except Account.DoesNotExist:
            raise Exception(f"Sender account {from_acc_no} does not exist.")

        try:
            to_acc = Account.objects.select_for_update().get(account_number=to_acc_no)
        except Account.DoesNotExist:
            raise Exception(f"Receiver account {to_acc_no} does not exist.")

        if schedule_at:
            sched = ScheduledTransfer.objects.create(
                user=user,
                from_account=from_acc,
                to_account=to_acc,
                amount=amount,
                schedule_at=schedule_at
            )
            execute_scheduled_transfer.apply_async(
                args=[sched.id],
                eta=schedule_at  
            )
            return sched  

        #  Check daily limit (Redis)
        if from_acc.balance < amount:
            raise Exception("Insufficient funds in sender account.")
        

        key = f"daily:{from_acc.account_number}:{timezone.now().date()}"
        count = redis_conn.incrbyfloat(key, float(amount))
        if redis_conn.ttl(key) == -1:
            ttl = (timezone.now().replace(hour=23, minute=59, second=59) - timezone.now()).seconds
            redis_conn.expire(key, ttl)
        if count > float(from_acc.daily_limit):
            raise Exception(f"Daily transaction limit of {from_acc.daily_limit} exceeded.")

    

        txn_id = str(uuid.uuid4())
        with db_transaction.atomic():
            from_acc.balance -= amount
            to_acc.balance += amount
            from_acc.save()
            to_acc.save()

            txn = Transaction.objects.create(
                txn_id=txn_id,
                from_account=from_acc,
                to_account=to_acc,
                amount=amount,
                status='completed'
            )

            AuditLog.objects.create(
                txn=txn,
                user=user,
                action='transfer',
                outcome='success'
            )

        return txn

class AccountAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        accounts = Account.objects.filter(user=request.user)
        serializer = AccountSerializer(accounts, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = AccountSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class AuditLogAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List audit logs for the current user"""
        logs = AuditLog.objects.filter(user=request.user).order_by('-id') 
        serializer = AuditLogSerializer(logs, many=True)
        return Response(serializer.data)
