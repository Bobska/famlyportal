from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def dashboard(request):
    """Budget Basic main dashboard view."""
    context = {
        'page_title': 'Budget Basic',
        'app_name': 'budget_basic',
    }
    return render(request, 'budget_basic/dashboard.html', context)


@login_required
def main(request):
    """Budget Basic main transactions view."""
    context = {
        'page_title': 'Transactions',
        'app_name': 'budget_basic',
    }
    return render(request, 'budget_basic/main.html', context)
