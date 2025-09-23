---
applyTo: '**'
---
Refactoring Guidelines
🔹 General Python & PEP 8

Follow PEP 8 (consistent naming, spacing, and line length).

Use meaningful, descriptive names for variables, functions, classes, and methods.

Remove unused imports, redundant code, and dead logic.

Split large functions/classes into smaller, testable units.

🔹 Django Models

Use Meta options correctly (ordering, verbose_name, unique_together, etc.).

Ensure related names are meaningful when using ForeignKey/ManyToMany.

Move business logic into model methods or managers, not views.

Optimize queries with select_related and prefetch_related.

Add docstrings explaining why certain constraints or fields exist.

🔹 Django Views

Follow Class-Based View (CBV) conventions where appropriate.

Avoid putting business logic directly in views — delegate to services or managers.

Use get_object_or_404 and get_list_or_404 instead of manual query checks.

Add inline comments for tricky context data or custom permission checks.

🔹 Django Forms & Serializers

Keep validation logic inside clean_<field> or validate_<field> methods.

Add docstrings to explain validation rules.

Ensure reusable form/serializer fields are abstracted properly.

🔹 Django Templates

Avoid complex business logic in templates — move it to the view/context.

Refactor repeated template blocks into template tags or includes.

🔹 Django Admin

Keep admin definitions simple and register models cleanly.

Use list_display, list_filter, and search_fields effectively.

🔹 Django Middleware / Signals

Ensure signals don’t contain heavy business logic (delegate to services).

Comment why a middleware/signal is required and what problem it solves.

🔹 Testing & Maintainability

Structure code for unit testability.

Make refactored code easy to mock/stub in Django’s test framework.

Add docstrings explaining expected inputs/outputs for critical functions.

📘 Documentation Guidelines

Add docstrings (""" """) for all models, views, and serializers.

Use inline comments for:

Non-obvious query optimizations

Business rules (why, not just what)

Any edge case handling

Include explanations of why code is written in a specific way (not just what it does).