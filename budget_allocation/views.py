from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from accounts.decorators import family_required


@login_required
@family_required
def dashboard(request):
    """Budget Allocation Dashboard"""
    context = {
        'title': 'Budget Allocation Dashboard',
    }
    return render(request, 'budget_allocation/dashboard.html', context)
