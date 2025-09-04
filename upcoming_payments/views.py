from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.

def dashboard(request):
    return HttpResponse("Upcoming Payments Dashboard - Coming Soon")

def payment_list(request):
    return HttpResponse("Payment List - Coming Soon")

def payment_create(request):
    return HttpResponse("Payment Create - Coming Soon")

def reminder_list(request):
    return HttpResponse("Reminder List - Coming Soon")
