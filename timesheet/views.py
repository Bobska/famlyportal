from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.

def dashboard(request):
    return HttpResponse("Timesheet Dashboard - Coming Soon")

def entry_list(request):
    return HttpResponse("Entry List - Coming Soon")

def entry_create(request):
    return HttpResponse("Entry Create - Coming Soon")

def entry_detail(request, pk):
    return HttpResponse(f"Entry Detail {pk} - Coming Soon")

def entry_update(request, pk):
    return HttpResponse(f"Entry Update {pk} - Coming Soon")

def entry_delete(request, pk):
    return HttpResponse(f"Entry Delete {pk} - Coming Soon")

def job_list(request):
    return HttpResponse("Job List - Coming Soon")

def job_create(request):
    return HttpResponse("Job Create - Coming Soon")

def reports(request):
    return HttpResponse("Reports - Coming Soon")
