# Pyton Coding Rules

## General

- Strictly follow PEP 8 standards
- Place all imports at the top of the file
- Use `logger = logging.getLogger(__name__)` — never `print()`
- Never put secrets or environment-specific values in `settings.py` — use `django-environ`
  or `python-decouple` with split settings (`base` / `local` / `production`)
- Base URLs must live in `.env`

---

## Naming Conventions

### Unique and Descriptive Names
Avoid generic function names (e.g., `run`, `process`, `handle`, `validate`). Use specific, context-rich names:
- ✅ `process_user_registration_data()`
- ✅ `validate_email_format_input()`
- ✅ `send_payment_api_request()`

### Domain-Prefixed Function Names
When similar operations exist across domains, prefix with context:
- ✅ `auth_validate_jwt_token()`
- ✅ `order_calculate_total_amount()`
- ✅ `inventory_update_product_levels()`

### Action-Object-Context Pattern
Structure function names as: `{action}_{object}_{context}`
- ✅ `create_user_profile_from_registration()`
- ✅ `fetch_active_order_items_by_status()`

### Class Naming
Classes must end with their responsibility (Service, Calculator, Validator) and indicate domain:
- ✅ `UserRegistrationValidator`
- ✅ `SubscriptionBillingCalculator`

---

## Function Signatures

- **Complete Type Annotations**: Provide comprehensive type hints for all parameters and return values.
- **Explicit Imports**: Always import types (List, Optional, Decimal, datetime, etc.) explicitly.

---

## Documentation for Context

- **Comprehensive Docstrings**: Include docstrings explaining flow, Args, Returns, and Raises.
- **Module-Level Context**: Provide module docstrings explaining domain boundaries and naming prefixes.

---

## Variable Naming

- **Descriptive Names**: Use full, contextual variable names throughout function bodies (e.g., `subtotal_before_discounts`).
- **Avoid Single Letter Variables**: Only allowed for standard math operations or very short-lived loop counters.
- ✅ `for current_user_account in user_account_list:`

---

## Architecture

### Thin views, fat services

Views handle HTTP only — parse request, call a service, return response.
No ORM queries, no business logic, no email sending inside views.

### Thin models — no business logic

Models are for field definitions, `__str__`, `Meta`, and simple `@property` only.
No service calls, no email sending, no cross-model orchestration.

### No signals for business logic

Signals are for decoupled side effects only (e.g. audit logs).
Never use them to trigger core business logic — call service methods explicitly.

### Always wrap multi-step writes in transactions

Any operation that touches more than one model must be wrapped in
`transaction.atomic()`. Put it at the service layer, not the view.

### Raise domain exceptions from services, not HTTP exceptions

Services raise domain-level exceptions. Views translate them to HTTP.

```python
# services/exceptions.py
class OrderNotFound(Exception): pass

# view maps it
try:
    order = order_service.activate(order_id)
except OrderNotFound:
    raise Http404
```

---

> **See also**
> - `django-services` skill — service classes, commands, API clients, DTOs, error handling
> - `django-models` skill — model conventions, upsert patterns, queries, migrations