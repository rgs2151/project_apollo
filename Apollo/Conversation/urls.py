from django.urls import path
from django.shortcuts import render
from .views import *


urlpatterns = [
    path("history/", History.as_view(), name="conversation-history"),
    path("dashboard/", lambda request: render(request, template_name="index.html"), name="conversation-dashboard"),
]
