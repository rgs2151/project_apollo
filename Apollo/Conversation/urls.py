from django.urls import path
from django.shortcuts import render
from .views import *


urlpatterns = [
    path("dashboard/", lambda request: render(request, template_name="dashboard.html"), name="conversation-dashboard"),
    path("chat/", lambda request: render(request, template_name="chat.html"), name="conversation-chat"),
    path("connect/", lambda request: render(request, template_name="connect.html"), name="conversation-connect"),
    path("history/", History.as_view(), name="conversation-history"),
    path("converse/", Converse.as_view(), name="conversation-converse"),
    path("converse-history/", ConversationHistory.as_view(), name="conversation-converse-history"),
    path("events/", Events.as_view(), name="conversation-events"),
]
