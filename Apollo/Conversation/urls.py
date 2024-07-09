from django.urls import path
from django.shortcuts import render
from .views import *


urlpatterns = [
    path("dashboard/", lambda request: render(request, template_name="index.html"), name="conversation-dashboard"),
    path("history/", History.as_view(), name="conversation-history"),
    path("converse/", Converse.as_view(), name="conversation-converse"),
    path("converse-history/", ConversationHistory.as_view(), name="conversation-converse-history"),
    path("documents/", Documents.as_view(), name="conversation-documents"),
    path("events/", EventsView.as_view(), name="conversation-events"),
    path("doctors/", DoctorsView.as_view(), name="conversation-doctors"),
    path("goal/", GoalsView.as_view(), name="conversation-goal"),
]
