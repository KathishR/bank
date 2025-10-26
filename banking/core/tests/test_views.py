from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
from unittest.mock import patch
from datetime import timedelta
import uuid

from core.models import Account, Transaction, AuditLog, ScheduledTransfer

from rest_framework.test import APIClient

class APITestBase(TestCase):
    def setUp(self):
        self.client = APIClient()  # DRF client
        self.user1 = User.objects.create_user(username="user1", password="pass")
        self.user2 = User.objects.create_user(username="user2", password="pass")
        self.acc1 = Account.objects.create(user=self.user1, account_number="ACC1", balance=Decimal("1000"), daily_limit=Decimal("500"))
        self.acc2 = Account.objects.create(user=self.user2, account_number="ACC2", balance=Decimal("500"), daily_limit=Decimal("500"))
        self.client.force_authenticate(user=self.user1)  # authenticate DRF API



class BalanceAPITests(APITestBase):
    def test_get_balance(self):
        url = reverse("balance")  # updated
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["balance"], float(self.acc1.balance))


class AccountAPITests(APITestBase):
    def test_get_accounts(self):
        url = reverse("account_api")  # already matches
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["account_number"], "ACC1")

    def test_create_account(self):
        url = reverse("account_api")  # already matches
        data = {"account_number": "ACC3", "balance": "2000"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Account.objects.filter(account_number="ACC3").exists())


from unittest.mock import patch, MagicMock


from unittest.mock import patch

   

class TransferAPITests(APITestBase):

    @patch("core.views.redis_conn")
    def test_successful_transfer(self, mock_redis):
        # mock Redis methods
        mock_redis.incrbyfloat.return_value = 100  # below daily limit
        mock_redis.ttl.return_value = -1
        mock_redis.expire.return_value = True

        url = reverse("transfer")
        data = {"from_account": "ACC1", "to_account": "ACC2", "amount": "100"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        txn = Transaction.objects.get(txn_id=response.json()["transaction_id"])
        self.assertEqual(txn.amount, Decimal("100"))

    @patch("bank_app.views.redis_conn")
    def test_insufficient_balance(self, mock_redis):
        mock_redis.incrbyfloat.return_value = 100  # below daily limit
        mock_redis.ttl.return_value = -1
        mock_redis.expire.return_value = True

        url = reverse("transfer")
        data = {"from_account": "ACC1", "to_account": "ACC2", "amount": "5000"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Insufficient funds", response.json()["detail"])


    def test_insufficient_balance(self):
        url = reverse("transfer")  # updated
        data = {"from_account": "ACC1", "to_account": "ACC2", "amount": "5000"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Insufficient funds", response.json()["detail"])

    def test_daily_limit_exceeded(self):
        url = reverse("transfer")  # updated
        data = {"from_account": "ACC1", "to_account": "ACC2", "amount": "600"}  # exceeds daily_limit 500
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Daily transaction limit", response.json()["detail"])

    @patch("core.views.execute_scheduled_transfer.apply_async")
    def test_scheduled_transfer(self, mock_task):
        url = reverse("transfer")  # updated
        schedule_time = (timezone.now() + timedelta(days=1)).isoformat()
        data = {"from_account": "ACC1", "to_account": "ACC2", "amount": "100", "schedule_at": schedule_time}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        sched = ScheduledTransfer.objects.get(id=response.json()["scheduled_transfer_id"])
        self.assertEqual(sched.amount, Decimal("100"))
        mock_task.assert_called_once()


class AuditLogAPITests(APITestBase):
    def setUp(self):
        super().setUp()
        # Create a transaction and audit log
        txn = Transaction.objects.create(
            txn_id=str(uuid.uuid4()),
            from_account=self.acc1,
            to_account=self.acc2,
            amount=Decimal("50"),
            status="completed"
        )
        AuditLog.objects.create(txn=txn, user=self.user1, action="transfer", outcome="success")

    def test_get_audit_logs(self):
        url = reverse("audit_log_api")  # updated
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        logs = response.json()
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["action"], "transfer")
        self.assertEqual(logs[0]["outcome"], "success")
