from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.

def dashboard(request):
    return HttpResponse("Employment History Dashboard - Coming Soon")

def position_list(request):
    return HttpResponse("Position List - Coming Soon")

def position_create(request):
    return HttpResponse("Position Create - Coming Soon")

def position_detail(request, pk):
    return HttpResponse(f"Position Detail {pk} - Coming Soon")

def skill_list(request):
    return HttpResponse("Skill List - Coming Soon")
