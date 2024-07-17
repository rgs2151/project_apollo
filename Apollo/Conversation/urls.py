from django.urls import path
from django.shortcuts import render
from .views import *
from rest_framework.decorators import authentication_classes


class Test(APIView):

    authentication_classes = [TokenAuthentication]

    def get(self, request: Request):
        return render(request, "test.html")



urlpatterns = [
    # Post APIs

    path("history/", History.as_view(), name="conversation-history"),
    path("keyinformation/", ConversationHistoryWithFaissSupportView.as_view(), name="conversation-keyinformation"),
    # path("converse/", Converse.as_view(), name="conversation-converse"),
    path("converse/", ChatView.as_view(), name="conversation-chat"),
    path("chathistory/", ChatHistoryView.as_view(), name="conversation-converse-history"),
    path("documents/", Documents.as_view(), name="conversation-documents"),
    path("doctor-events-dashboard/", DoctorEventDashboardView.as_view(), name="conversation-doctor-events-dashboard"),
    path("doctor-events/", DoctorEventView.as_view(), name="conversation-doctor-events"),
    path("doctors/", DoctorView.as_view(), name="conversation-doctors"),
    path("user-goals/", GoalsView.as_view(), name="conversation-user-goals"),
    path("user-events-dashboard", UserEventDashboardView.as_view(), name="conversation-user-events-dashboard"),

    # Get and Template APIs
    
    # For Users
    path("dashboard/", lambda request: render(request, template_name="dashboard.html"), name="conversation-dashboard"),
    path("chat/", lambda request: render(request, template_name="chat.html"), name="conversation-chat"),
    path("connect/", lambda request: render(request, template_name="connect.html"), name="conversation-connect"),
    
    # For Doctors
    # path("dr_dashboard/", dr_dashboad , name="conversation-dr-dashboard"),
    path("dr_calander/", lambda request: render(request, template_name="dr_calander.html"), name="conversation-dr-calander"),
    path("dr_circle/", lambda request: render(request, template_name="dr_circle.html"), name="conversation-dr-chat"),

    path("test/", Test.as_view(), name="test")
]
