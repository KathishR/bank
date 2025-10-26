from celery import shared_task 
from .models import ScheduledTransfer

@shared_task
def execute_scheduled_transfer(sched_id):
    try:
        from .views import TransferAPI
        sched = ScheduledTransfer.objects.get(id=sched_id)
        if sched.status != 'pending':
            return 

        api = TransferAPI()
        txn = api.perform_transfer(
            from_acc_no=sched.from_account.account_number,
            to_acc_no=sched.to_account.account_number,
            amount=float(sched.amount),
            schedule_at=None
        )
        api.perform_transfer(
            from_acc_no=sched.from_account.account_number,
            to_acc_no=sched.to_account.account_number,
            amount=float(sched.amount),
            schedule_at=None
        )
        sched.status = 'completed'
        sched.save()
    except Exception as e:
        sched.status = 'failed'
        sched.error_msg = str(e)
        sched.save()
