from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.

def dashboard(request):
    return HttpResponse("Credit Cards Dashboard - Coming Soon")

def card_list(request):
    return HttpResponse("Card List - Coming Soon")

def card_create(request):
    return HttpResponse("Card Create - Coming Soon")

def transaction_list(request):
    return HttpResponse("Transaction List - Coming Soon")
