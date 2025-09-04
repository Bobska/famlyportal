from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.

def dashboard(request):
    return HttpResponse("Household Budget Dashboard - Coming Soon")

def budget_list(request):
    return HttpResponse("Budget List - Coming Soon")

def budget_create(request):
    return HttpResponse("Budget Create - Coming Soon")

def expense_list(request):
    return HttpResponse("Expense List - Coming Soon")

def income_list(request):
    return HttpResponse("Income List - Coming Soon")
