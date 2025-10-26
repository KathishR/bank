from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta

from core.models import Account, Transaction, AuditLog, ScheduledTransfer


class AccountModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="kathish", password="testpass")
        self.account = Account.objects.create(
            user=self.user,
            account_number="ACC12345",
            balance=Decimal("10000.00"),
            daily_limit=Decimal("5000.00")
        )

    def test_account_creation(self):
        self.assertEqual(self.account.user.username, "kathish")
        self.assertEqual(self.account.balance, Decimal("10000.00"))
        self.assertEqual(str(self.account), "kathish-ACC12345")

    def test_unique_account_number(self):
        with self.assertRaises(Exception):
            Account.objects.create(
                user=self.user,
                account_number="ACC12345",  
                balance=Decimal("500.00")
            )


class TransactionModelTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="user1", password="testpass")
        self.user2 = User.objects.create_user(username="user2", password="testpass")

        self.acc1 = Account.objects.create(user=self.user1, account_number="A100", balance=Decimal("10000.00"))
        self.acc2 = Account.objects.create(user=self.user2, account_number="A200", balance=Decimal("5000.00"))

        self.txn = Transaction.objects.create(
            txn_id="TXN001",
            from_account=self.acc1,
            to_account=self.acc2,
            amount=Decimal("1000.00"),
            status="pending"
        )

    def test_transaction_creation(self):
        self.assertEqual(self.txn.amount, Decimal("1000.00"))
        self.assertEqual(self.txn.status, "pending")
        self.assertEqual(self.txn.from_account.account_number, "A100")

    def test_transaction_unique_id(self):
        with self.assertRaises(Exception):
            Transaction.objects.create(
                txn_id="TXN001", 
                from_account=self.acc1,
                to_account=self.acc2,
                amount=Decimal("100.00"),
                status="pending"
            )


class AuditLogModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="testpass")
        self.acc1 = Account.objects.create(user=self.user, account_number="ACC100", balance=Decimal("5000"))
        self.acc2 = Account.objects.create(user=self.user, account_number="ACC200", balance=Decimal("3000"))

        self.txn = Transaction.objects.create(
            txn_id="TXN100",
            from_account=self.acc1,
            to_account=self.acc2,
            amount=Decimal("200.00"),
            status="completed"
        )

        self.log = AuditLog.objects.create(
            txn=self.txn,
            user=self.user,
            action="transfer",
            outcome="success",
            reason="Fund transfer completed"
        )

    def test_audit_log_creation(self):
        self.assertEqual(self.log.txn.txn_id, "TXN100")
        self.assertEqual(self.log.action, "transfer")
        self.assertEqual(self.log.outcome, "success")

    def test_audit_log_nullable_fields(self):
        log = AuditLog.objects.create(
            txn=self.txn,
            user=None,
            action="test",
            outcome="ok"
        )
        self.assertIsNone(log.user)
        self.assertEqual(log.outcome, "ok")


class ScheduledTransferModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="scheduled_user", password="testpass")
        self.from_acc = Account.objects.create(user=self.user, account_number="S100", balance=Decimal("10000"))
        self.to_acc = Account.objects.create(user=self.user, account_number="S200", balance=Decimal("2000"))

        self.schedule_time = timezone.now() + timedelta(days=1)

        self.scheduled_transfer = ScheduledTransfer.objects.create(
            user=self.user,
            from_account=self.from_acc,
            to_account=self.to_acc,
            amount=Decimal("500.00"),
            schedule_at=self.schedule_time
        )

    def test_scheduled_transfer_creation(self):
        self.assertEqual(self.scheduled_transfer.status, "pending")
        self.assertEqual(self.scheduled_transfer.amount, Decimal("500.00"))
        self.assertIn("scheduled at", str(self.scheduled_transfer))

    def test_scheduled_transfer_default_status(self):
        self.assertEqual(self.scheduled_transfer.status, "pending")

    def test_failed_scheduled_transfer(self):
        self.scheduled_transfer.status = "failed"
        self.scheduled_transfer.error_msg = "Insufficient balance"
        self.scheduled_transfer.save()

        updated = ScheduledTransfer.objects.get(pk=self.scheduled_transfer.pk)
        self.assertEqual(updated.status, "failed")
        self.assertEqual(updated.error_msg, "Insufficient balance")

    def test_future_schedule(self):
        self.assertTrue(self.scheduled_transfer.schedule_at > timezone.now())