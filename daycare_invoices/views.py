from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.

def dashboard(request):
    return HttpResponse("Daycare Invoices Dashboard - Coming Soon")

def invoice_list(request):
    return HttpResponse("Invoice List - Coming Soon")

def invoice_create(request):
    return HttpResponse("Invoice Create - Coming Soon")

def invoice_detail(request, pk):
    return HttpResponse(f"Invoice Detail {pk} - Coming Soon")

def payment_list(request):
    return HttpResponse("Payment List - Coming Soon")
