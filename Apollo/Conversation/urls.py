from django.urls import path
from django.shortcuts import render
from .views import *
from rest_framework.decorators import authentication_classes


class Test(APIView):

    authentication_classes = [TokenAuthentication]

    def get(self, request: Request):
        return render(request, "test.html")



urlpatterns = [
    path("dashboard/", lambda request: render(request, template_name="dashboard.html"), name="conversation-dashboard"),
    path("chat/", lambda request: render(request, template_name="chat.html"), name="conversation-chat"),
    path("connect/", lambda request: render(request, template_name="connect.html"), name="conversation-connect"),
    path("history/", History.as_view(), name="conversation-history"),
    path("keyinformation/", ConversationHistoryWithFaissSupportView.as_view(), name="conversation-keyinformation"),
    path("converse/", Converse.as_view(), name="conversation-converse"),
    path("chathistory/", ChatHistoryView.as_view(), name="conversation-converse-history"),
    path("documents/", Documents.as_view(), name="conversation-documents"),
    path("doctor-events/", DoctorEventView.as_view(), name="conversation-doctor-events"),
    path("doctors/", DoctorView.as_view(), name="conversation-doctors"),
    path("goal/", GoalsView.as_view(), name="conversation-goal"),

    path("test/", Test.as_view(), name="test"),
    # path("test-view/", TestAPI.as_view(), name="test-test"),
    # path("test-view1/", TestAPI1.as_view(), name="test-test1")
]
