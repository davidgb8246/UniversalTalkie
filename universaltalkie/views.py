from django.http import JsonResponse
from django.shortcuts import render

def heartbeat(request):
    return JsonResponse({"status": "ok"})
