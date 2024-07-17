from django.urls import path
from .views_templates import *


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
    path("user-events-dashboard/", UserEventDashboardView.as_view(), name="conversation-user-events-dashboard"),

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

    path("test/", Test.as_view(), name="test"),


    # admin apis
    path("admin-reset-fiass-store-key-information-store/", AdminResetKeyInformationFiassStore.as_view(), name="admin-reset-fiass-store-key-information-store"),

]
