import json
from budget_basic.models import Payee, Category

# Create test data if needed
print("Current payees and their categories:")
payees = Payee.objects.all().prefetch_related('categories')

for payee in payees:
    categories = list(payee.categories.all())
    print(f"Payee: {payee.name}")
    print(f"  Categories: {[cat.name for cat in categories]}")
    print(f"  JSON format: {{'id': {payee.id}, 'name': '{payee.name}', 'categories': {[{'id': cat.id, 'name': cat.name} for cat in categories]}}}")
    print()

print("Testing the endpoint format:")
payee_list = [
    {
        'id': p.id, 
        'name': p.name,
        'categories': [{'id': cat.id, 'name': cat.name} for cat in p.categories.all()]
    } 
    for p in payees
]

print("Full payee list with categories:")
print(json.dumps(payee_list, indent=2))