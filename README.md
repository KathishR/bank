## 💸 Money Transfer Trigger — Customer-initiated Flow

Purpose: describe the end-to-end flow, checks, transactional update, logging, and handling of edge cases for a user-initiated transfer.

### Actors

Primary actors:

| Actor | Role | Responsibilities | Why needed |
|---|---:|---|---|
| Customer (initiator) | End user initiating transfer | Provide auth token, from/to accounts, amount, optional schedule | Source of intent — drives authorization and business rules |
| From Account (sender) | Source of funds | Hold balance, enforce available funds and daily limits | Must be validated & locked to avoid double-spend |
| To Account (receiver) | Recipient of funds | Receive credited amount and maintain balance | Completes the transfer; used for reconciliation |
| Auth Service / Token Validator | Authentication & authorization | Validate JWT, scopes, user status, token revocation | Ensures only authorized actions proceed |

Supporting/system actors:

| Actor | Role | Responsibilities | Why needed |
|---|---:|---|---|
| Database (Transactional DB) | Single source of truth for balances/transactions | Persist accounts, transactions, scheduled transfers, idempotency keys | Atomic updates and durable state |
| Redis (counter/cache) | Fast counters and short-term state | Daily counters, rate-limits, locks, TTL-backed keys | Low-latency enforcement of daily limits and transient state |
| Celery / Task Runner | Async execution for scheduled transfers | Enqueue and execute scheduled transfers, retries, idempotency | Decouples scheduling and execution; handles late/long work |
| AuditLog / Logging system | Forensics & compliance | Persist attempt records, outcomes, metadata (user, IP, request id) | Required for audits, dispute resolution, alerts |
| Notification service | User notifications | Send success/failure emails/SMS/push | UX and user-facing confirmations |
| Monitoring & Metrics (Prometheus, Sentry) | Observability | Track attempts, failures, rate-limits, latencies, errors | Alerting and incident response |
| Anti-fraud / Risk service | Risk evaluation | Score transfers, flag suspicious activity | Prevents fraud and enforces manual review workflows |
| Idempotency store | Deduplication | Persist idempotency keys and outcomes | Prevents double-processing on retries |

### Why explicit actors & responsibilities matter
- Clear ownership: maps each capability to a service/team for faster debugging and change control.  
- Security: isolates auth, fraud, and persistence so failures in one layer don't silently corrupt state.  
- Reliability: separates fast-path counters (Redis) from source-of-truth (DB) and provides DB fallback.  
- Observability & compliance: ensures every attempt is recorded for audits and dispute resolution.  
- Scalability: lets high-throughput components (counters, task queues) scale independently from transactional DB.

### 1) High-level flow
1. Authenticate request (JWT).
2. Validate accounts exist and are active.
3. Validate sender has sufficient balance.
4. Validate daily limit (Redis counter with DB fallback).
5. Perform atomic DB transaction: debit sender, credit receiver, insert Transaction and AuditLog records.
6. Return success or specific error.
7. (Optional) If transfer is scheduled, enqueue Celery task instead of immediate DB transfer.

### 2) Example API (request / responses)
Request:
```
POST /api/v1/transfer/
Authorization: Bearer <access_token>
{
    "from_account": "ACC123",
    "to_account": "ACC456",
    "amount": 1000.00,
    "schedule_at": null   # ISO timestamp to schedule; null for immediate
}
```

Success (200 / 201):
```
{
    "transaction_id": "TXN_0001",
    "status": "completed",
    "balance": 4500.00
}
```

Errors:
- 400 Bad Request — validation errors (e.g., daily limit exceeded)
- 402 / 400 — insufficient funds
- 409 Conflict — concurrent update conflict (retryable)
Example error payloads:
```
{ "detail": "Insufficient funds." }
{ "detail": "Daily transaction limit exceeded. Try again tomorrow." }
```

### 3) Atomic DB operation (conceptual / Django pseudocode)
- Use a DB transaction + row-level locks (SELECT ... FOR UPDATE / select_for_update) to avoid race conditions.
- Example pattern:
```python
from django.db import transaction

@transaction.atomic
def transfer(from_acc_id, to_acc_id, amount, user, meta):
        # lock rows
        from_acc = Account.objects.select_for_update().get(pk=from_acc_id)
        to_acc = Account.objects.select_for_update().get(pk=to_acc_id)

        if from_acc.balance < amount:
                raise InsufficientFunds()

        # update balances
        from_acc.balance -= amount
        to_acc.balance += amount
        from_acc.save()
        to_acc.save()

        # record transaction + audit
        txn = Transaction.objects.create(..., amount=amount, status='completed')
        AuditLog.objects.create(transaction=txn, user=user, action='transfer', outcome='success', meta=meta)
        return txn
```
- Wrap with retry/backoff on serialized errors (e.g., transaction serialization failures).

### 4) Daily limit check (Redis atomic counter + DB fallback)
- Use Redis INCR with TTL per account/day key:
```
KEY = f"daily:{account_id}:{YYYYMMDD}"
count = redis.incrbyfloat(KEY, amount)
if redis.ttl(KEY) == -1:
        redis.expire(KEY, seconds_until_midnight)
if count > account.daily_limit:
        # concurrently rollback or deny
```
- If Redis unavailable, compute total from DB (sum of today's transactions) and enforce limit.

### 5) Scheduled transfers (Celery)
- If schedule_at provided, persist a ScheduledTransfer record and enqueue a Celery task:
    - Celery task performs the same atomic transfer routine at execution time.
    - Use idempotency key (transaction or schedule id) to avoid double-processing.
    - Task should re-check balance & limits and log outcome into AuditLog.

### 6) Audit & observability
- Always write AuditLog entries for attempts (success/failure) including: user, IP, request id, input payload, reason if failed.
- Correlate logs with request-id and trace id for debugging.
- Metrics: transfer attempts, successes, failures, rate-limited counts.

### 7) Edge cases & handling
- Insufficient funds: return 400/402 with clear message; log as failed audit event.
- Exceeding daily limits: return 400 with limit details; increment a rate-limit metric.
- Concurrent updates: detect serialization errors/locked rows, retry with bounded attempts; return 409 if persistent.
- Partial failures: never leave balances inconsistent — if any DB write fails, rollback the whole transaction and log failure.
- Redis inconsistency: if Redis indicates limit exceeded but DB shows otherwise, prefer DB-consistent enforcement and reconcile counters asynchronously.

Implementation notes:
- Keep token TTLs short or use blacklist for revocation.
- Use DB-backed idempotency keys for safe retries.
- Use structured logs and metrics for alerting on spikes in failures or rate-limits.
- Test edge cases with concurrent load tests and chaos scenarios.

