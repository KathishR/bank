from django.db import models
from django.contrib.auth.models import User

class Account(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    account_number = models.CharField(max_length=20, unique=True)
    balance = models.DecimalField(max_digits=12, decimal_places=2)
    daily_limit = models.DecimalField(max_digits=12, decimal_places=2, default=5000)

    def __str__(self):
        return f"{self.user.username}-{self.account_number}"

class Transaction(models.Model):
    txn_id = models.CharField(max_length=30, unique=True)
    from_account = models.ForeignKey(Account, related_name='sent', on_delete=models.CASCADE)
    to_account = models.ForeignKey(Account, related_name='received', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=[('pending','pending'),('completed','completed'),('failed','failed')])
    created_at = models.DateTimeField(auto_now_add=True)

class AuditLog(models.Model):
    txn = models.ForeignKey(Transaction, on_delete=models.CASCADE, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50)
    outcome = models.CharField(max_length=50)
    reason = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)


class ScheduledTransfer(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    from_account = models.ForeignKey('Account', related_name='scheduled_from', on_delete=models.CASCADE)
    to_account = models.ForeignKey('Account', related_name='scheduled_to', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    schedule_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_msg = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.amount} scheduled at {self.schedule_at}"
