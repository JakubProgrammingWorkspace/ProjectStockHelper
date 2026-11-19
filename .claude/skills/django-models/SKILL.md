---
name: django-models
description: "Conventions for Django model definitions, database upsert patterns, query optimisation, and migrations in this codebase. Use this skill whenever writing or editing a Django model, performing any database write (create, update, upsert, bulk insert), writing queryset logic, or creating/modifying a migration — even if the user just says 'save this to the database', 'add a model field', or 'write a migration'."
---

# Django Models

## Model Conventions

```python
class Calendar(models.Model):
    # Natural-key fields first
    ticker = models.CharField(max_length=20)
    date = models.DateField(db_index=True)   # db_index on any filter/order_by field

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Constants on the class — no magic strings/numbers in services
    FORM_TYPE_8K = '8-K'
    FORM_TYPE_10K = '10-K'

    TAG_ID_MAPPING = {
        1: 'SalesRevenueNet',
        4: 'NetIncomeLoss',
    }

    class Meta:
        unique_together = [('ticker', 'date')]

    def __str__(self):
        return f"{self.ticker} {self.date}"   # only guaranteed fields
```

- Multi-field unique constraints on natural keys (`unique_together` or `UniqueConstraint`)
- `auto_now_add` for `created_at`, `auto_now` for `updated_at`
- `__str__` must reference only fields guaranteed to exist

---

## Database Access

### Upsert patterns — pick the right one

```python
# Conditional update — do NOT silently overwrite existing data
earnings_record_instance, is_newly_created = Calendar.objects.get_or_create(
    ticker=incoming_market_data['ticker'],
    date=incoming_market_data['date'],
    defaults={...},
)
if not is_newly_created:
    earnings_record_instance.current_eps = incoming_market_data['current_eps']
    earnings_record_instance.save(update_fields=['current_eps', 'surprise'])

# Always-update upsert
ticker_record, _ = GlobalTickerMetadata.objects.update_or_create(
    ticker=target_ticker_symbol,
    defaults={'last_sync_timestamp': current_utc_time},
)

# High-volume ingestion
from django.db import transaction

with transaction.atomic():
    Calendar.objects.bulk_create(
        pending_record_instances, 
        update_conflicts=True, 
        update_fields=['revenue', 'net_income']
    )
```

- `get_or_create` → existing data must not be silently overwritten
- `update_or_create` → overwriting is always correct
- `bulk_create(update_conflicts=True)` → high-volume ingestion
- Always `transaction.atomic()` for bulk and multi-step writes
- Always `update_fields=[...]` to avoid touching unrelated columns

### Query optimisation

Never query inside loops — always use `select_related` (FK/OneToOne) or
`prefetch_related` (M2M/reverse FK).

Encapsulate reusable filter chains in a custom `QuerySet`:

```python
class OrderQuerySet(models.QuerySet):
    def filter_active_undelivered_orders(self) -> 'OrderQuerySet':
        """Retrieve all orders that are currently active and not yet delivered."""
        return self.filter(status=OrderStatus.ACTIVE, delivery_date__isnull=True)

class Order(models.Model):
    objects = OrderQuerySet.as_manager()

# usage
active_orders_list = Order.objects.filter_active_undelivered_orders()
```

No raw SQL unless absolutely necessary; if unavoidable, use parameterised queries only.

---

## Migrations

- **CRITICAL RULE:** If you change anything in the models, you MUST run migrations. It must be done in two steps: first create migrations (`make create-migrations`) and then apply them (`make execute-migrations`). Always ask user for confirmation before applying migrations.

- **Never edit an applied migration** — always create a new one
- New fields on existing rows must have a `default` or `null=True`
- New optional fields: `null=True, blank=True`
- `CharField` / `TextField`: never `null=True` — use `blank=True, default=""`
- Squash only when the entire team is in sync
