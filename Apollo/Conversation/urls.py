from django.urls import path
from .views_templates import *


class Test(APIView):

    authentication_classes = [TokenAuthentication]

    def get(self, request: Request):
        return render(request, "test.html")



urlpatterns = [
    # Post APIs

    path("history/", History.as_view(), name="conversation-history"),
    path("converse/", Converse.as_view(), name="conversation-converse"),
    path("converse-history/", ConversationHistory.as_view(), name="conversation-converse-history"),
    path("documents/", Documents.as_view(), name="conversation-documents"),
    path("events/", EventsView.as_view(), name="conversation-events"),
    path("doctors/", DoctorsView.as_view(), name="conversation-doctors"),
    path("goal/", GoalsView.as_view(), name="conversation-goal"),

    # Get and Template APIs
    
    # For Users
    path("profile/", UserProfile.as_view(), name="conversation-profile"),

    path("dashboard/", Dashboard.as_view(), name="conversation-dashboard"),
    path("chat/", Chat.as_view(), name="conversation-chat"),
    path("connect/", Connect.as_view(), name="conversation-connect"),
    
    # For Doctors
    path("dr_dashboard/", DrDashboad.as_view(), name="conversation-dr-dashboard"),
    path("dr_calander/", DrCalander.as_view(), name="conversation-dr-calander"),
    path("dr_circle/", DrCircle.as_view(), name="conversation-dr-chat"),

    path("test/", Test.as_view(), name="test")
]
